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
                text="Décision validée pour CEVA-RHYAD-002-PF avant le 12/07.",
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

            transcript_text = result.transcript_text_path.read_text(encoding="utf-8")
            self.assertIn("[00:00:00 --> 00:00:02]", transcript_text)
            self.assertIn("CEVA-RHYAD-002-PF", transcript_text)

            transcript_json = json.loads(result.transcript_json_path.read_text(encoding="utf-8"))
            self.assertEqual(transcript_json["language"], "fr")
            self.assertEqual(transcript_json["backend"], "fake")
            self.assertEqual(transcript_json["segments"][0]["text"], result.segments[0].text)
            self.assertEqual(transcript_json["analysis_draft"]["documents"], ["CEVA-RHYAD-002-PF"])

            summary = result.summary_draft_path.read_text(encoding="utf-8")
            self.assertIn("## Extraction IA à préparer", summary)
            self.assertIn("### Décisions candidates", summary)
            self.assertIn("CEVA-RHYAD-002-PF", summary)

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
