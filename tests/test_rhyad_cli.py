import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cli import rhyad


def _write_cli_fixture(root):
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  code: RHYAD",
                "  name: Test Project",
                "  client: Test Client",
                "  location: Test Location",
                "document:",
                "  revision: Rev0.1",
                "  status: Working Draft",
            ]
        ),
        encoding="utf-8",
    )
    (config_dir / "document_registry.yaml").write_text(
        "\n".join(
            [
                "documents:",
                "  - code: '002'",
                "    official_code: CEVA-RHYAD-002-PF",
                "    revision: Rev0.1",
                "    family: '000'",
                "    source: config/documents/002.yaml",
                "  - code: F01",
                "    official_code: CEVA-RHYAD-100-F01",
                "    revision: Rev0.1",
                "    family: '100'",
                "    source: config/documents/functions/F01.yaml",
            ]
        ),
        encoding="utf-8",
    )
    (config_dir / "rhyad_repository.yaml").write_text(
        "\n".join(
            [
                "repository:",
                "  code: RHYAD",
                "  families:",
                "    - code: '000'",
                "      title: Documents de Gouvernance Projet",
                "      documents:",
                "        - code: '002'",
                "          title: Programme Fonctionnel",
                "    - code: '100'",
                "      title: Fonctions du Programme Fonctionnel",
                "      documents:",
                "        - code: F01",
                "          title: Réception et Expédition",
            ]
        ),
        encoding="utf-8",
    )
    (root / "knowledge").mkdir()
    (root / "knowledge" / "project.yaml").write_text("project: {}\n", encoding="utf-8")
    (root / "knowledge" / "README.md").write_text("Knowledge\n", encoding="utf-8")
    (root / "inbox").mkdir()
    (root / "output").mkdir()


def _append_registry_document(root, code, official_code, family="000", title=None, source=None):
    path = root / "config" / "document_registry.yaml"
    source_code = str(code).strip("'\"")
    source = source or f"config/documents/{source_code}.yaml"
    with open(path, "a", encoding="utf-8") as f:
        lines = [
            "",
            f"  - code: {code}",
            f"    official_code: {official_code}",
        ]
        if title:
            lines.append(f"    title: {title}")
        lines.extend(
            [
                "    revision: Rev0.1",
                f"    family: '{family}'",
                f"    source: {source}",
                "",
            ]
        )
        f.write("\n".join(lines))


