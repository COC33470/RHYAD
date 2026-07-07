import json
import tempfile
import unittest
from pathlib import Path

from app.modules.meetings.meeting_reasoning import LOW_CONFIDENCE_VALIDATION_NOTE
from app.services.meeting_reasoning_service import MeetingReasoningService


class MeetingReasoningServiceTest(unittest.TestCase):
    def test_reformulates_actions_decisions_and_risks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript = root / "transcript_cleaned.md"
            transcript.write_text(
                "\n".join(
                    [
                        "# Transcription nettoyée",
                        "## Transcription nettoyée horodatée",
                        "- [00:00:01 --> 00:00:05] Il faut identifier les UPS pour les microcoupures du site en Arabie Saoudite.",
                        "- [00:00:05 --> 00:00:10] le choix des souches de main et des master seeds doit être validé.",
                        "- [00:00:10 --> 00:00:15] Le terrain est attendu en septembre pour préparer l'appel d'offres.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            summary = root / "meeting_summary_draft.md"
            summary.write_text("Synthèse: UPS, master seeds, terrain septembre.\n", encoding="utf-8")
            output_dir = root / "outputs"

            result = MeetingReasoningService().reason(
                transcript_cleaned_path=transcript,
                meeting_summary_path=summary,
                output_dir=output_dir,
                meeting_id="20260707-reasoning-test",
            )

            actions = [item.action for item in result.data.actions]
            decisions = [item.decision for item in result.data.decisions]
            risks = result.data.risks

            self.assertIn(
                "Identifier le fournisseur d'électricité local afin de confirmer les contraintes d'alimentation électrique du site.",
                actions,
            )
            self.assertIn(
                "Le choix des master seeds devra être validé avant le lancement des études détaillées.",
                decisions,
            )
            self.assertTrue(any(risk.probability for risk in risks))
            self.assertTrue(any(risk.gravity for risk in risks))
            self.assertTrue(any(risk.criticality in {"Élevée", "Critique"} for risk in risks))
            self.assertTrue(any(risk.action_plan != "À définir" for risk in risks))

            action_log = result.paths.action_log_path.read_text(encoding="utf-8")
            decision_log = result.paths.decision_log_path.read_text(encoding="utf-8")
            self.assertNotIn("Il faut identifier.", action_log)
            self.assertNotIn("le choix des souches de main", decision_log)
            self.assertIn("| ID | Action | Responsable | Échéance | Priorité | Statut | Sujet source | Confiance | Validation |", action_log)

    def test_dashboard_is_project_oriented_and_not_transcript_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript = root / "transcript_cleaned.md"
            noisy_sentence = "Il faut identifier."
            transcript.write_text(
                "\n".join(
                    [
                        "# Transcription nettoyée",
                        "## Transcription nettoyée horodatée",
                        f"- [00:00:01 --> 00:00:03] {noisy_sentence}",
                        "- [00:00:03 --> 00:00:08] Le terrain est attendu en septembre pour préparer l'appel d'offres.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = MeetingReasoningService().reason(
                transcript_cleaned_path=transcript,
                output_dir=root / "outputs",
                meeting_id="20260707-dashboard-test",
            )

            dashboard = result.paths.dashboard_prefill_path.read_text(encoding="utf-8")
            self.assertIn("## Points bloquants", dashboard)
            self.assertIn("## Actions critiques", dashboard)
            self.assertIn("## Risques critiques", dashboard)
            self.assertIn("## Documents à produire", dashboard)
            self.assertNotIn(noisy_sentence, dashboard)
            self.assertIn("terrain", dashboard.lower())

    def test_low_confidence_items_require_project_manager_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript = root / "transcript_cleaned.md"
            transcript.write_text(
                "\n".join(
                    [
                        "# Transcription nettoyée",
                        "## Transcription nettoyée horodatée",
                        "- [00:00:01 --> 00:00:03] Mention isolée GMP à confirmer.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = MeetingReasoningService().reason(
                transcript_cleaned_path=transcript,
                output_dir=root / "outputs",
                meeting_id="20260707-low-confidence-test",
            )

            self.assertTrue(result.data.topics)
            self.assertEqual(result.data.topics[0].confidence, "low")
            self.assertEqual(result.data.topics[0].validation_note, LOW_CONFIDENCE_VALIDATION_NOTE)
            minutes = result.paths.meeting_minutes_prefill_path.read_text(encoding="utf-8")
            self.assertIn(LOW_CONFIDENCE_VALIDATION_NOTE, minutes)

    def test_writes_meeting_knowledge_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript = root / "transcript_cleaned.md"
            transcript.write_text(
                "\n".join(
                    [
                        "# Transcription nettoyée",
                        "## Transcription nettoyée horodatée",
                        "- [00:00:01 --> 00:00:05] UPS et microcoupures sur les équipements critiques.",
                        "- [00:00:05 --> 00:00:10] Terrain en septembre pour appel d'offres.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = MeetingReasoningService().reason(
                transcript_cleaned_path=transcript,
                output_dir=root / "outputs",
                meeting_id="20260707-graph-test",
            )

            graph = json.loads(result.paths.meeting_knowledge_graph_path.read_text(encoding="utf-8"))
            self.assertIn("topics", graph)
            self.assertIn("nodes", graph)
            self.assertIn("edges", graph)
            self.assertTrue(any(topic["actions"] for topic in graph["topics"]))
            self.assertTrue(any(edge["relation"] == "risk" for edge in graph["edges"]))


if __name__ == "__main__":
    unittest.main()
