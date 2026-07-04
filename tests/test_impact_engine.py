import tempfile
import unittest
from pathlib import Path

from engine.core.impact_engine import get_impacts, load_traceability


def _write_traceability(root, traceability_text):
    knowledge_dir = root / "knowledge"
    knowledge_dir.mkdir(parents=True)
    path = knowledge_dir / "traceability.yaml"
    path.write_text(traceability_text, encoding="utf-8")
    return path


def _write_registry(root):
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    path = config_dir / "document_registry.yaml"
    path.write_text(
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
    return path


class ImpactEngineTest(unittest.TestCase):
    def test_load_traceability_reads_yaml_relations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_traceability(
                root,
                "\n".join(
                    [
                        "traceability:",
                        "  - source: D-001",
                        "    destination: CEVA-RHYAD-002-PF",
                        "    relation: decision",
                    ]
                ),
            )

            relations = load_traceability(path)

            self.assertEqual(
                relations,
                [
                    {
                        "source": "D-001",
                        "destination": "CEVA-RHYAD-002-PF",
                        "relation": "decision",
                    }
                ],
            )

    def test_get_impacts_returns_empty_result_for_unknown_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            _write_traceability(
                root,
                "\n".join(
                    [
                        "traceability:",
                        "  - source: D-001",
                        "    destination: CEVA-RHYAD-002-PF",
                        "    relation: decision",
                    ]
                ),
            )

            result = get_impacts("D-999", root / "knowledge", root / "config" / "document_registry.yaml")

            self.assertEqual(result["source"], "D-999")
            self.assertEqual(result["impacted_documents"], [])
            self.assertEqual(result["impact_count"], 0)

    def test_get_impacts_returns_unique_impact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            _write_traceability(
                root,
                "\n".join(
                    [
                        "traceability:",
                        "  - source: D-001",
                        "    destination: CEVA-RHYAD-002-PF",
                        "    relation: decision",
                    ]
                ),
            )

            result = get_impacts("D-001", root / "knowledge", root / "config" / "document_registry.yaml")

            self.assertEqual(result["impacted_documents"], ["CEVA-RHYAD-002-PF"])
            self.assertEqual(result["impact_count"], 1)
            self.assertEqual(result["impacts"][0]["relation"], "decision")
            self.assertTrue(result["impacts"][0]["registered"])

    def test_get_impacts_returns_multiple_impacts_from_relations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root)
            _write_traceability(
                root,
                "\n".join(
                    [
                        "traceability:",
                        "  - source: H-002",
                        "    destination:",
                        "      - CEVA-RHYAD-002-PF",
                        "      - CEVA-RHYAD-100-F01",
                        "    relation: hypothesis",
                        "  - source: H-002",
                        "    destination: CEVA-RHYAD-300-DB01",
                        "    relation: design-basis",
                    ]
                ),
            )

            result = get_impacts("h-002", root / "knowledge", root / "config" / "document_registry.yaml")

            self.assertEqual(
                result["impacted_documents"],
                ["CEVA-RHYAD-002-PF", "CEVA-RHYAD-100-F01", "CEVA-RHYAD-300-DB01"],
            )
            self.assertEqual(result["impact_count"], 3)
            self.assertEqual([impact["relation"] for impact in result["impacts"]], ["hypothesis", "hypothesis", "design-basis"])
            self.assertFalse(result["impacts"][2]["registered"])


if __name__ == "__main__":
    unittest.main()
