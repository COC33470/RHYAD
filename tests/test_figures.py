import base64
import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from engine.core.document_builder import build_document
from engine.core.figures import check_figures, load_figures_registry


PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _write_registry(root, file_path="assets/figures/000/test.png", used_in=None):
    used_in = used_in or []
    used_lines = "\n".join(f"      - \"{item}\"" for item in used_in) if used_in else "[]"
    registry_path = root / "config" / "figures_registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
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
    return registry_path


def _write_document(root):
    yaml_path = root / "document.yaml"
    yaml_path.write_text(
        "\n".join(
            [
                "reference: TEST-FIG",
                "title: Test figures",
                "chapters:",
                "  - title: 1. Figures",
                "    text: Chapitre de test.",
                "    figures:",
                "      - id: FIG-000-001",
            ]
        ),
        encoding="utf-8",
    )
    return yaml_path


class FiguresTest(unittest.TestCase):
    def test_load_figures_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = _write_registry(root)

            registry = load_figures_registry(registry_path)

            self.assertEqual(registry["figures"][0]["id"], "FIG-000-001")
            self.assertEqual(registry["figures"][0]["caption"], "Légende test")

    def test_build_document_inserts_existing_figure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root, used_in=["TEST-FIG"])
            figure_path = root / "assets" / "figures" / "000" / "test.png"
            figure_path.parent.mkdir(parents=True, exist_ok=True)
            figure_path.write_bytes(base64.b64decode(PNG_1X1))
            yaml_path = _write_document(root)
            output_path = root / "out" / "test.docx"

            build_document(yaml_path, output_path, project_config={}, project_root=root)

            with zipfile.ZipFile(output_path) as docx:
                names = docx.namelist()
                document_xml = docx.read("word/document.xml").decode("utf-8")

            self.assertTrue(any(name.startswith("word/media/") for name in names))
            self.assertIn("Figure FIG-000-001 - Légende test", document_xml)

    def test_build_document_warns_for_missing_figure_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root, used_in=["TEST-FIG"])
            yaml_path = _write_document(root)
            output_path = root / "out" / "test.docx"
            stream = io.StringIO()

            with contextlib.redirect_stdout(stream):
                build_document(yaml_path, output_path, project_config={}, project_root=root)

            self.assertTrue(output_path.exists())
            self.assertIn("WARNING: Figure file not found for FIG-000-001", stream.getvalue())

    def test_check_figures_reports_existing_missing_and_unused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = _write_registry(root)

            result = check_figures(root, registry_path)

            self.assertEqual(result["declared"], 1)
            self.assertEqual(len(result["missing"]), 1)
            self.assertEqual(len(result["unused"]), 1)


if __name__ == "__main__":
    unittest.main()
