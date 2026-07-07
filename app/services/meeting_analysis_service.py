import re

from app.modules.meetings.models import MeetingAnalysisDraft, TranscriptSegment, TranscriptionResult


DOCUMENT_PATTERN = re.compile(r"\bCEVA-RHYAD-[A-Z0-9][A-Z0-9_-]*(?:-[A-Z0-9][A-Z0-9_-]*)*\b")
DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")


class MeetingAnalysisService:
    def prepare_draft(self, segments: list[TranscriptSegment]) -> MeetingAnalysisDraft:
        decisions = []
        actions = []
        deadlines = []
        risks = []
        documents = set()

        for segment in segments:
            text = segment.text.strip()
            lowered = text.lower()

            if any(keyword in lowered for keyword in ("décision", "decide", "décidé", "validé", "arbitré")):
                decisions.append(text)
            if any(keyword in lowered for keyword in ("action", "à faire", "a faire", "responsable", "doit", "prendre en charge")):
                actions.append(text)
            if DATE_PATTERN.search(text) or any(keyword in lowered for keyword in ("échéance", "deadline", "avant le", "pour le")):
                deadlines.append(text)
            if any(keyword in lowered for keyword in ("risque", "blocage", "bloquant", "alerte", "retard", "dérive")):
                risks.append(text)

            for match in DOCUMENT_PATTERN.findall(text):
                documents.add(match)

        return MeetingAnalysisDraft(
            decisions=decisions,
            actions=actions,
            deadlines=deadlines,
            risks=risks,
            documents=sorted(documents),
        )

    def build_summary_markdown(self, result: TranscriptionResult) -> str:
        draft = result.analysis_draft
        lines = [
            f"# Meeting Summary Draft - {result.meeting_id}",
            "",
            "## Source",
            "",
            f"- Audio: `{result.stored_audio_path}`",
            f"- Langue: `{result.language}`",
            f"- Backend transcription: `{result.backend}`",
            f"- Modèle: `{result.model_name}`",
            "",
            "## Extraction IA à préparer",
            "",
            "### Décisions candidates",
            *self._bullet_lines(draft.decisions),
            "",
            "### Actions candidates",
            *self._bullet_lines(draft.actions),
            "",
            "### Échéances candidates",
            *self._bullet_lines(draft.deadlines),
            "",
            "### Risques candidats",
            *self._bullet_lines(draft.risks),
            "",
            "### Documents évoqués",
            *self._bullet_lines(draft.documents),
            "",
            "## Transcription horodatée",
            "",
        ]

        for segment in result.segments:
            lines.append(f"- [{segment.to_dict()['start_timestamp']} -> {segment.to_dict()['end_timestamp']}] {segment.text}")

        return "\n".join(lines).rstrip() + "\n"

    def _bullet_lines(self, values: list[str]) -> list[str]:
        if not values:
            return ["- À extraire par IA."]
        return [f"- {value}" for value in values]
