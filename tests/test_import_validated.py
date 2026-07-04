import unittest
import tempfile
from pathlib import Path
from unittest import mock

from engine.core.document_builder import validate_document_config
import scripts.main as main_script
import scripts.import_validated as importer
from scripts.import_validated import markdown_to_document


def _write_pipeline_config(root):
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
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
                "  language: fr",
                "  confidentiality: INTERNAL",
                "output:",
                "  docx: output/docx",
                "  pdf: output/pdf",
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
                "        - code: '003'",
                "          title: Glossaire",
            ]
        ),
        encoding="utf-8",
    )
    (config_dir / "document_registry.yaml").write_text(
        "\n".join(
            [
                "documents:",
                "  - code: '003'",
                "    official_code: CEVA-RHYAD-003-GLOSSAIRE",
                "    revision: Rev0.1",
                "    family: '000'",
                "    source: config/documents/003.yaml",
            ]
        ),
        encoding="utf-8",
    )


def _patch_pipeline_paths(root):
    return mock.patch.multiple(
        importer,
        ROOT=root,
        INBOX_ROOT=root / "inbox",
        INBOX_VALIDATED_DIR=root / "inbox" / "validated",
        INBOX_PROCESSED_DIR=root / "inbox" / "processed",
        INBOX_REJECTED_DIR=root / "inbox" / "rejected",
        INBOX_DIR=root / "inbox" / "validated",
        LOG_PATH=root / "logs" / "import.log",
        PROJECT_CONFIG=root / "config" / "project.yaml",
        REPOSITORY_CONFIG=root / "config" / "rhyad_repository.yaml",
        DOCUMENT_REGISTRY_CONFIG=root / "config" / "document_registry.yaml",
    )


