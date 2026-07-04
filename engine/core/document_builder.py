from pathlib import Path
import yaml
from docx import Document

from engine.styles.ceva_style import setup_document, add_title


def build_document(yaml_path: Path, output_path: Path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    doc = Document()
    setup_document(doc)

    add_title(
        doc,
        data["reference"],
        data["title"],
        data.get("subtitle", "")
    )

    for chapter in data["chapters"]:
        doc.add_heading(chapter["title"], level=1)

        if "text" in chapter:
            doc.add_paragraph(chapter["text"])

        if "bullets" in chapter:
            for item in chapter["bullets"]:
                doc.add_paragraph(item, style="List Bullet")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
