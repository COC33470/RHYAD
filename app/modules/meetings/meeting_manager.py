from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import shutil
import tempfile
from typing import Optional
import zipfile

from app.modules.meetings.extracted_meeting_data import MeetingExtractionResult
from app.modules.meetings.meeting_reasoning import MeetingReasoningResult
from app.modules.meetings.models import MeetingArtifactPaths, MeetingPostAnalysisResult, TranscriptionResult
from app.services.meeting_data_extraction_service import MeetingDataExtractionService
from app.services.meeting_analysis_service import MeetingAnalysisService
from app.services.meeting_reasoning_service import MeetingReasoningService
from app.services.transcription_service import (
    SUPPORTED_AUDIO_EXTENSIONS,
    FFMpegAudioPreprocessor,
    TranscriptionConfig,
    TranscriptionService,
)


class MeetingManagerError(RuntimeError):
    pass


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("_")
    return slug[:80] or "meeting"


def configure_meeting_logger(project_root: Path) -> logging.Logger:
    logger = logging.getLogger("rhyad.meetings")
    logger.setLevel(logging.INFO)
    log_dir = project_root / "data" / "meetings" / "outputs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "meeting_manager.log"

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_path:
            return logger

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


class MeetingManager:
    def __init__(
        self,
        project_root: Path,
        transcription_service: Optional[TranscriptionService] = None,
        analysis_service: Optional[MeetingAnalysisService] = None,
        data_extraction_service: Optional[MeetingDataExtractionService] = None,
        reasoning_service: Optional[MeetingReasoningService] = None,
        executor: Optional[ThreadPoolExecutor] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.project_root = Path(project_root)
        self.paths = MeetingArtifactPaths(
            audio_dir=self.project_root / "data" / "meetings" / "audio",
            transcripts_dir=self.project_root / "data" / "meetings" / "transcripts",
            outputs_dir=self.project_root / "data" / "meetings" / "outputs",
        )
        self.logger = logger or configure_meeting_logger(self.project_root)
        self.config = TranscriptionConfig.from_project(self.project_root)
        self.transcription_service = transcription_service
        self.analysis_service = analysis_service or MeetingAnalysisService(
            glossary_path=self.project_root / "config" / "meeting_glossary.yaml"
        )
        self.data_extraction_service = data_extraction_service or MeetingDataExtractionService()
        self.reasoning_service = reasoning_service or MeetingReasoningService()
        self.executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="rhyad-meeting")

    @classmethod
    def from_project(cls, project_root: Path) -> "MeetingManager":
        return cls(project_root=project_root)

    def select_audio_file(self, audio_path: Path) -> Path:
        path = Path(audio_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            raise MeetingManagerError(f"Unsupported audio format: {path.suffix}. Expected one of: {allowed}")
        return path

    def import_audio_source(self, source_path: Path) -> Path:
        self.paths.ensure()
        source = Path(source_path).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Meeting source not found: {source}")

        if source.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory(prefix="rhyad-meeting-import-") as tmp:
                extracted_audio = self._extract_audio_from_zip(source, Path(tmp))
                return self._copy_audio_to_project(extracted_audio)

        selected_audio = self.select_audio_file(source)
        return self._copy_audio_to_project(selected_audio)

    def process_audio(self, audio_path: Path, meeting_id: Optional[str] = None) -> TranscriptionResult:
        self.paths.ensure()
        selected_audio = self.select_audio_file(audio_path)
        meeting_id = meeting_id or self._meeting_id(selected_audio)
        transcript_dir = self.paths.transcripts_dir / meeting_id
        output_dir = self.paths.outputs_dir / meeting_id
        transcript_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        stored_audio = self._store_audio(selected_audio, meeting_id)
        transcript_text_path = transcript_dir / "transcript.txt"
        transcript_json_path = transcript_dir / "transcript.json"
        summary_draft_path = output_dir / "meeting_summary_draft.md"

        try:
            self.logger.info("Starting meeting transcription: %s", selected_audio)
            transcription_service = self._get_transcription_service()
            segments = transcription_service.transcribe_audio(stored_audio)
            analysis_draft = self.analysis_service.prepare_draft(segments)
            result = TranscriptionResult(
                meeting_id=meeting_id,
                source_audio_path=selected_audio,
                stored_audio_path=stored_audio,
                transcript_text_path=transcript_text_path,
                transcript_json_path=transcript_json_path,
                summary_draft_path=summary_draft_path,
                segments=segments,
                language=transcription_service.config.language,
                backend=transcription_service.config.backend,
                model_name=transcription_service.config.model_name,
                created_at=datetime.now().isoformat(timespec="seconds"),
                analysis_draft=analysis_draft,
            )
            self._write_outputs(result)
            post_analysis = self.analyze_transcript(result.transcript_text_path, meeting_id=meeting_id)
            result = replace(result, post_analysis=post_analysis)
            self._write_outputs(result)
            self.logger.info("Meeting transcription completed: %s", meeting_id)
            return result
        except Exception:
            self.logger.exception("Meeting transcription failed: %s", selected_audio)
            raise

    def analyze_transcript(self, transcript_path: Path, meeting_id: Optional[str] = None) -> MeetingPostAnalysisResult:
        self.paths.ensure()
        source = Path(transcript_path).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Transcript file not found: {source}")
        if source.suffix.lower() not in {".txt", ".md"}:
            raise MeetingManagerError(f"Unsupported transcript format: {source.suffix}. Expected .txt or .md")

        meeting_id = meeting_id or self._meeting_id_from_transcript(source)
        transcript_cleaned_path = source.parent / "transcript_cleaned.md"
        output_dir = self.paths.outputs_dir / meeting_id

        try:
            self.logger.info("Starting meeting transcript analysis: %s", source)
            result = self.analysis_service.analyze_transcript_file(
                transcript_path=source,
                transcript_cleaned_path=transcript_cleaned_path,
                output_dir=output_dir,
                meeting_id=meeting_id,
            )
            self.logger.info("Meeting transcript analysis completed: %s", meeting_id)
            return result
        except Exception:
            self.logger.exception("Meeting transcript analysis failed: %s", source)
            raise

    def clean_transcript(self, transcript_path: Path, meeting_id: Optional[str] = None) -> Path:
        self.paths.ensure()
        requested_source = Path(transcript_path).expanduser().resolve()
        source = self._resolve_transcript_source(requested_source, "transcript.txt")
        if not source.exists():
            raise FileNotFoundError(f"Transcript file not found: {requested_source}")
        if source.suffix.lower() not in {".txt", ".md"}:
            raise MeetingManagerError(f"Unsupported transcript format: {source.suffix}. Expected .txt or .md")

        meeting_id = meeting_id or self._meeting_id_from_transcript(source)
        transcript_cleaned_path = requested_source.parent / "transcript_cleaned.md"

        try:
            self.logger.info("Starting meeting transcript cleanup: %s", source)
            result = self.analysis_service.clean_transcript_file(
                transcript_path=source,
                transcript_cleaned_path=transcript_cleaned_path,
                meeting_id=meeting_id,
            )
            self.logger.info("Meeting transcript cleanup completed: %s", result)
            return result
        except Exception:
            self.logger.exception("Meeting transcript cleanup failed: %s", source)
            raise

    def extract_meeting_data(
        self,
        transcript_cleaned_path: Path,
        meeting_summary_path: Optional[Path] = None,
        transcript_json_path: Optional[Path] = None,
        meeting_id: Optional[str] = None,
    ) -> MeetingExtractionResult:
        self.paths.ensure()
        requested_source = Path(transcript_cleaned_path).expanduser().resolve()
        source = self._resolve_transcript_source(requested_source, "transcript_cleaned.md")
        if not source.exists():
            raise FileNotFoundError(f"Cleaned transcript file not found: {requested_source}")
        if source.suffix.lower() not in {".md", ".txt"}:
            raise MeetingManagerError(f"Unsupported transcript format: {source.suffix}. Expected .md or .txt")

        meeting_id = meeting_id or self._meeting_id_from_transcript(source)
        output_dir = self._output_dir_for_transcript(requested_source, meeting_id)
        summary_path = Path(meeting_summary_path).expanduser().resolve() if meeting_summary_path else self._infer_summary_path(source, meeting_id, output_dir)
        json_path = Path(transcript_json_path).expanduser().resolve() if transcript_json_path else self._infer_transcript_json_path(source)

        try:
            self.logger.info("Starting meeting data extraction: %s", source)
            result = self.data_extraction_service.extract(
                transcript_cleaned_path=source,
                output_dir=output_dir,
                meeting_id=meeting_id,
                meeting_summary_path=summary_path,
                transcript_json_path=json_path,
            )
            self.logger.info("Meeting data extraction completed: %s", meeting_id)
            return result
        except Exception:
            self.logger.exception("Meeting data extraction failed: %s", source)
            raise

    def reason_meeting(
        self,
        transcript_cleaned_path: Path,
        meeting_summary_path: Optional[Path] = None,
        meeting_id: Optional[str] = None,
    ) -> MeetingReasoningResult:
        self.paths.ensure()
        requested_source = Path(transcript_cleaned_path).expanduser().resolve()
        source = self._resolve_transcript_source(requested_source, "transcript_cleaned.md")
        if not source.exists():
            raise FileNotFoundError(f"Cleaned transcript file not found: {requested_source}")
        if source.suffix.lower() not in {".md", ".txt"}:
            raise MeetingManagerError(f"Unsupported transcript format: {source.suffix}. Expected .md or .txt")

        meeting_id = meeting_id or self._meeting_id_from_transcript(source)
        output_dir = self._output_dir_for_transcript(requested_source, meeting_id)
        summary_path = (
            Path(meeting_summary_path).expanduser().resolve()
            if meeting_summary_path
            else self._infer_summary_path(source, meeting_id, output_dir)
        )

        try:
            self.logger.info("Starting meeting reasoning: %s", source)
            result = self.reasoning_service.reason(
                transcript_cleaned_path=source,
                output_dir=output_dir,
                meeting_id=meeting_id,
                meeting_summary_path=summary_path,
            )
            self.logger.info("Meeting reasoning completed: %s", meeting_id)
            return result
        except Exception:
            self.logger.exception("Meeting reasoning failed: %s", source)
            raise

    def generate_deliverables(self, transcript_cleaned_path: Path) -> MeetingReasoningResult:
        return self.reason_meeting(transcript_cleaned_path)

    def start_processing_job(self, audio_path: Path, meeting_id: Optional[str] = None) -> Future:
        return self.executor.submit(self.process_audio, audio_path, meeting_id)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=False)

    def _meeting_id(self, audio_path: Path) -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{timestamp}-{_safe_slug(audio_path.stem)}"

    def _meeting_id_from_transcript(self, transcript_path: Path) -> str:
        transcripts_root = self.paths.transcripts_dir.resolve()
        try:
            relative = transcript_path.resolve().relative_to(transcripts_root)
        except ValueError:
            return _safe_slug(transcript_path.stem)

        if len(relative.parts) > 1:
            return _safe_slug(relative.parts[0])
        return _safe_slug(transcript_path.stem)

    def _output_dir_for_transcript(self, transcript_path: Path, meeting_id: str) -> Path:
        transcripts_root = self.paths.transcripts_dir.resolve()
        try:
            relative = transcript_path.resolve().relative_to(transcripts_root)
        except ValueError:
            return self.paths.outputs_dir / meeting_id

        if len(relative.parts) > 1:
            return self.paths.outputs_dir / meeting_id
        return self.paths.outputs_dir

    def _infer_summary_path(self, transcript_path: Path, meeting_id: str, output_dir: Path) -> Path:
        candidates = [
            output_dir / "meeting_summary_draft.md",
            self.paths.outputs_dir / meeting_id / "meeting_summary_draft.md",
            self.paths.outputs_dir / "meeting_summary_draft.md",
            transcript_path.parent / "meeting_summary_draft.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _infer_transcript_json_path(self, transcript_path: Path) -> Path:
        candidate = transcript_path.parent / "transcript.json"
        if candidate.exists():
            return candidate
        return transcript_path.with_suffix(".json")

    def _resolve_transcript_source(self, requested_source: Path, filename: str) -> Path:
        if requested_source.exists():
            return requested_source
        try:
            relative = requested_source.relative_to(self.paths.transcripts_dir.resolve())
        except ValueError:
            return requested_source

        if len(relative.parts) == 1 and relative.name == filename:
            candidates = sorted(
                self.paths.transcripts_dir.glob(f"*/{filename}"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if candidates:
                return candidates[0].resolve()
        return requested_source

    def _store_audio(self, audio_path: Path, meeting_id: str) -> Path:
        destination = self.paths.audio_dir / f"{meeting_id}{audio_path.suffix.lower()}"
        if audio_path.resolve() != destination.resolve():
            shutil.copy2(audio_path, destination)
        return destination

    def _get_transcription_service(self) -> TranscriptionService:
        if self.transcription_service is None:
            self.transcription_service = TranscriptionService(
                config=self.config,
                audio_preprocessor=FFMpegAudioPreprocessor(self.config, logger=self.logger),
                logger=self.logger,
            )
        return self.transcription_service

    def _copy_audio_to_project(self, audio_path: Path) -> Path:
        destination = self.paths.audio_dir / audio_path.name
        if audio_path.resolve() != destination.resolve():
            shutil.copy2(audio_path, destination)
        return destination

    def _extract_audio_from_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extract_dir)
        except zipfile.BadZipFile as exc:
            raise MeetingManagerError(f"Invalid meeting zip file: {zip_path}") from exc

        audio_files = sorted(
            path for path in extract_dir.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        )
        if not audio_files:
            allowed = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            raise MeetingManagerError(f"No supported audio file found in {zip_path}. Expected one of: {allowed}")
        return audio_files[0]

    def _write_outputs(self, result: TranscriptionResult) -> None:
        result.transcript_text_path.write_text(result.transcript_text(), encoding="utf-8")
        result.transcript_json_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result.summary_draft_path.write_text(
            self.analysis_service.build_summary_markdown(result),
            encoding="utf-8",
        )
