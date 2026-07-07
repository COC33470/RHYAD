from dataclasses import dataclass
import json
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable, Optional, Protocol, Sequence

try:
    import yaml
except ImportError:
    yaml = None

from app.modules.meetings.models import TranscriptSegment


SUPPORTED_AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav"}


class TranscriptionError(RuntimeError):
    pass


class AudioTranscriber(Protocol):
    def transcribe(self, audio_path: Path, language: str) -> list[TranscriptSegment]:
        ...


CommandRunner = Callable[[Sequence[str], Optional[int]], subprocess.CompletedProcess]


@dataclass(frozen=True)
class TranscriptionConfig:
    backend: str = "faster-whisper"
    model_name: str = "tiny"
    language: str = "fr"
    device: str = "auto"
    compute_type: str = "int8"
    segment_seconds: int = 900
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    openai_model: str = ""

    @classmethod
    def from_project(cls, project_root: Path) -> "TranscriptionConfig":
        config_path = project_root / "config" / "meeting_manager.yaml"
        if not config_path.exists() or yaml is None:
            return cls()

        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        values = raw.get("transcription", raw)
        return cls(
            backend=str(values.get("backend", cls.backend)),
            model_name=str(values.get("model_name", cls.model_name)),
            language=str(values.get("language", cls.language)),
            device=str(values.get("device", cls.device)),
            compute_type=str(values.get("compute_type", cls.compute_type)),
            segment_seconds=int(values.get("segment_seconds", cls.segment_seconds)),
            ffmpeg_path=str(values.get("ffmpeg_path", cls.ffmpeg_path)),
            ffprobe_path=str(values.get("ffprobe_path", cls.ffprobe_path)),
            openai_model=str(values.get("openai_model", cls.openai_model)),
        )


@dataclass(frozen=True)
class AudioChunk:
    path: Path
    offset_seconds: float


def find_ffmpeg_executable(configured_path: str = "ffmpeg") -> str:
    executable = shutil.which(configured_path)
    if executable:
        return executable

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise TranscriptionError(
            f"ffmpeg executable not found: {configured_path}. Install ffmpeg or imageio-ffmpeg."
        ) from exc

    return imageio_ffmpeg.get_ffmpeg_exe()


def default_command_runner(command: Sequence[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(command),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def _format_process_output(result: subprocess.CompletedProcess) -> str:
    parts = []
    if result.stdout:
        parts.append(f"stdout: {result.stdout.strip()}")
    if result.stderr:
        parts.append(f"stderr: {result.stderr.strip()}")
    return "\n".join(parts)


class FFMpegAudioPreprocessor:
    def __init__(
        self,
        config: TranscriptionConfig,
        runner: CommandRunner = default_command_runner,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config
        self.runner = runner
        self.logger = logger or logging.getLogger("rhyad.meetings")
        self.ffmpeg_path = find_ffmpeg_executable(config.ffmpeg_path)

    def prepare_chunks(self, audio_path: Path, work_dir: Path) -> list[AudioChunk]:
        audio_path = audio_path.resolve()
        self._validate_audio_path(audio_path)
        work_dir.mkdir(parents=True, exist_ok=True)

        duration = self.probe_duration(audio_path)
        if duration and duration > self.config.segment_seconds:
            return self._split_audio(audio_path, work_dir)
        if duration is None:
            return self._split_audio(audio_path, work_dir)
        return [AudioChunk(self._convert_audio(audio_path, work_dir), 0.0)]

    def probe_duration(self, audio_path: Path) -> Optional[float]:
        command = [
            self.config.ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(audio_path),
        ]
        try:
            result = self.runner(command, 120)
        except FileNotFoundError as exc:
            self.logger.warning("ffprobe executable not found: %s", self.config.ffprobe_path)
            return None

        if result.returncode != 0:
            self.logger.warning("ffprobe failed for %s: %s", audio_path, _format_process_output(result))
            return None

        try:
            data = json.loads(result.stdout or "{}")
            return float((data.get("format") or {}).get("duration") or 0)
        except (TypeError, ValueError, json.JSONDecodeError):
            self.logger.warning("ffprobe returned an unreadable duration for %s", audio_path)
            return None

    def _split_audio(self, audio_path: Path, work_dir: Path) -> list[AudioChunk]:
        pattern = work_dir / "segment_%05d.wav"
        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-vn",
            "-f",
            "segment",
            "-segment_time",
            str(self.config.segment_seconds),
            "-reset_timestamps",
            "1",
            str(pattern),
        ]
        self._run_ffmpeg(command, audio_path)

        paths = sorted(work_dir.glob("segment_*.wav"))
        if not paths:
            raise TranscriptionError(f"ffmpeg did not create audio segments for {audio_path}")

        return [
            AudioChunk(path=path, offset_seconds=index * self.config.segment_seconds)
            for index, path in enumerate(paths)
        ]

    def _convert_audio(self, audio_path: Path, work_dir: Path) -> Path:
        converted_path = work_dir / f"{audio_path.stem}.wav"
        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-vn",
            str(converted_path),
        ]
        self._run_ffmpeg(command, audio_path)
        if not converted_path.exists():
            raise TranscriptionError(f"ffmpeg did not create converted audio: {converted_path}")
        return converted_path

    def _run_ffmpeg(self, command: Sequence[str], audio_path: Path) -> None:
        try:
            result = self.runner(command, None)
        except FileNotFoundError as exc:
            raise TranscriptionError(f"ffmpeg executable not found: {self.ffmpeg_path}") from exc

        if result.returncode != 0:
            details = _format_process_output(result)
            message = f"ffmpeg failed while preparing {audio_path}"
            if details:
                message = f"{message}\n{details}"
            raise TranscriptionError(message)

    def _validate_audio_path(self, audio_path: Path) -> None:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            raise TranscriptionError(f"Unsupported audio format: {audio_path.suffix}. Expected one of: {allowed}")


class FasterWhisperTranscriber:
    def __init__(self, config: TranscriptionConfig):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "faster-whisper is not installed. Install it or set transcription.backend to 'whisper'."
            ) from exc

        self.model = WhisperModel(
            config.model_name,
            device=config.device,
            compute_type=config.compute_type,
        )

    def transcribe(self, audio_path: Path, language: str) -> list[TranscriptSegment]:
        segments, _info = self.model.transcribe(str(audio_path), language=language, vad_filter=True)
        return [
            TranscriptSegment(index=index, start=float(segment.start), end=float(segment.end), text=segment.text)
            for index, segment in enumerate(segments, start=1)
        ]