class ImportValidatedTest(unittest.TestCase):
    def test_markdown_to_document_converts_metadata_chapters_lists_and_tables(self):
        markdown = """reference: "TST-001"
title: "Test Document"
subtitle: "Validated Content"
revision: "Rev.0.1"
status: "Working Draft"

# 1. Objet

Texte validé.

- Point validé
- Deuxième point validé

# 2. Tableau

| Référence | Document |
|---|---|
| RHYAD-001 | Charte Projet |
| RHYAD-002 | Programme Fonctionnel |
"""

        document = markdown_to_document(markdown, "TST-001")

        self.assertEqual(document["reference"], "TST-001")
        self.assertEqual(document["title"], "Test Document")
        self.assertEqual(document["subtitle"], "Validated Content")
        self.assertEqual(document["revision"], "Rev.0.1")
        self.assertEqual(document["status"], "Working Draft")
        self.assertEqual(len(document["chapters"]), 2)
        self.assertEqual(document["chapters"][0]["bullets"], ["Point validé", "Deuxième point validé"])
        self.assertEqual(document["chapters"][1]["tables"][0]["headers"], ["Référence", "Document"])
        self.assertEqual(
            document["chapters"][1]["tables"][0]["rows"][0],
            ["RHYAD-001", "Charte Projet"],
        )
        validate_document_config(document, "TST-001.yaml")

    def test_markdown_to_document_uses_repository_title_when_title_missing(self):
        markdown = "Texte validé."

        document = markdown_to_document(markdown, "003", repository_title="Glossaire")

        self.assertEqual(document["reference"], "003")
        self.assertEqual(document["title"], "Glossaire")
        self.assertEqual(document["chapters"][0]["title"], "Contenu")

    def test_normalize_document_code_accepts_compact_design_basis_codes(self):
        self.assertEqual(importer.normalize_document_code("DB01"), "DB-001")
        self.assertEqual(importer.normalize_document_code("reg5"), "REG-005")
        self.assertEqual(importer.normalize_document_code("001A"), "001A")

    def test_import_pipeline_success_generates_yaml_outputs_archive_log_and_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pipeline_config(root)
            validated_dir = root / "inbox" / "validated"
            validated_dir.mkdir(parents=True)
            (validated_dir / "003.md").write_text(
                """title: "Glossaire"
status: "Working Draft"

# 1. Objet

Texte validé.

- Terme validé

# 2. Tableau

| Acronym | Definition |
|---|---|
| GMP | Good Manufacturing Practices |
""",
                encoding="utf-8",
            )
            commands = []

            def fake_run(command):
                commands.append(command)
                if command == ["python3", "scripts/main.py", "003"]:
                    docx_path = root / "output" / "docx" / "000" / "CEVA-RHYAD-003-GLOSSAIRE_Rev0.1.docx"
                    pdf_path = root / "output" / "pdf" / "000" / "CEVA-RHYAD-003-GLOSSAIRE_Rev0.1.pdf"
                    docx_path.parent.mkdir(parents=True, exist_ok=True)
                    pdf_path.parent.mkdir(parents=True, exist_ok=True)
                    docx_path.write_text("docx", encoding="utf-8")
                    pdf_path.write_text("pdf", encoding="utf-8")
                    return "generation ok"
                if command == ["python3", "-m", "unittest", "discover"]:
                    return "tests ok"
                if command == ["git", "add", "."]:
                    return ""
                if command == ["git", "commit", "-m", "Integrate validated 003"]:
                    return "[develop abc1234] Integrate validated 003"
                raise AssertionError(f"Unexpected command: {command}")

            with _patch_pipeline_paths(root), mock.patch.object(main_script, "ROOT", root):
                result = importer.import_validated_content("003", run_command=fake_run)

            yaml_path = root / "config" / "documents" / "003.yaml"
            self.assertTrue(yaml_path.exists())
            yaml_data = importer.yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            self.assertEqual(yaml_data["reference"], "CEVA-RHYAD-003-GLOSSAIRE")
            self.assertEqual(yaml_data["revision"], "Rev0.1")
            self.assertEqual(yaml_data["status"], "Working Draft")
            self.assertEqual(yaml_data["chapters"][0]["text"], "Texte validé.")

            self.assertTrue(result["docx_path"].exists())
            self.assertTrue(result["pdf_path"].exists())
            self.assertEqual(result["family"], "000")
            self.assertTrue((root / "inbox" / "processed" / "003.md").exists())
            self.assertFalse((root / "inbox" / "validated" / "003.md").exists())

            log_text = (root / "logs" / "import.log").read_text(encoding="utf-8")
            self.assertIn("document=003", log_text)
            self.assertIn("result=success", log_text)
            self.assertIn("commit=Integrate validated 003", log_text)
            self.assertIn(["git", "commit", "-m", "Integrate validated 003"], commands)

    def test_import_pipeline_rejects_invalid_markdown_and_writes_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pipeline_config(root)
            validated_dir = root / "inbox" / "validated"
            validated_dir.mkdir(parents=True)
            (validated_dir / "003.md").write_text(
                """title: "Glossaire"

# 1. Tableau invalide

| A | B |
|---|---|
| Une seule cellule |
""",
                encoding="utf-8",
            )
            commands = []

            def fake_run(command):
                commands.append(command)
                raise AssertionError(f"Unexpected command: {command}")

            with _patch_pipeline_paths(root), mock.patch.object(main_script, "ROOT", root):
                with self.assertRaises(importer.ImportErrorWithContext):
                    importer.import_validated_content("003", run_command=fake_run)

            self.assertFalse((root / "inbox" / "validated" / "003.md").exists())
            self.assertTrue((root / "inbox" / "rejected" / "003.md").exists())
            self.assertTrue((root / "inbox" / "rejected" / "003.md.log").exists())
            self.assertFalse((root / "inbox" / "processed" / "003.md").exists())
            self.assertEqual(commands, [])

            import_log = (root / "logs" / "import.log").read_text(encoding="utf-8")
            rejection_log = (root / "inbox" / "rejected" / "003.md.log").read_text(encoding="utf-8")
            self.assertIn("result=rejected", import_log)
            self.assertIn("Markdown table row has 1 cells", rejection_log)


if __name__ == "__main__":
    unittest.main()
