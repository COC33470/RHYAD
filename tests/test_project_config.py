import tempfile
import unittest
from pathlib import Path

from scripts.main import load_project_config, resolve_output_dir


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


if __name__ == "__main__":
    unittest.main()