class WhisperTranscriber:
    def __init__(self, config: TranscriptionConfig):
        try:
            import whisper
        except ImportError as exc:
            raise TranscriptionError(
                "whisper is not installed. Install openai-whisper or set transcription.backend to 'faster-whisper'."
            ) from exc

        self.model = whisper.load_model(config.model_name)

    def transcribe(self, audio_path: Path, language: str) -> list[TranscriptSegment]:
        result = self.model.transcribe(str(audio_path), language=language, task="transcribe", fp16=False)
        return [
            TranscriptSegment(
                index=index,
                start=float(segment.get("start", 0.0)),
                end=float(segment.get("end", 0.0)),
                text=str(segment.get("text", "")),
            )
            for index, segment in enumerate(result.get("segments", []), start=1)
        ]


def build_transcriber(config: TranscriptionConfig) -> AudioTranscriber:
    backend = config.backend.strip().lower()
    if backend in {"faster-whisper", "faster_whisper"}:
        return FasterWhisperTranscriber(config)
    if backend == "whisper":
        return WhisperTranscriber(config)
    if backend == "openai":
        raise TranscriptionError("OpenAI transcription backend is reserved for a future RHYAD release.")
    raise TranscriptionError(f"Unsupported transcription backend: {config.backend}")


class TranscriptionService:
    def __init__(
        self,
        config: Optional[TranscriptionConfig] = None,
        transcriber: Optional[AudioTranscriber] = None,
        audio_preprocessor: Optional[FFMpegAudioPreprocessor] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or TranscriptionConfig()
        self.logger = logger or logging.getLogger("rhyad.meetings")
        self.transcriber = transcriber
        self.audio_preprocessor = audio_preprocessor or FFMpegAudioPreprocessor(self.config, logger=self.logger)

    def transcribe_audio(self, audio_path: Path) -> list[TranscriptSegment]:
        if self.transcriber is None:
            self.transcriber = build_transcriber(self.config)

        with tempfile.TemporaryDirectory(prefix="rhyad-meeting-audio-") as tmp:
            chunks = self.audio_preprocessor.prepare_chunks(audio_path, Path(tmp))
            return self._transcribe_chunks(chunks)

    def _transcribe_chunks(self, chunks: list[AudioChunk]) -> list[TranscriptSegment]:
        transcript_segments = []
        next_index = 1

        for chunk in chunks:
            self.logger.info("Transcribing audio chunk: %s", chunk.path)
            chunk_segments = self.transcriber.transcribe(chunk.path, self.config.language)
            for segment in chunk_segments:
                transcript_segments.append(
                    TranscriptSegment(
                        index=next_index,
                        start=segment.start + chunk.offset_seconds,
                        end=segment.end + chunk.offset_seconds,
                        text=segment.text.strip(),
                        source=chunk.path.name,
                    )
                )
                next_index += 1

        return transcript_segments
