import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InternalDocumentationTest(unittest.TestCase):
    def test_internal_documentation_tree_exists(self):
        internal_dir = ROOT / "docs" / "internal"
        system_doc = internal_dir / "RHYAD-SYS-001.md"

        self.assertTrue(internal_dir.is_dir())
        self.assertTrue(system_doc.exists())
        self.assertIn(
            "Architecture du moteur documentaire RHYAD",
            system_doc.read_text(encoding="utf-8"),
        )

    def test_ceva_documents_do_not_reference_internal_documentation(self):
        forbidden_patterns = (
            "RHYAD-SYS",
            "docs/internal",
            "Architecture du moteur documentaire RHYAD",
        )

        for path in (ROOT / "config" / "documents").rglob("*.yaml"):
            content = path.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                self.assertNotIn(pattern, content, f"{path} references internal documentation")


if __name__ == "__main__":
    unittest.main()