def _write_document_source(root, source, reference, title, status="Draft"):
    path = root / source
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"reference: {reference}",
                f"title: {title}",
                "revision: Rev0.1",
                f"status: {status}",
                "chapters:",
                "  - title: 1. Test",
                "    text: Test.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_figures_registry(root, file_path="assets/figures/000/test.png", used_in=None):
    used_in = used_in or []
    registry_path = root / "config" / "figures_registry.yaml"
    used_lines = "\n".join(f"      - \"{item}\"" for item in used_in) if used_in else "[]"
    registry_path.write_text(
        "\n".join(
            [
                "figures:",
                "  - id: \"FIG-000-001\"",
                "    title: \"Figure test\"",
                "    family: \"000\"",
                f"    file: \"{file_path}\"",
                "    caption: \"Légende test\"",
                "    source: \"RHYAD\"",
                "    status: \"Draft\"",
                "    used_in:" if used_in else "    used_in: []",
                used_lines if used_in else "",
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )


class RhyadCliTest(unittest.TestCase):
    def test_load_project_summary_and_registry_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)

            project = rhyad.load_project_summary(root / "config" / "project.yaml")
            registry = rhyad.load_registry_documents(root / "config" / "document_registry.yaml")

            self.assertEqual(project["project"]["client"], "Test Client")
            self.assertEqual(project["project"]["name"], "Test Project")
            self.assertEqual(len(registry), 2)
            self.assertEqual(registry[1]["official_code"], "CEVA-RHYAD-100-F01")

    def test_command_list_prints_official_code_title_and_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()

            exit_code = rhyad.command_list(root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("CEVA-RHYAD-002-PF | Programme Fonctionnel | famille 000", output)
            self.assertIn("CEVA-RHYAD-100-F01 | Réception et Expédition | famille 100", output)

    def test_generate_import_and_validate_proxy_existing_scripts(self):
        commands = []

        def fake_runner(command, timeout=None):
            commands.append(command)
            return rhyad.CommandResult(0, "ok")

        self.assertEqual(rhyad.command_generate("002", runner=fake_runner, stream=io.StringIO()), 0)
        self.assertEqual(rhyad.command_import("003", runner=fake_runner, stream=io.StringIO()), 0)
        self.assertEqual(rhyad.command_validate(runner=fake_runner, stream=io.StringIO()), 0)

        self.assertEqual(commands[0], ["python3", "scripts/main.py", "002"])
        self.assertEqual(commands[1], ["python3", "scripts/import_validated.py", "003"])
        self.assertEqual(commands[2], ["python3", "-m", "unittest", "discover"])

    def test_meetings_transcribe_reports_created_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            audio_path = root / "meeting.m4a"
            audio_path.write_bytes(b"fake m4a")
            stream = io.StringIO()

            class FakeMeetingManager:
                def __init__(self):
                    self.shutdown_called = False

                def process_audio(self, path):
                    self.audio_path = path
                    return SimpleNamespace(
                        meeting_id="meeting-test",
                        transcript_text_path=root / "data" / "meetings" / "transcripts" / "meeting-test" / "transcript.txt",
                        transcript_json_path=root / "data" / "meetings" / "transcripts" / "meeting-test" / "transcript.json",
                        summary_draft_path=root / "data" / "meetings" / "outputs" / "meeting-test" / "meeting_summary_draft.md",
                        segments=[object(), object()],
                    )

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["transcribe", str(audio_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.audio_path, audio_path)
            output = stream.getvalue()
            self.assertIn("RHYAD Meeting Manager", output)
            self.assertIn("Meeting ID: meeting-test", output)
            self.assertIn("Segments: 2", output)

    def test_meetings_import_reports_imported_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            zip_path = root / "meeting.zip"
            zip_path.write_bytes(b"fake zip")
            stream = io.StringIO()

            class FakeMeetingManager:
                def import_audio_source(self, path):
                    self.source_path = path
                    return root / "data" / "meetings" / "audio" / "Réunion n01 CEVA.m4a"

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["import", str(zip_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.source_path, zip_path)
            output = stream.getvalue()
            self.assertIn("RHYAD Meeting Manager", output)
            self.assertIn("Imported audio:", output)
            self.assertIn("Réunion n01 CEVA.m4a", output)

    def test_meetings_analyze_reports_alpha_02_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            transcript_path = root / "data" / "meetings" / "transcripts" / "meeting-test" / "transcript.txt"
            transcript_path.parent.mkdir(parents=True)
            transcript_path.write_text("[00:00:01 --> 00:00:03] Il faut vérifier les UPS.\n", encoding="utf-8")
            stream = io.StringIO()

            class FakeMeetingManager:
                def analyze_transcript(self, path):
                    self.transcript_path = path
                    return SimpleNamespace(
                        meeting_id="meeting-test",
                        transcript_cleaned_path=transcript_path.parent / "transcript_cleaned.md",
                        meeting_minutes_draft_path=root / "data" / "meetings" / "outputs" / "meeting-test" / "meeting_minutes_draft.md",
                        action_log_path=root / "data" / "meetings" / "outputs" / "meeting-test" / "action_log.md",
                        decision_log_path=root / "data" / "meetings" / "outputs" / "meeting-test" / "decision_log.md",
                        risk_register_update_path=root
                        / "data"
                        / "meetings"
                        / "outputs"
                        / "meeting-test"
                        / "risk_register_update.md",
                        document_impact_log_path=root
                        / "data"
                        / "meetings"
                        / "outputs"
                        / "meeting-test"
                        / "document_impact_log.md",
                    )

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["analyze", str(transcript_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.transcript_path, transcript_path)
            output = stream.getvalue()
            self.assertIn("RHYAD Meeting Manager", output)
            self.assertIn("Cleaned transcript:", output)
            self.assertIn("Meeting minutes draft:", output)
            self.assertIn("Document impact log:", output)

    def test_meetings_clean_reports_cleaned_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            transcript_path = root / "data" / "meetings" / "transcripts" / "transcript.txt"
            transcript_path.parent.mkdir(parents=True)
            transcript_path.write_text("[00:00:01 --> 00:00:03] Il faut vérifier les UPS.\n", encoding="utf-8")
            stream = io.StringIO()

            class FakeMeetingManager:
                def clean_transcript(self, path):
                    self.transcript_path = path
                    return transcript_path.parent / "transcript_cleaned.md"

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["clean", str(transcript_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.transcript_path, transcript_path)
            self.assertIn("Cleaned transcript:", stream.getvalue())

    def test_meetings_extract_reports_alpha_03_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            transcript_path = root / "data" / "meetings" / "transcripts" / "meeting-test" / "transcript_cleaned.md"
            transcript_path.parent.mkdir(parents=True)
            transcript_path.write_text("- [00:00:01 --> 00:00:03] Il faut vérifier les UPS.\n", encoding="utf-8")
            stream = io.StringIO()

            class FakeMeetingManager:
                def extract_meeting_data(self, path):
                    self.transcript_path = path
                    output_dir = root / "data" / "meetings" / "outputs" / "meeting-test"
                    return SimpleNamespace(
                        meeting_id="meeting-test",
                        paths=SimpleNamespace(
                            meeting_minutes_prefill_path=output_dir / "meeting_minutes_prefill.md",
                            dashboard_prefill_path=output_dir / "dashboard_prefill.md",
                            action_log_path=output_dir / "action_log.md",
                            decision_log_path=output_dir / "decision_log.md",
                            risk_register_update_path=output_dir / "risk_register_update.md",
                            document_impact_log_path=output_dir / "document_impact_log.md",
                        ),
                    )

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["extract", str(transcript_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.transcript_path, transcript_path)
            output = stream.getvalue()
            self.assertIn("Meeting minutes prefill:", output)
            self.assertIn("Dashboard prefill:", output)
            self.assertIn("Risk register update:", output)

    def test_meetings_generate_deliverables_reports_alpha_03_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            transcript_path = root / "data" / "meetings" / "transcripts" / "transcript_cleaned.md"
            transcript_path.parent.mkdir(parents=True)
            transcript_path.write_text("- [00:00:01 --> 00:00:03] Il faut vérifier les UPS.\n", encoding="utf-8")
            stream = io.StringIO()

            class FakeMeetingManager:
                def generate_deliverables(self, path):
                    self.transcript_path = path
                    output_dir = root / "data" / "meetings" / "outputs"
                    return SimpleNamespace(
                        meeting_id="transcript_cleaned",
                        paths=SimpleNamespace(
                            meeting_minutes_prefill_path=output_dir / "meeting_minutes_prefill.md",
                            dashboard_prefill_path=output_dir / "dashboard_prefill.md",
                            action_log_path=output_dir / "action_log.md",
                            decision_log_path=output_dir / "decision_log.md",
                            risk_register_update_path=output_dir / "risk_register_update.md",
                            document_impact_log_path=output_dir / "document_impact_log.md",
                        ),
                    )

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["generate-deliverables", str(transcript_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.transcript_path, transcript_path)
            output = stream.getvalue()
            self.assertIn("Meeting minutes prefill:", output)
            self.assertIn("Dashboard prefill:", output)
            self.assertIn("Document impact log:", output)

    def test_meetings_reason_reports_alpha_04_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            transcript_path = root / "data" / "meetings" / "transcripts" / "transcript_cleaned.md"
            transcript_path.parent.mkdir(parents=True)
            transcript_path.write_text("- [00:00:01 --> 00:00:03] UPS et microcoupures.\n", encoding="utf-8")
            stream = io.StringIO()

            class FakeMeetingManager:
                def reason_meeting(self, path):
                    self.transcript_path = path
                    output_dir = root / "data" / "meetings" / "outputs"
                    return SimpleNamespace(
                        meeting_id="transcript_cleaned",
                        paths=SimpleNamespace(
                            meeting_minutes_prefill_path=output_dir / "meeting_minutes_prefill.md",
                            dashboard_prefill_path=output_dir / "dashboard_prefill.md",
                            action_log_path=output_dir / "action_log.md",
                            decision_log_path=output_dir / "decision_log.md",
                            risk_register_update_path=output_dir / "risk_register_update.md",
                            document_impact_log_path=output_dir / "document_impact_log.md",
                            meeting_knowledge_graph_path=output_dir / "meeting_knowledge_graph.json",
                        ),
                    )

                def shutdown(self):
                    self.shutdown_called = True

            fake_manager = FakeMeetingManager()
            with patch("cli.rhyad.MeetingManager.from_project", return_value=fake_manager):
                exit_code = rhyad.command_meetings(["reason", str(transcript_path)], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_manager.shutdown_called)
            self.assertEqual(fake_manager.transcript_path, transcript_path)
            output = stream.getvalue()
            self.assertIn("Meeting minutes prefill:", output)
            self.assertIn("Meeting knowledge graph:", output)

    def test_paste_rejects_unknown_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()
            commands = []

            def fake_runner(command, timeout=None):
                commands.append(command)
                return rhyad.CommandResult(0, "unexpected")

            exit_code = rhyad.command_paste(
                "003",
                root=root,
                stdin=io.StringIO("# Glossaire\n"),
                runner=fake_runner,
                stream=stream,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(commands, [])
            self.assertFalse((root / "inbox" / "validated" / "003.md").exists())
            self.assertIn("Document inconnu", stream.getvalue())

    def test_paste_rejects_empty_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            _append_registry_document(root, "'003'", "CEVA-RHYAD-003-GLOSSAIRE")
            stream = io.StringIO()
            commands = []

            def fake_runner(command, timeout=None):
                commands.append(command)
                return rhyad.CommandResult(0, "unexpected")

            exit_code = rhyad.command_paste(
                "003",
                root=root,
                stdin=io.StringIO("  \n\n"),
                runner=fake_runner,
                stream=stream,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(commands, [])
            self.assertFalse((root / "inbox" / "validated" / "003.md").exists())
            self.assertIn("Erreur: contenu vide.", stream.getvalue())

    def test_paste_creates_markdown_launches_pipeline_and_prints_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            _append_registry_document(root, "'003'", "CEVA-RHYAD-003-GLOSSAIRE")
            stream = io.StringIO()
            commands = []
            markdown = "# Glossaire\n\nTexte validé.\n"

            def fake_runner(command, timeout=None):
                commands.append(command)
                return rhyad.CommandResult(
                    0,
                    "\n".join(
                        [
                            "YAML généré: config/documents/003.yaml",
                            "DOCX produit: output/docx/000/CEVA-RHYAD-003-GLOSSAIRE_Rev0.1.docx",
                            "PDF produit: output/pdf/000/CEVA-RHYAD-003-GLOSSAIRE_Rev0.1.pdf",
                            "Résultat tests:",
                            "Ran 36 tests in 0.1s",
                            "",
                            "OK",
                            "Sortie Git:",
                            "[main abc1234] Integrate validated 003",
                        ]
                    ),
                )

            exit_code = rhyad.command_paste(
                "003",
                root=root,
                stdin=io.StringIO(markdown),
                runner=fake_runner,
                stream=stream,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(commands, [["python3", "scripts/import_validated.py", "003"]])
            self.assertEqual((root / "inbox" / "validated" / "003.md").read_text(encoding="utf-8"), markdown)
            output = stream.getvalue()
            self.assertIn("RHYAD Import interactif", output)
            self.assertIn("CEVA-RHYAD-003-GLOSSAIRE", output)
            self.assertIn("Lignes importées :\n3", output)
            self.assertIn("DOCX :\nOK", output)
            self.assertIn("PDF :\nOK", output)
            self.assertIn("Tests :\n36 OK", output)
            self.assertIn("Commit :\nabc1234", output)

    def test_status_prints_project_git_registry_knowledge_and_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()

            def fake_runner(command, timeout=None):
                if command == ["git", "status", "--short"]:
                    return rhyad.CommandResult(0, "")
                if command == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                    return rhyad.CommandResult(0, "develop")
                if command == ["git", "log", "-1", "--pretty=%h %s"]:
                    return rhyad.CommandResult(0, "abc1234 Test commit")
                if command == ["python3", "-m", "unittest", "discover"]:
                    return rhyad.CommandResult(0, "OK")
                return rhyad.CommandResult(1, "unexpected")

            exit_code = rhyad.command_status(root=root, runner=fake_runner, stream=stream)

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("Client: Test Client", output)
            self.assertIn("Projet: Test Project", output)
            self.assertIn("Branche Git: develop", output)
            self.assertIn("Etat Git: clean", output)
            self.assertIn("Documents dans le registre: 2", output)
            self.assertIn("Fichiers Knowledge Core: 2", output)
            self.assertIn("Dernier commit: abc1234 Test commit", output)
            self.assertIn("Tests rapides: OK", output)

    def test_doctor_checks_expected_paths_and_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()

            def fake_runner(command, timeout=None):
                self.assertEqual(command, ["python3", "-m", "unittest", "discover"])
                return rhyad.CommandResult(0, "OK")

            with patch("cli.rhyad.find_libreoffice_executable", return_value="/usr/bin/soffice"):
                exit_code = rhyad.command_doctor(root=root, runner=fake_runner, stream=stream)

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("OK Python", output)
            self.assertIn("OK config/project.yaml", output)
            self.assertIn("OK config/document_registry.yaml", output)
            self.assertIn("OK tests: OK", output)

    def test_impact_prints_impacted_documents_and_traceability_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            (root / "knowledge" / "traceability.yaml").write_text(
                "\n".join(
                    [
                        "traceability:",
                        "  - source: D-014",
                        "    destination: CEVA-RHYAD-002-PF",
                        "    relation: decision",
                        "  - source: D-014",
                        "    destination: CEVA-RHYAD-100-F01",
                        "    relation: decision",
                    ]
                ),
                encoding="utf-8",
            )
            stream = io.StringIO()

            exit_code = rhyad.command_impact("D-014", root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("Objet analysé: D-014", output)
            self.assertIn("CEVA-RHYAD-002-PF (decision)", output)
            self.assertIn("CEVA-RHYAD-100-F01 (decision)", output)
            self.assertIn("Nombre d'impacts: 2", output)
            self.assertIn("Origine des relations:", output)

    def test_figures_list_prints_registry_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            _write_figures_registry(root, used_in=["CEVA-RHYAD-002-PF"])
            stream = io.StringIO()

            exit_code = rhyad.command_figures(["list"], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("Figures RHYAD", output)
            self.assertIn("FIG-000-001 | Figure test | assets/figures/000/test.png | Draft", output)
            self.assertIn("CEVA-RHYAD-002-PF", output)

    def test_figures_check_reports_existing_missing_and_unused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            _write_figures_registry(root)
            stream = io.StringIO()

            exit_code = rhyad.command_figures(["check"], root=root, stream=stream)

            self.assertEqual(exit_code, 1)
            output = stream.getvalue()
            self.assertIn("Figures déclarées: 1", output)
            self.assertIn("Figures manquantes: 1", output)
            self.assertIn("Figures non utilisées: 1", output)
            self.assertIn("FIG-000-001", output)

    def test_ui_opens_main_menu_and_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()
            inputs = iter(["0"])

            exit_code = rhyad.command_ui(root=root, stream=stream, input_func=lambda: next(inputs))

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("RHYAD", output)
            self.assertIn("Assistant AMO / Maîtrise d'Œuvre Industrielle", output)
            self.assertIn("Projet actif :", output)
            self.assertIn("Test Project", output)
            self.assertIn("0. Quitter", output)
            self.assertIn("Fermeture de l'interface RHYAD.", output)

    def test_ui_navigates_documents_menu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()
            inputs = iter(["2", "0", "0"])

            exit_code = rhyad.command_ui(root=root, stream=stream, input_func=lambda: next(inputs))

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("Menu Documents", output)
            self.assertIn("1. Afficher tous les documents", output)
            self.assertIn("6. Générer un document", output)
            self.assertIn("7. Nouveau document", output)

    def test_ui_generate_document_lists_only_existing_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            _write_document_source(
                root,
                "config/documents/002.yaml",
                "CEVA-RHYAD-002-PF",
                "Programme Fonctionnel",
            )
            _write_document_source(
                root,
                "config/documents/functions/F01.yaml",
                "CEVA-RHYAD-100-F01",
                "Réception et Expédition",
            )
            _append_registry_document(
                root,
                "MTH01",
                "CEVA-RHYAD-000-MTH01",
                title='"Guide Méthodologique RHYAD"',
            )
            stream = io.StringIO()
            inputs = iter(["2", "6", "1", "", "0", "0"])
            commands = []

            def fake_runner(command, timeout=None):
                commands.append(command)
                return rhyad.CommandResult(0, "generation ok")

            exit_code = rhyad.command_ui(
                root=root,
                runner=fake_runner,
                stream=stream,
                input_func=lambda: next(inputs),
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(commands, [["python3", "scripts/main.py", "002"]])
            output = stream.getvalue()
            self.assertIn("Documents existants", output)
            self.assertIn("CEVA-RHYAD-002-PF", output)
            self.assertIn("CEVA-RHYAD-100-F01", output)
            self.assertNotIn("CEVA-RHYAD-000-MTH01 | Guide Méthodologique RHYAD", output)

    def test_ui_new_document_creates_skeleton_and_launches_paste_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            _write_document_source(
                root,
                "config/documents/002.yaml",
                "CEVA-RHYAD-002-PF",
                "Programme Fonctionnel",
            )
            _write_document_source(
                root,
                "config/documents/functions/F01.yaml",
                "CEVA-RHYAD-100-F01",
                "Réception et Expédition",
            )
            _append_registry_document(
                root,
                "MTH01",
                "CEVA-RHYAD-000-MTH01",
                title='"Guide Méthodologique RHYAD"',
            )
            stream = io.StringIO()
            inputs = iter(["2", "7", "1", "", "0", "0"])
            pasted = []

            def fake_paste(document, root=None, runner=None, stream=None):
                pasted.append(document)
                print("Workflow paste lancé.", file=stream)
                return 0

            exit_code = rhyad.command_ui(
                root=root,
                stream=stream,
                input_func=lambda: next(inputs),
                paste_func=fake_paste,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(pasted, ["MTH01"])
            yaml_path = root / "config" / "documents" / "MTH01.yaml"
            self.assertTrue(yaml_path.exists())
            yaml_text = yaml_path.read_text(encoding="utf-8")
            self.assertIn('reference: "CEVA-RHYAD-000-MTH01"', yaml_text)
            self.assertIn('title: "Guide Méthodologique RHYAD"', yaml_text)
            self.assertIn('revision: "Rev0.1"', yaml_text)
            self.assertIn('status: "Draft"', yaml_text)
            output = stream.getvalue()
            self.assertIn("Nouveaux documents disponibles", output)
            self.assertIn("Document préparé : CEVA-RHYAD-000-MTH01", output)
            self.assertIn("Workflow paste lancé.", output)
            self.assertNotIn("config/documents/MTH01.yaml", output)

    def test_ui_displays_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            stream = io.StringIO()
            inputs = iter(["1", "", "0"])

            def fake_runner(command, timeout=None):
                if command == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                    return rhyad.CommandResult(0, "develop")
                if command == ["git", "status", "--short"]:
                    return rhyad.CommandResult(0, "")
                return rhyad.CommandResult(0, "")

            exit_code = rhyad.command_ui(
                root=root,
                runner=fake_runner,
                stream=stream,
                input_func=lambda: next(inputs),
            )

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("Tableau de bord", output)
            self.assertIn("Projet : Test Project", output)
            self.assertIn("Git : develop / clean", output)
            self.assertIn("Dernière génération : Aucune", output)
            self.assertIn("Documents Draft :", output)
            self.assertIn("Décisions ouvertes :", output)
            self.assertIn("Prochaine réunion :", output)

    def test_dashboard_prints_project_documents_knowledge_tests_and_latest_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_cli_fixture(root)
            (root / "knowledge" / "decisions.yaml").write_text(
                "decisions:\n  - id: D-001\n", encoding="utf-8"
            )
            (root / "knowledge" / "risks.yaml").write_text(
                "risks:\n  - id: R-001\n  - id: R-002\n", encoding="utf-8"
            )
            (root / "knowledge" / "assumptions.yaml").write_text("assumptions: []\n", encoding="utf-8")
            (root / "knowledge" / "requirements.yaml").write_text(
                "requirements:\n  - id: REQ-001\n", encoding="utf-8"
            )
            (root / "knowledge" / "interfaces.yaml").write_text("interfaces: []\n", encoding="utf-8")
            docx = root / "output" / "docx" / "000" / "CEVA-RHYAD-002-PF_Rev0.1.docx"
            pdf = root / "output" / "pdf" / "000" / "CEVA-RHYAD-002-PF_Rev0.1.pdf"
            docx.parent.mkdir(parents=True, exist_ok=True)
            pdf.parent.mkdir(parents=True, exist_ok=True)
            docx.write_text("docx", encoding="utf-8")
            pdf.write_text("pdf", encoding="utf-8")
            stream = io.StringIO()

            def fake_runner(command, timeout=None):
                if command == ["python3", "-m", "unittest", "discover"]:
                    return rhyad.CommandResult(0, "Ran 25 tests in 0.1s\n\nOK")
                if command == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                    return rhyad.CommandResult(0, "develop")
                if command == ["git", "log", "-1", "--pretty=%h %s"]:
                    return rhyad.CommandResult(0, "abc1234 Test commit")
                return rhyad.CommandResult(1, "unexpected")

            exit_code = rhyad.command_dashboard(root=root, runner=fake_runner, stream=stream)

            self.assertEqual(exit_code, 0)
            output = stream.getvalue()
            self.assertIn("Projet: Test Project", output)
            self.assertIn("Client: Test Client", output)
            self.assertIn("Branche Git: develop", output)
            self.assertIn("Dernier commit: abc1234 Test commit", output)
            self.assertIn("- nombre total: 2", output)
            self.assertIn("- générés: 1", output)
            self.assertIn("- en attente: 1", output)
            self.assertIn("- décisions: 1", output)
            self.assertIn("- risques: 2", output)
            self.assertIn("- exigences: 1", output)
            self.assertIn("- nombre: 25", output)
            self.assertIn("- résultat: OK", output)
            self.assertIn("Dernière génération:", output)


if __name__ == "__main__":
    unittest.main()
