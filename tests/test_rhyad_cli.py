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


if __name__ == "__main__":
    unittest.main()
