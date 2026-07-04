from pathlib import Path
import yaml
from docx import Document

from engine.styles.ceva_style import setup_document, add_title


def _require_mapping(data, label):
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping.")


def _require_string(data, key, label):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string.")
    return value


def validate_document_config(data, yaml_path: Path):
    label = str(yaml_path)
    _require_mapping(data, label)

    _require_string(data, "reference", label)
    _require_string(data, "title", label)

    subtitle = data.get("subtitle")
    if subtitle is not None and not isinstance(subtitle, str):
        raise ValueError(f"{label}.subtitle must be a string when provided.")

    chapters = data.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError(f"{label}.chapters must be a non-empty list.")

    for index, chapter in enumerate(chapters, start=1):
        chapter_label = f"{label}.chapters[{index}]"
        _require_mapping(chapter, chapter_label)
        _require_string(chapter, "title", chapter_label)

        text = chapter.get("text")
        if text is not None and not isinstance(text, str):
            raise ValueError(f"{chapter_label}.text must be a string when provided.")

        bullets = chapter.get("bullets")
        if bullets is not None:
            if not isinstance(bullets, list):
                raise ValueError(f"{chapter_label}.bullets must be a list when provided.")
            for item_index, item in enumerate(bullets, start=1):
                if not isinstance(item, str) or not item.strip():
                    raise ValueError(
                        f"{chapter_label}.bullets[{item_index}] must be a non-empty string."
                    )


def _resolve_optional_path(path_value, project_root):
    if not path_value:
        return None

    path = Path(path_value)
    if not path.is_absolute() and project_root is not None:
        path = Path(project_root) / path

    return path if path.exists() else None


def _project_rows(project_config):
    if not project_config:
        return []

    project = project_config.get("project") or {}
    document = project_config.get("document") or {}
    authors = project_config.get("authors") or {}

    rows = [
        ("Projet", project.get("name")),
        ("Client", project.get("client")),
        ("Localisation", project.get("location")),
        ("Révision", document.get("revision")),
        ("Statut", document.get("status")),
        ("Confidentialité", document.get("confidentiality")),
        ("Auteur", authors.get("author")),
        ("Société", authors.get("company")),
    ]
    return [(label, value) for label, value in rows if value]


def _add_project_metadata(document, project_config):
    rows = _project_rows(project_config)
    if not rows:
        return

    table = document.add_table(rows=0, cols=2)
    table.style = "Table Grid"

    for label, value in rows:
        row = table.add_row().cells
        row[0].text = label
        row[1].text = str(value)

    document.add_paragraph("")


def build_document(yaml_path: Path, output_path: Path, project_config=None, project_root=None):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    validate_document_config(data, yaml_path)

    doc = Document()
    setup_document(doc)

    branding = (project_config or {}).get("branding", {})
    logo_path = _resolve_optional_path(branding.get("logo_ceva"), project_root)

    add_title(
        doc,
        data["reference"],
        data["title"],
        data.get("subtitle", ""),
        logo_path=logo_path,
    )
    _add_project_metadata(doc, project_config or {})

    for chapter in data["chapters"]:
        doc.add_heading(chapter["title"], level=1)

        if "text" in chapter:
            doc.add_paragraph(chapter["text"])

        if "bullets" in chapter:
            for item in chapter["bullets"]:
                doc.add_paragraph(item, style="List Bullet")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
