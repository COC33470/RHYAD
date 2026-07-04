import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.core.document_builder import build_document
from engine.core.knowledge_core import load_knowledge_core
from engine.utils.pdf import convert_docx_to_pdf

CONFIG_DIR = ROOT / "config" / "documents"
PROJECT_CONFIG = ROOT / "config" / "project.yaml"
REPOSITORY_CONFIG = ROOT / "config" / "rhyad_repository.yaml"
DOCUMENT_REGISTRY_CONFIG = ROOT / "config" / "document_registry.yaml"
KNOWLEDGE_DIR = ROOT / "knowledge"


def _require_mapping(data, label):
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping.")


def _require_string(data, key, label):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string.")
    return value


def validate_project_config(data, path: Path):
    label = str(path)
    _require_mapping(data, label)

    project = data.get("project")
    _require_mapping(project, f"{label}.project")
    _require_string(project, "code", f"{label}.project")
    _require_string(project, "name", f"{label}.project")

    document = data.get("document")
    _require_mapping(document, f"{label}.document")
    _require_string(document, "revision", f"{label}.document")
    _require_string(document, "status", f"{label}.document")

    output = data.get("output")
    _require_mapping(output, f"{label}.output")
    _require_string(output, "docx", f"{label}.output")
    _require_string(output, "pdf", f"{label}.output")

    branding = data.get("branding", {})
    if branding is not None:
        _require_mapping(branding, f"{label}.branding")


def load_project_config(path: Path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    validate_project_config(data, path)
    return data


def load_repository_config(path: Path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _require_mapping(data, str(path))
    repository = data.get("repository")
    _require_mapping(repository, f"{path}.repository")
    families = repository.get("families")
    if not isinstance(families, list) or not families:
        raise ValueError(f"{path}.repository.families must be a non-empty list.")

    return data


def load_document_registry_config(path: Path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _require_mapping(data, str(path))
    documents = data.get("documents")
    if not isinstance(documents, list):
        raise ValueError(f"{path}.documents must be a list.")

    for index, document in enumerate(documents, start=1):
        label = f"{path}.documents[{index}]"
        _require_mapping(document, label)
        _require_string(document, "code", label)
        _require_string(document, "official_code", label)
        _require_string(document, "revision", label)
        _require_string(document, "family", label)
        _require_string(document, "source", label)

    return data


def find_registry_document(registry_config, code):
    code = code.upper()
    for document in (registry_config or {}).get("documents", []):
        if str(document.get("code", "")).upper() == code:
            return document
    return None


def find_repository_document(repository_config, code):
    repository = (repository_config or {}).get("repository") or {}
    for family in repository.get("families", []):
        family_code = str(family.get("code", "")).upper()
        for document in family.get("documents", []):
            document_code = str(document.get("code", "")).upper()
            if document_code == code:
                return {
                    "family_code": family_code,
                    "family_title": family.get("title", ""),
                    "document": document,
                }
    return None


def resolve_document_yaml_path(code, registry_entry=None):
    if registry_entry:
        source = Path(registry_entry["source"])
        return source if source.is_absolute() else ROOT / source

    direct_path = CONFIG_DIR / f"{code}.yaml"
    if direct_path.exists():
        return direct_path

    function_path = CONFIG_DIR / "functions" / f"{code}.yaml"
    if function_path.exists():
        return function_path

    return direct_path


def resolve_output_dir(project_config, key, fallback):
    value = (project_config.get("output") or {}).get(key, fallback)
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def resolve_family_output_dir(project_config, key, fallback, repository_entry):
    output_dir = resolve_output_dir(project_config, key, fallback)
    if repository_entry:
        family_code = repository_entry.get("family_code") or repository_entry.get("family")
        if family_code:
            output_dir = output_dir / family_code
    return output_dir


def resolve_output_stem(project_code, code, registry_entry=None):
    if registry_entry:
        return f"{registry_entry['official_code']}_{registry_entry['revision']}"
    return f"{project_code}-{code}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/main.py 002")
        return 1

    try:
        project_config = load_project_config(PROJECT_CONFIG)
        repository_config = load_repository_config(REPOSITORY_CONFIG)
        registry_config = load_document_registry_config(DOCUMENT_REGISTRY_CONFIG)
        load_knowledge_core(KNOWLEDGE_DIR)
    except ValueError as exc:
        print("Configuration invalid.")
        print(exc)
        return 1

    code = sys.argv[1].upper()
    registry_entry = find_registry_document(registry_config, code)
    yaml_path = resolve_document_yaml_path(code, registry_entry)

    if not yaml_path.exists():
        print(f"Document configuration not found: {yaml_path}")
        return 1

    repository_entry = find_repository_document(repository_config, code)
    project_code = (project_config.get("project") or {}).get("code", "RHYAD")
    routing_entry = registry_entry or repository_entry
    output_docx = resolve_family_output_dir(project_config, "docx", "output/docx", routing_entry)
    output_pdf = resolve_family_output_dir(project_config, "pdf", "output/pdf", routing_entry)
    output_stem = resolve_output_stem(project_code, code, registry_entry)
    docx_path = output_docx / f"{output_stem}.docx"

    try:
        build_document(yaml_path, docx_path, project_config=project_config, project_root=ROOT)
    except (OSError, ValueError) as exc:
        print("DOCX generation failed.")
        print(exc)
        return 1

    print(f"DOCX generated: {docx_path}")

    try:
        pdf_path = convert_docx_to_pdf(docx_path, output_pdf)
        print(f"PDF generated: {pdf_path}")
    except Exception as exc:
        print("PDF export skipped or failed.")
        print(exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
