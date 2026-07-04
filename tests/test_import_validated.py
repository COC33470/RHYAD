import unittest

from engine.core.document_builder import validate_document_config
from scripts.import_validated import markdown_to_document


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


if __name__ == "__main__":
    unittest.main()
