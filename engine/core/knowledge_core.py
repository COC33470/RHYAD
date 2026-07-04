from pathlib import Path
import yaml


KNOWLEDGE_FILES = {
    "project.yaml": (
        "client",
        "project",
        "location",
        "current_revision",
        "status",
        "units",
        "languages",
        "global_parameters",
    ),
    "glossary.yaml": ("glossary",),
    "decisions.yaml": ("decisions",),
    "risks.yaml": ("risks",),
    "assumptions.yaml": ("assumptions",),
    "requirements.yaml": ("requirements",),
    "interfaces.yaml": ("interfaces",),
    "meetings.yaml": ("meetings",),
    "traceability.yaml": ("traceability",),
}


class KnowledgeCoreError(ValueError):
    pass


def _require_mapping(data, label):
    if not isinstance(data, dict):
        raise KnowledgeCoreError(f"{label} must be a YAML mapping.")


def _load_yaml_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    _require_mapping(data, str(path))
    return data


def validate_knowledge_file(data, filename):
    required_keys = KNOWLEDGE_FILES[filename]
    for key in required_keys:
        if key not in data:
            raise KnowledgeCoreError(f"{filename}.{key} is required.")

    stem = Path(filename).stem
    if stem != "project" and not isinstance(data.get(stem), list):
        raise KnowledgeCoreError(f"{filename}.{stem} must be a list.")


def load_knowledge_core(knowledge_dir: Path):
    knowledge_dir = Path(knowledge_dir)
    if not knowledge_dir.exists():
        return {}

    if not knowledge_dir.is_dir():
        raise KnowledgeCoreError(f"{knowledge_dir} must be a directory.")

    core = {}
    for filename in KNOWLEDGE_FILES:
        path = knowledge_dir / filename
        if not path.exists():
            raise KnowledgeCoreError(f"Knowledge Core file not found: {path}")

        data = _load_yaml_file(path)
        validate_knowledge_file(data, filename)
        core[path.stem] = data

    return core
