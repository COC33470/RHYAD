import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import zipfile

from app.modules.meetings.meeting_manager import MeetingManager
from app.modules.meetings.models import TranscriptSegment
from app.services.transcription_service import FFMpegAudioPreprocessor, TranscriptionConfig, TranscriptionService


class FakeTranscriber:
    def __init__(self):
        self.calls = []

    def transcribe(self, audio_path, language):
        self.calls.append((audio_path, language))
        return [
            TranscriptSegment(
                index=1,
                start=0.0,
                end=2.0,
                text=(
                    "Décision validée pour CEVA-RHYAD-002-PF avant le 12/07. "
                    "Il faut identifier les UPS pour les micro coupures en Arabie Saoudite."
                ),
            )
        ]


def _write_fake_m4a(root):
    audio_path = root / "meeting-alpha.m4a"
    audio_path.write_bytes(b"fake m4a")
    return audio_path


def _fake_short_audio_runner(command, timeout=None):
    if command[0] == "ffprobe":
        return subprocess.CompletedProcess(command, 0, stdout='{"format": {"duration": "3.2"}}', stderr="")

    output_path = Path(command[-1])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"RIFF fake wav")
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


class MeetingManagerTest(unittest.TestCase):
    def test_process_m4a_creates_transcript_json_and_summary_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio_path = _write_fake_m4a(root)
            config = TranscriptionConfig(backend="fake", model_name="fake-model", language="fr")
            transcriber = FakeTranscriber()
            service = TranscriptionService(
                config=config,
                transcriber=transcriber,
                audio_preprocessor=FFMpegAudioPreprocessor(config, runner=_fake_short_audio_runner),
            )
            manager = MeetingManager(project_root=root, transcription_service=service)

            result = manager.process_audio(audio_path, meeting_id="meeting-alpha")
            manager.shutdown()

            self.assertEqual(transcriber.calls[0][1], "fr")
            self.assertEqual(result.meeting_id, "meeting-alpha")
            self.assertTrue((root / "data" / "meetings" / "audio" / "meeting-alpha.m4a").exists())
            self.assertTrue(result.transcript_text_path.exists())
            self.assertTrue(result.transcript_json_path.exists())
            self.assertTrue(result.summary_draft_path.exists())
            self.assertIsNotNone(result.post_analysis)
            self.assertTrue(result.post_analysis.transcript_cleaned_path.exists())
            self.assertTrue(result.post_analysis.meeting_minutes_draft_path.exists())
            self.assertTrue(result.post_analysis.action_log_path.exists())
            self.assertTrue(result.post_analysis.decision_log_path.exists())
            self.assertTrue(result.post_analysis.risk_register_update_path.exists())
            self.assertTrue(result.post_analysis.document_impact_log_path.exists())

            transcript_text = result.transcript_text_path.read_text(encoding="utf-8")
            self.assertIn("[00:00:00 --> 00:00:02]", transcript_text)
            self.assertIn("CEVA-RHYAD-002-PF", transcript_text)

            transcript_json = json.loads(result.transcript_json_path.read_text(encoding="utf-8"))
            self.assertEqual(transcript_json["language"], "fr")
            self.assertEqual(transcript_json["backend"], "fake")
            self.assertEqual(transcript_json["segments"][0]["text"], result.segments[0].text)
            self.assertEqual(transcript_json["analysis_draft"]["documents"], ["CEVA-RHYAD-002-PF"])
            self.assertIn("meeting_minutes_draft.md", transcript_json["post_analysis_paths"][1])

            summary = result.summary_draft_path.read_text(encoding="utf-8")
            self.assertIn("## Extraction IA à préparer", summary)
            self.assertIn("### Décisions candidates", summary)
            self.assertIn("CEVA-RHYAD-002-PF", summary)

            cleaned = result.post_analysis.transcript_cleaned_path.read_text(encoding="utf-8")
            self.assertIn("microcoupures", cleaned)
            self.assertIn("UPS", cleaned)

            minutes = result.post_analysis.meeting_minutes_draft_path.read_text(encoding="utf-8")
            self.assertIn("Alimentation électrique / UPS / microcoupures", minutes)
            self.assertIn("Contraintes site Arabie Saoudite", minutes)

    def test_analyze_transcript_creates_alpha_02_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript_dir = root / "data" / "meetings" / "transcripts" / "meeting-existing"
            transcript_dir.mkdir(parents=True)
            transcript_path = transcript_dir / "transcript.txt"
            transcript_path.write_text(
                "\n".join(
                    [
                        "[00:00:01 --> 00:00:05] programme fonctionnale et contraintes de site en rabise au lit.",
                        "[00:00:05 --> 00:00:09] Il faut regarder les UPS pour les micro coupures.",
                        "[00:00:09 --> 00:00:13] Point risque sur les souches et les master-sins en congélateurs.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            manager = MeetingManager(project_root=root, transcription_service=None)
            result = manager.analyze_transcript(transcript_path)
            manager.shutdown()

            self.assertEqual(result.meeting_id, "meeting-existing")
            for path in result.artifact_paths():
                self.assertTrue(path.exists(), path)

            cleaned = result.transcript_cleaned_path.read_text(encoding="utf-8")
            self.assertIn("programme fonctionnel", cleaned)
            self.assertIn("Arabie Saoudite", cleaned)
            self.assertIn("master seeds", cleaned)

            risk_log = result.risk_register_update_path.read_text(encoding="utf-8")
            self.assertIn("souches", risk_log)
            self.assertIn("master seeds", risk_log)

    def test_extract_meeting_data_creates_alpha_03_prefill_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript_dir = root / "data" / "meetings" / "transcripts" / "20260707-meeting-existing"
            output_dir = root / "data" / "meetings" / "outputs" / "20260707-meeting-existing"
            transcript_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            transcript_path = transcript_dir / "transcript_cleaned.md"
            transcript_path.write_text(
                "\n".join(
                    [
                        "# Transcription nettoyée",
                        "- [00:00:01 --> 00:00:05] Le programme fonctionnel doit intégrer les contraintes du site en Arabie Saoudite.",
                        "- [00:00:05 --> 00:00:09] Il faut identifier les UPS pour les microcoupures.",
                        "- [00:00:09 --> 00:00:13] Point risque sur les souches et les master seeds en congélateurs.",
                        "- [00:00:13 --> 00:00:17] Le terrain est attendu en septembre pour préparer l'appel d'offres.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (output_dir / "meeting_summary_draft.md").write_text("# Summary\n", encoding="utf-8")
            (transcript_dir / "transcript.json").write_text('{"created_at": "2026-07-07T10:00:00"}\n', encoding="utf-8")

            manager = MeetingManager(project_root=root, transcription_service=None)
            result = manager.extract_meeting_data(transcript_path)
            manager.shutdown()

            self.assertEqual(result.meeting_id, "20260707-meeting-existing")
            for path in result.artifact_paths():
                self.assertTrue(path.exists(), path)

            minutes = result.paths.meeting_minutes_prefill_path.read_text(encoding="utf-8")
            self.assertIn("Compte rendu CEVA-RHYAD prérempli", minutes)
            self.assertIn("Informations réunion", minutes)
            self.assertIn("Exigences techniques candidates", minutes)

            dashboard = result.paths.dashboard_prefill_path.read_text(encoding="utf-8")
            self.assertIn("Dashboard projet prérempli - CEVA-RHYAD-400-R05", dashboard)
            self.assertIn("## 1. État du projet", dashboard)
            self.assertIn("## 6. Prochaines étapes", dashboard)

            self.assertTrue(result.data.actions)
            self.assertTrue(result.data.risks)
            self.assertTrue(result.data.document_impacts)
            self.assertTrue(result.data.technical_requirements)

    def test_clean_transcript_creates_themed_cleaned_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript_dir = root / "data" / "meetings" / "transcripts"
            transcript_dir.mkdir(parents=True)
            transcript_path = transcript_dir / "transcript.txt"
            transcript_path.write_text(
                "\n".join(
                    [
                        "[00:00:01 --> 00:00:05] programme fonctionnale et contraintes en rabise au lit.",
                        "[00:00:05 --> 00:00:09] Il faut regarder les UPS pour les micro coupures.",
                        "[00:00:09 --> 00:00:13] phrase bruitée avec un situite.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            manager = MeetingManager(project_root=root, transcription_service=None)
            cleaned_path = manager.clean_transcript(transcript_path)
            manager.shutdown()

            self.assertEqual(cleaned_path.resolve(), (transcript_dir / "transcript_cleaned.md").resolve())
            cleaned = cleaned_path.read_text(encoding="utf-8")
            self.assertIn("## Vue par thèmes", cleaned)
            self.assertIn("## Transcription nettoyée horodatée", cleaned)
            self.assertIn("programme fonctionnel", cleaned)
            self.assertIn("Arabie Saoudite", cleaned)
            self.assertIn("microcoupures", cleaned)
            self.assertIn("[à vérifier]", cleaned)

    def test_generate_deliverables_writes_root_outputs_for_root_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript_dir = root / "data" / "meetings" / "transcripts"
            transcript_dir.mkdir(parents=True)
            transcript_path = transcript_dir / "transcript_cleaned.md"
            transcript_path.write_text(
                "\n".join(
                    [
                        "# Transcription nettoyée",
                        "## Transcription nettoyée horodatée",
                        "- [00:00:01 --> 00:00:05] Le programme fonctionnel doit intégrer les contraintes du site en Arabie Saoudite.",
                        "- [00:00:05 --> 00:00:09] Il faut identifier les UPS pour les microcoupures.",
                        "- [00:00:09 --> 00:00:13] Point risque sur les souches et les master seeds en congélateurs.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            manager = MeetingManager(project_root=root, transcription_service=None)
            result = manager.generate_deliverables(transcript_path)
            manager.shutdown()

            self.assertEqual(result.output_dir, root / "data" / "meetings" / "outputs")
            minutes = result.paths.meeting_minutes_prefill_path.read_text(encoding="utf-8")
            dashboard = result.paths.dashboard_prefill_path.read_text(encoding="utf-8")
            actions = result.paths.action_log_path.read_text(encoding="utf-8")
            decisions = result.paths.decision_log_path.read_text(encoding="utf-8")
            risks = result.paths.risk_register_update_path.read_text(encoding="utf-8")
            impacts = result.paths.document_impact_log_path.read_text(encoding="utf-8")
            graph = result.paths.meeting_knowledge_graph_path.read_text(encoding="utf-8")

            self.assertIn("## 3. Sujets traités", minutes)
            self.assertIn("Meeting Manager Alpha 0.4", minutes)
            self.assertIn("## Documents à produire", dashboard)
            self.assertIn("Identifier le fournisseur d'électricité local", actions)
            self.assertIn("| ID | Décision | Contexte | Valideur | Date | Impact documentaire | Confiance | Validation |", decisions)
            self.assertIn("| ID | Risque | Cause | Impact | Probabilité | Gravité | Criticité | Responsable | Plan d'action | Confiance | Statut |", risks)
            self.assertIn("| ID | Document concerné | Modification à faire | Source métier | Priorité | Confiance | Statut |", impacts)
            self.assertIn('"nodes"', graph)

    def test_import_zip_detects_m4a_and_copies_to_audio_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_audio = root / "Réunion n01 CEVA.m4a"
            source_audio.write_bytes(b"fake m4a")
            zip_path = root / "meeting-source.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.write(source_audio, arcname="exports/Réunion n01 CEVA.m4a")

            manager = MeetingManager(project_root=root, transcription_service=None)
            imported_path = manager.import_audio_source(zip_path)
            manager.shutdown()

            self.assertEqual(imported_path, root / "data" / "meetings" / "audio" / "Réunion n01 CEVA.m4a")
            self.assertEqual(imported_path.read_bytes(), b"fake m4a")

    def test_start_processing_job_returns_future(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio_path = _write_fake_m4a(root)
            config = TranscriptionConfig(backend="fake", model_name="fake-model", language="fr")
            service = TranscriptionService(
                config=config,
                transcriber=FakeTranscriber(),
                audio_preprocessor=FFMpegAudioPreprocessor(config, runner=_fake_short_audio_runner),
            )
            manager = MeetingManager(project_root=root, transcription_service=service)

            future = manager.start_processing_job(audio_path, meeting_id="meeting-async")
            result = future.result(timeout=5)
            manager.shutdown()

            self.assertEqual(result.meeting_id, "meeting-async")
            self.assertTrue(result.transcript_text_path.exists())

    def test_long_audio_is_split_and_offsets_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio_path = _write_fake_m4a(root)
            config = TranscriptionConfig(
                backend="fake",
                model_name="fake-model",
                language="fr",
                segment_seconds=900,
            )

            def fake_long_audio_runner(command, timeout=None):
                if command[0] == "ffprobe":
                    return subprocess.CompletedProcess(command, 0, stdout='{"format": {"duration": "1801"}}', stderr="")
                pattern = Path(command[-1])
                for index in range(3):
                    (pattern.parent / f"segment_{index:05d}.wav").write_bytes(b"RIFF fake wav")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            class ChunkTranscriber:
                def transcribe(self, audio_path, language):
                    return [TranscriptSegment(index=1, start=1.0, end=2.0, text=f"Segment {audio_path.name}")]

            service = TranscriptionService(
                config=config,
                transcriber=ChunkTranscriber(),
                audio_preprocessor=FFMpegAudioPreprocessor(config, runner=fake_long_audio_runner),
            )

            segments = service.transcribe_audio(audio_path)

            self.assertEqual([segment.start for segment in segments], [1.0, 901.0, 1801.0])
            self.assertEqual([segment.end for segment in segments], [2.0, 902.0, 1802.0])
            self.assertEqual([segment.index for segment in segments], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
