from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def format_timestamp(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@dataclass(frozen=True)
class TranscriptSegment:
    index: int
    start: float
    end: float
    text: str
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "start_timestamp": format_timestamp(self.start),
            "end_timestamp": format_timestamp(self.end),
            "text": self.text,
            "source": self.source,
        }


@dataclass(frozen=True)
class MeetingArtifactPaths:
    audio_dir: Path
    transcripts_dir: Path
    outputs_dir: Path

    def ensure(self) -> None:
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class MeetingAnalysisDraft:
    decisions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    deadlines: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "decisions": self.decisions,
            "actions": self.actions,
            "deadlines": self.deadlines,
            "risks": self.risks,
            "documents": self.documents,
        }


@dataclass(frozen=True)
class TranscriptionResult:
    meeting_id: str
    source_audio_path: Path
    stored_audio_path: Path
    transcript_text_path: Path
    transcript_json_path: Path
    summary_draft_path: Path
    segments: list[TranscriptSegment]
    language: str
    backend: str
    model_name: str
    created_at: str
    analysis_draft: MeetingAnalysisDraft = field(default_factory=MeetingAnalysisDraft)

    def transcript_text(self) -> str:
        lines = []
        for segment in self.segments:
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            lines.append(f"[{start} --> {end}] {segment.text.strip()}")
        return "\n".join(lines).strip() + ("\n" if lines else "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "created_at": self.created_at,
            "language": self.language,
            "backend": self.backend,
            "model_name": self.model_name,
            "source_audio_path": str(self.source_audio_path),
            "stored_audio_path": str(self.stored_audio_path),
            "transcript_text_path": str(self.transcript_text_path),
            "transcript_json_path": str(self.transcript_json_path),
            "summary_draft_path": str(self.summary_draft_path),
            "segments": [segment.to_dict() for segment in self.segments],
            "analysis_draft": self.analysis_draft.to_dict(),
        }
