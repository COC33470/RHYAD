from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MeetingInfo:
    project: str = "À confirmer"
    meeting_date: str = "À confirmer"
    subject: str = "À confirmer"
    identified_participants: list[str] = field(default_factory=list)
    context: str = "À confirmer"


@dataclass(frozen=True)
class ExecutiveSummary:
    short_summary: str = "À confirmer"
    major_points: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DashboardData:
    overall_status: str = "À confirmer"
    document_progress: list[str] = field(default_factory=list)
    recent_decisions: list[str] = field(default_factory=list)
    critical_actions: list[str] = field(default_factory=list)
    main_risks: list[str] = field(default_factory=list)
    next_milestones: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionItem:
    decision: str
    context: str = "À confirmer"
    owner_or_validator: str = "À confirmer"
    date: str = "À confirmer"
    document_impact: str = "À confirmer"


@dataclass(frozen=True)
class ActionItem:
    action: str
    owner: str = "À confirmer"
    due_date: str = "À confirmer"
    priority: str = "Moyenne"
    status: str = "À qualifier"
    transcription_source: str = "À confirmer"


@dataclass(frozen=True)
class RiskItem:
    risk: str
    cause: str = "À confirmer"
    impact: str = "À confirmer"
    proposed_measure: str = "À définir"
    criticality: str = "À qualifier"


@dataclass(frozen=True)
class OpenPointItem:
    open_point: str
    expected_arbitration: str = "À confirmer"
    owner: str = "À confirmer"
    target_due_date: str = "À confirmer"


@dataclass(frozen=True)
class DocumentImpactItem:
    document: str
    required_change: str
    decision_source: str = "À confirmer"
    priority: str = "Moyenne"


@dataclass(frozen=True)
class TechnicalRequirementItem:
    requirement: str
    discipline: str = "À confirmer"
    related_constraint: str = "À confirmer"
    project_impact: str = "À qualifier"


@dataclass(frozen=True)
class ExtractedMeetingData:
    meeting_info: MeetingInfo = field(default_factory=MeetingInfo)
    executive_summary: ExecutiveSummary = field(default_factory=ExecutiveSummary)
    dashboard_data: DashboardData = field(default_factory=DashboardData)
    decisions: list[DecisionItem] = field(default_factory=list)
    actions: list[ActionItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)
    open_points: list[OpenPointItem] = field(default_factory=list)
    document_impacts: list[DocumentImpactItem] = field(default_factory=list)
    technical_requirements: list[TechnicalRequirementItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeetingExtractionArtifactPaths:
    meeting_minutes_prefill_path: Path
    dashboard_prefill_path: Path
    action_log_path: Path
    decision_log_path: Path
    risk_register_update_path: Path
    document_impact_log_path: Path

    def artifact_paths(self) -> list[Path]:
        return [
            self.meeting_minutes_prefill_path,
            self.dashboard_prefill_path,
            self.action_log_path,
            self.decision_log_path,
            self.risk_register_update_path,
            self.document_impact_log_path,
        ]


@dataclass(frozen=True)
class MeetingExtractionResult:
    meeting_id: str
    source_transcript_path: Path
    output_dir: Path
    data: ExtractedMeetingData
    paths: MeetingExtractionArtifactPaths

    def artifact_paths(self) -> list[Path]:
        return self.paths.artifact_paths()
