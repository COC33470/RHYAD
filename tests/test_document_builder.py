import tempfile
import unittest
import zipfile
import re
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
            self.assertIn("Reference", header_xml)
            self.assertIn("TEST-F99", header_xml)
            self.assertIn("Test document", header_xml)
            self.assertIn("Revision", header_xml)
            self.assertIn("Status", header_xml)
            self.assertIn("PAGE", footer_xml)
            self.assertIn("NUMPAGES", footer_xml)
            self.assertIn("INTERNAL", footer_xml)

    def test_document_template_uses_default_header_after_cover_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yaml_path = root / "F99.yaml"
            yaml_path.write_text(
                "\n".join(
                    [
                        "reference: TEST-F99",
                        "title: Test document",
                        "revision: Rev1",
                        "status: Validated",
                        "chapters:",
                        "  - title: 1. Purpose",
                        "    text: Test body.",
                    ]
                ),
                encoding="utf-8",
            )

            output_path = root / "output" / "docx" / "TEST-F99.docx"
            project_config = {
                "document": {
                    "confidentiality": "INTERNAL",
                },
            }

            build_document(yaml_path, output_path, project_config=project_config, project_root=root)

            with zipfile.ZipFile(output_path) as docx:
                document_xml = docx.read("word/document.xml").decode("utf-8")
                header_xml = docx.read("word/header1.xml").decode("utf-8")
                footer_xml_parts = [
                    docx.read(name).decode("utf-8")
                    for name in docx.namelist()
                    if name.startswith("word/footer")
                ]

            page_width = int(re.search(r'<w:pgSz[^>]*w:w="(\d+)"', document_xml).group(1))
            left_margin = int(re.search(r'<w:pgMar[^>]*w:left="(\d+)"', document_xml).group(1))
            right_margin = int(re.search(r'<w:pgMar[^>]*w:right="(\d+)"', document_xml).group(1))
            body_width = page_width - left_margin - right_margin
            header_width = int(re.search(r'<w:tblW[^>]*w:w="(\d+)"', header_xml).group(1))

            self.assertIn("<w:titlePg/>", document_xml)
            self.assertIn('<w:headerReference w:type="default"', document_xml)
            self.assertNotIn('<w:headerReference w:type="first"', document_xml)
            self.assertIn('<w:footerReference w:type="default"', document_xml)
            self.assertIn('<w:footerReference w:type="first"', document_xml)
            self.assertEqual(header_width, body_width)
            self.assertIn('<w:bottom w:val="single" w:sz="4" w:space="0" w:color="29306B"/>', header_xml)
            self.assertEqual(len(footer_xml_parts), 2)
            self.assertTrue(all("PAGE" in footer_xml for footer_xml in footer_xml_parts))
            self.assertTrue(all("NUMPAGES" in footer_xml for footer_xml in footer_xml_parts))
            self.assertTrue(all("INTERNAL" in footer_xml for footer_xml in footer_xml_parts))

    def test_build_document_prefers_document_revision_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yaml_path = root / "003.yaml"
            yaml_path.write_text(
                "\n".join(
                    [
                        "reference: CEVA-RHYAD-003-GLOSSAIRE",
                        "title: Glossaire",
                        "revision: Rev0.1",
                        "status: Validated",
                        "chapters:",
                        "  - title: 1. Objet",
                        "    text: Texte validé.",
                    ]
                ),
                encoding="utf-8",
            )

            output_path = root / "output" / "docx" / "CEVA-RHYAD-003-GLOSSAIRE.docx"
            project_config = {
                "project": {"name": "Test Project"},
                "document": {
                    "revision": "A1.0",
                    "status": "DRAFT",
                    "confidentiality": "INTERNAL",
                },
            }

            build_document(yaml_path, output_path, project_config=project_config, project_root=root)

            generated = Document(output_path)
            table_text = "\n".join(
                cell.text for table in generated.tables for row in table.rows for cell in row.cells
            )

            self.assertIn("Rev0.1", table_text)
            self.assertIn("Validated", table_text)

    def test_build_document_renders_ordered_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yaml_path = root / "F01.yaml"
            yaml_path.write_text(
                "\n".join(
                    [
                        "reference: CEVA-RHYAD-100-F01",
                        "title: Réception et Expédition",
                        "chapters:",
                        "  - title: 3. Périmètre",
                        "    blocks:",
                        "      - type: text",
                        "        text: 'La fonction couvre notamment :'",
                        "      - type: list",
                        "        items:",
                        "          - Flux entrants",
                        "          - Flux sortants",
                        "      - type: text",
                        "        text: 'Sont exclus :'",
                        "      - type: list",
                        "        items:",
                        "          - Procédures qualité",
                    ]
                ),
                encoding="utf-8",
            )

            output_path = root / "output" / "docx" / "CEVA-RHYAD-100-F01.docx"
            build_document(yaml_path, output_path, project_root=root)

            generated = Document(output_path)
            paragraph_texts = [p.text for p in generated.paragraphs]
            paragraph_styles = {p.text: p.style.name for p in generated.paragraphs if p.text}

            expected_order = [
                "La fonction couvre notamment :",
                "Flux entrants",
                "Flux sortants",
                "Sont exclus :",
                "Procédures qualité",
            ]
            positions = [paragraph_texts.index(text) for text in expected_order]

            self.assertEqual(positions, sorted(positions))
            self.assertEqual(paragraph_styles["Flux entrants"], "List Bullet")
            self.assertEqual(paragraph_styles["Procédures qualité"], "List Bullet")

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
