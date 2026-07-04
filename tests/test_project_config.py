import tempfile
import unittest
from pathlib import Path

from scripts.main import (
    find_repository_document,
    load_project_config,
    load_repository_config,
    resolve_family_output_dir,
    resolve_output_dir,
)


class ProjectConfigTest(unittest.TestCase):
    def test_load_project_config_validates_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.yaml"
            path.write_text(
                "\n".join(
                    [
                        "project:",
                        "  code: TEST",
                        "  name: Test Project",
                        "document:",
                        "  revision: T1",
                        "  status: DRAFT",
                        "output:",
                        "  docx: output/docx",
                        "  pdf: output/pdf",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_project_config(path)

            self.assertEqual(config["project"]["code"], "TEST")
            self.assertTrue(str(resolve_output_dir(config, "docx", "fallback")).endswith("output/docx"))

    def test_load_project_config_rejects_missing_pdf_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.yaml"
            path.write_text(
                "\n".join(
                    [
                        "project:",
                        "  code: TEST",
                        "  name: Test Project",
                        "document:",
                        "  revision: T1",
                        "  status: DRAFT",
                        "output:",
                        "  docx: output/docx",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "output.pdf"):
                load_project_config(path)

    def test_repository_routes_documents_to_official_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rhyad_repository.yaml"
            path.write_text(
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

            repository = load_repository_config(path)
            project_config = {"output": {"docx": "output/docx"}}

            doc_002 = find_repository_document(repository, "002")
            doc_f01 = find_repository_document(repository, "F01")

            self.assertEqual(doc_002["family_code"], "000")
            self.assertEqual(doc_f01["family_code"], "100")
            self.assertTrue(
                str(resolve_family_output_dir(project_config, "docx", "fallback", doc_002)).endswith(
                    "output/docx/000"
                )
            )
            self.assertTrue(
                str(resolve_family_output_dir(project_config, "docx", "fallback", doc_f01)).endswith(
                    "output/docx/100"
                )
            )


if __name__ == "__main__":
    unittest.main()
