import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.core.document_builder import build_document
from engine.utils.pdf import convert_docx_to_pdf

CONFIG_DIR = ROOT / "config" / "documents"
PROJECT_CONFIG = ROOT / "config" / "project.yaml"


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


def resolve_output_dir(project_config, key, fallback):
    value = (project_config.get("output") or {}).get(key, fallback)
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/main.py F01")
        return 1

    code = sys.argv[1].upper()
    yaml_path = CONFIG_DIR / f"{code}.yaml"

    if not yaml_path.exists():
        print(f"Document configuration not found: {yaml_path}")
        return 1

    try:
        project_config = load_project_config(PROJECT_CONFIG)
    except ValueError as exc:
        print("Project configuration invalid.")
        print(exc)
        return 1

    project_code = (project_config.get("project") or {}).get("code", "RHYAD")
    output_docx = resolve_output_dir(project_config, "docx", "output/docx")
    output_pdf = resolve_output_dir(project_config, "pdf", "output/pdf")
    docx_path = output_docx / f"{project_code}-{code}.docx"

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
