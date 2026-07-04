import io
import tempfile
import unittest
from pathlib import Path

import yaml

from cli import rhyad
from engine.core.traceability_suggester import suggest_traceability


def _write_registry(root):
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "document_registry.yaml").write_text(
        "\n".join(
            [
                "documents:",
                "  - code: '001'",
                "    official_code: CEVA-RHYAD-001-CHARTE",
                "    revision: Rev0.1",
                "    family: '000'",
                "    source: config/documents/001.yaml",
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


def _write_documents(root):
    documents_dir = root / "config" / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    (documents_dir / "001.yaml").write_text(
        "\n".join(
            [
                "reference: CEVA-RHYAD-001-CHARTE",
                "title: Charte",
                "chapters:",
                "  - title: Référence",
                "    text: Le périmètre est défini dans RHYAD-002.",
                "  - title: Auto-référence",
                "    text: Le document CEVA-RHYAD-001-CHARTE reste la source.",
            ]
        ),
        encoding="utf-8",
    )
    (documents_dir / "002.yaml").write_text(
        "\n".join(
            [
                "reference: CEVA-RHYAD-002-PF",
                "title: Programme Fonctionnel",
                "chapters:",
                "  - title: Fonctions",
                "    bullets:",
                "      - F01",
            ]
        ),
        encoding="utf-8",
    )
    return documents_dir


class TraceabilitySuggesterTest(unittest.TestCase):
    def test_suggest_traceability_detects_explicit_yaml_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            documents_dir = _write_documents(root)
            knowledge_dir = root / "knowledge"
            knowledge_dir.mkdir()
            suggestions_path = knowledge_dir / "traceability_suggestions.yaml"

            result = suggest_traceability(
                documents_dir=documents_dir,
                inbox_validated_dir=root / "inbox" / "validated",
                knowledge_dir=knowledge_dir,
                registry_path=root / "config" / "document_registry.yaml",
                suggestions_path=suggestions_path,
            )

            self.assertEqual(result["suggestion_count"], 2)
            payload = yaml.safe_load(suggestions_path.read_text(encoding="utf-8"))
            suggestions = payload["traceability_suggestions"]
            self.assertIn(
                {
                    "source": "CEVA-RHYAD-001-CHARTE",
                    "destination": "CEVA-RHYAD-002-PF",
                    "relation": "explicit-reference",
                    "status": "proposed",
                    "evidence": suggestions[0]["evidence"],
                },
                suggestions,
            )
            self.assertTrue(
                any(
                    suggestion["source"] == "CEVA-RHYAD-002-PF"
                    and suggestion["destination"] == "CEVA-RHYAD-100-F01"
                    and suggestion["evidence"]["matched_reference"] == "F01"
                    for suggestion in suggestions
                )
            )

    def test_suggest_traceability_does_not_modify_validated_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            documents_dir = _write_documents(root)
            knowledge_dir = root / "knowledge"
            knowledge_dir.mkdir()
            traceability_path = knowledge_dir / "traceability.yaml"
            original_traceability = "traceability: []\n"
            traceability_path.write_text(original_traceability, encoding="utf-8")

            suggest_traceability(
                documents_dir=documents_dir,
                inbox_validated_dir=root / "inbox" / "validated",
                knowledge_dir=knowledge_dir,
                registry_path=root / "config" / "document_registry.yaml",
                suggestions_path=knowledge_dir / "traceability_suggestions.yaml",
            )

            self.assertEqual(traceability_path.read_text(encoding="utf-8"), original_traceability)

    def test_suggest_traceability_reads_inbox_validated_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            documents_dir = root / "config" / "documents"
            documents_dir.mkdir(parents=True)
            inbox_dir = root / "inbox" / "validated"
            inbox_dir.mkdir(parents=True)
            (inbox_dir / "001.md").write_text(
                "title: Charte\n\n# Référence\n\nVoir RHYAD-002.\n",
                encoding="utf-8",
            )
            knowledge_dir = root / "knowledge"
            knowledge_dir.mkdir()

            result = suggest_traceability(
                documents_dir=documents_dir,
                inbox_validated_dir=inbox_dir,
                knowledge_dir=knowledge_dir,
                registry_path=root / "config" / "document_registry.yaml",
                suggestions_path=knowledge_dir / "traceability_suggestions.yaml",
            )

            self.assertEqual(result["suggestion_count"], 1)
            self.assertEqual(result["suggestions"][0]["source"], "CEVA-RHYAD-001-CHARTE")
            self.assertEqual(result["suggestions"][0]["destination"], "CEVA-RHYAD-002-PF")
            self.assertEqual(result["suggestions"][0]["evidence"]["source_file"], str(inbox_dir / "001.md"))

    def test_cli_trace_suggest_writes_suggestions_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            _write_documents(root)
            (root / "knowledge").mkdir(exist_ok=True)
            (root / "inbox" / "validated").mkdir(parents=True)
            stream = io.StringIO()

            exit_code = rhyad.command_trace(["suggest"], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / "knowledge" / "traceability_suggestions.yaml").exists())
            self.assertIn("Nombre de propositions: 2", stream.getvalue())
            self.assertIn("n'a pas été modifié", stream.getvalue())

    def test_cli_trace_approve_does_not_modify_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge_dir = root / "knowledge"
            knowledge_dir.mkdir()
            traceability_path = knowledge_dir / "traceability.yaml"
            original = "traceability: []\n"
            traceability_path.write_text(original, encoding="utf-8")
            stream = io.StringIO()

            exit_code = rhyad.command_trace(["approve"], root=root, stream=stream)

            self.assertEqual(exit_code, 0)
            self.assertEqual(traceability_path.read_text(encoding="utf-8"), original)
            self.assertIn("Validation automatique non activée", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
