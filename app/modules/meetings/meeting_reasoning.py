from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


LOW_CONFIDENCE_VALIDATION_NOTE = "Validation chef de projet requise"


@dataclass(frozen=True)
class MeetingContext:
    project: str = "CEVA Riyadh Campus Project"
    meeting_date: str = "À confirmer"
    subject: str = "Réunion de cadrage programme, site, modules et risques"
    participants: list[str] = field(default_factory=list)
    purpose: str = "Transformer la transcription en données projet exploitables RHYAD."
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class Decision:
    id: str
    decision: str
    context: str
    owner_or_validator: str = "À confirmer"
    date: str = "À confirmer"
    document_impact: list[str] = field(default_factory=list)
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class ActionItem:
    id: str
    action: str
    owner: str = "À confirmer"
    due_date: str = "À confirmer"
    priority: str = "Moyenne"
    status: str = "À qualifier"
    source_topic: str = "À confirmer"
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class Risk:
    id: str
    risk: str
    cause: str
    impact: str
    probability: str = "Moyenne"
    gravity: str = "Moyenne"
    criticality: str = "Modérée"
    owner: str = "À confirmer"
    action_plan: str = "À définir"
    source_topic: str = "À confirmer"
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class Requirement:
    id: str
    requirement: str
    discipline: str
    constraint: str
    project_impact: str
    source_topic: str = "À confirmer"
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class DocumentImpact:
    id: str
    document: str
    required_change: str
    source_topic: str
    priority: str = "Moyenne"
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class OpenPoint:
    id: str
    open_point: str
    expected_arbitration: str
    owner: str = "À confirmer"
    target_due_date: str = "À confirmer"
    source_topic: str = "À confirmer"
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class Milestone:
    id: str
    milestone: str
    target_date: str = "À confirmer"
    status: str = "À qualifier"
    source_topic: str = "À confirmer"
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class DiscussionTopic:
    id: str
    subject: str
    context: str
    problem_statement: str
    decisions: list[Decision] = field(default_factory=list)
    actions: list[ActionItem] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    document_impacts: list[DocumentImpact] = field(default_factory=list)
    open_points: list[OpenPoint] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    persons: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    confidence: str = "medium"
    validation_note: str = ""


@dataclass(frozen=True)
class DashboardReasoningData:
    overall_status: str
    blocking_points: list[str] = field(default_factory=list)
    major_decisions: list[str] = field(default_factory=list)
    critical_actions: list[str] = field(default_factory=list)
    critical_risks: list[str] = field(default_factory=list)
    planning: list[str] = field(default_factory=list)
    next_deadlines: list[str] = field(default_factory=list)
    documents_to_produce: list[str] = field(default_factory=list)
    documents_to_update: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MeetingReasoningModel:
    context: MeetingContext
    topics: list[DiscussionTopic] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    actions: list[ActionItem] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    document_impacts: list[DocumentImpact] = field(default_factory=list)
    open_points: list[OpenPoint] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    dashboard: DashboardReasoningData = field(default_factory=lambda: DashboardReasoningData("À confirmer"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeetingReasoningArtifactPaths:
    meeting_minutes_prefill_path: Path
    dashboard_prefill_path: Path
    action_log_path: Path
    decision_log_path: Path
    risk_register_update_path: Path
    document_impact_log_path: Path
    meeting_knowledge_graph_path: Path

    def artifact_paths(self) -> list[Path]:
        return [
            self.meeting_minutes_prefill_path,
            self.dashboard_prefill_path,
            self.action_log_path,
            self.decision_log_path,
            self.risk_register_update_path,
            self.document_impact_log_path,
            self.meeting_knowledge_graph_path,
        ]


@dataclass(frozen=True)
class MeetingReasoningResult:
    meeting_id: str
    source_transcript_path: Path
    source_summary_path: Optional[Path]
    output_dir: Path
    data: MeetingReasoningModel
    paths: MeetingReasoningArtifactPaths

    def artifact_paths(self) -> list[Path]:
        return self.paths.artifact_paths()
