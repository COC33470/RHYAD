import unittest
from pathlib import Path

import yaml

from engine.core.knowledge_core import KNOWLEDGE_FILES, load_knowledge_core
from scripts.main import PROJECT_CONFIG, load_project_config


class KnowledgeCoreTest(unittest.TestCase):
    def test_knowledge_core_files_exist_and_are_yaml_mappings(self):
        knowledge_dir = Path("knowledge")

        for filename in KNOWLEDGE_FILES:
            path = knowledge_dir / filename

            self.assertTrue(path.exists(), f"Missing Knowledge Core file: {path}")
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self.assertIsInstance(data, dict)

    def test_load_knowledge_core_loads_required_sections(self):
        core = load_knowledge_core(Path("knowledge"))

        self.assertEqual(set(core), {Path(filename).stem for filename in KNOWLEDGE_FILES})
        self.assertIn("project", core["project"])
        self.assertIn("glossary", core["glossary"])
        self.assertIn("decisions", core["decisions"])
        self.assertIn("traceability", core["traceability"])

    def test_project_knowledge_uses_existing_project_config_values(self):
        project_config = load_project_config(PROJECT_CONFIG)
        core = load_knowledge_core(Path("knowledge"))
        project = project_config["project"]
        document = project_config["document"]
        knowledge_project = core["project"]

        self.assertEqual(knowledge_project["client"], project["client"])
        self.assertEqual(knowledge_project["project"]["code"], project["code"])
        self.assertEqual(knowledge_project["project"]["name"], project["name"])
        self.assertEqual(knowledge_project["location"], project["location"])
        self.assertEqual(knowledge_project["current_revision"], document["revision"])
        self.assertEqual(knowledge_project["status"], document["status"])
        self.assertEqual(knowledge_project["languages"], [document["language"]])
        self.assertEqual(
            knowledge_project["global_parameters"]["confidentiality"],
            document["confidentiality"],
        )


if __name__ == "__main__":
    unittest.main()
