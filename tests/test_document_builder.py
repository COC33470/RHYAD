import tempfile
import unittest
import zipfile
from pathlib import Path

from docx import Document

from engine.core.document_builder import build_document, validate_document_config


class DocumentBuilderTest(unittest.TestCase):
    def test_build_document_with_project_metadata_and_optional_missing_logo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yaml_path = root / "F99.yaml"
            yaml_path.write_text(
                "\n".join(
                    [
                        "reference: TEST-F99",
                        "title: Test document",
                        "subtitle: Revision T",
                        "chapters:",
                        "  - title: 1. Purpose",
                        "    text: Test body.",
                        "  - title: 2. References",
                        "    bullets:",
                        "      - REF-001",
                        "    tables:",
                        "      - title: Test table",
                        "        headers: [Code, Description]",
                        "        rows:",
                        "          - [A, Alpha]",
                        "          - [B, Beta]",
                    ]
                ),
                encoding="utf-8",
            )

            output_path = root / "output" / "docx" / "TEST-F99.docx"
            project_config = {
                "project": {
                    "name": "Test Project",
                    "client": "Test Client",
                    "location": "Test Location",
                },
                "document": {
                    "revision": "T1",
                    "status": "DRAFT",
                    "confidentiality": "INTERNAL",
                },
                "authors": {"author": "Test Author", "company": "Test Company"},
                "branding": {"logo_ceva": "assets/logos/missing.png"},
            }

            build_document(
                yaml_path,
                output_path,
                project_config=project_config,
                project_root=root,
            )

            self.assertTrue(output_path.exists())
            generated = Document(output_path)
            paragraph_text = "\n".join(p.text for p in generated.paragraphs)
            table_text = "\n".join(
                cell.text for table in generated.tables for row in table.rows for cell in row.cells
            )

            self.assertIn("TEST-F99", paragraph_text)
            self.assertIn("Test document", paragraph_text)
            self.assertIn("REF-001", paragraph_text)
            self.assertIn("Test Project", paragraph_text)
            self.assertIn("Document Number", table_text)
            self.assertIn("TEST-F99", table_text)
            self.assertIn("DRAFT", table_text)
            self.assertIn("Code", table_text)
            self.assertIn("Alpha", table_text)

            with zipfile.ZipFile(output_path) as docx:
                document_xml = docx.read("word/document.xml").decode("utf-8")
                header_xml = docx.read("word/header1.xml").decode("utf-8")
                footer_xml = docx.read("word/footer1.xml").decode("utf-8")

            self.assertIn("Document Control", document_xml)
            self.assertIn("Test table", document_xml)
            self.assertIn('TOC \\o "1-3" \\h \\z \\u', document_xml)
            self.assertIn("Document", header_xml)
            self.assertIn("TEST-F99", header_xml)
            self.assertIn("Revision", header_xml)
            self.assertIn("Status", header_xml)
            self.assertIn("PAGE", footer_xml)
            self.assertIn("NUMPAGES", footer_xml)
            self.assertIn("INTERNAL", footer_xml)

    def test_validate_document_config_requires_chapters(self):
        with self.assertRaisesRegex(ValueError, "chapters"):
            validate_document_config(
                {"reference": "TEST-F99", "title": "Test document"},
                Path("F99.yaml"),
            )

    def test_validate_document_config_rejects_table_row_width_mismatch(self):
        with self.assertRaisesRegex(ValueError, "must contain 2 values"):
            validate_document_config(
                {
                    "reference": "TEST-F99",
                    "title": "Test document",
                    "chapters": [
                        {
                            "title": "1. Test",
                            "tables": [
                                {
                                    "headers": ["Code", "Description"],
                                    "rows": [["A"]],
                                }
                            ],
                        }
                    ],
                },
                Path("F99.yaml"),
            )


if __name__ == "__main__":
    unittest.main()
