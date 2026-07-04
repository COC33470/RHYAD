import io
import tempfile
import unittest
from pathlib import Path

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


def _append_registry_document(root, code, official_code, family="000"):
    path = root / "config" / "document_registry.yaml"
    source_code = str(code).strip("'\"")
    with open(path, "a", encoding="utf-8") as f:
        f.write(
            "\n".join(
                [
                    "",
                    f"  - code: {code}",
                    f"    official_code: {official_code}",
                    "    revision: Rev0.1",
                    f"    family: '{family}'",
                    f"    source: config/documents/{source_code}.yaml",
                    "",
                ]
            )
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
