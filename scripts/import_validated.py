import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.core.document_builder import validate_document_config
from scripts.main import (
    PROJECT_CONFIG,
    REPOSITORY_CONFIG,
    find_repository_document,
    load_project_config,
    load_repository_config,
    resolve_family_output_dir,
)

INBOX_DIR = ROOT / "inbox" / "validated"
CONFIG_DIR = ROOT / "config" / "documents"

METADATA_KEYS = {
    "reference": "reference",
    "référence": "reference",
    "ref": "reference",
    "title": "title",
    "titre": "title",
    "subtitle": "subtitle",
    "sous-titre": "subtitle",
    "sous titre": "subtitle",
    "revision": "revision",
    "révision": "revision",
    "status": "status",
    "statut": "status",
}


class ImportErrorWithContext(RuntimeError):
    pass


def _clean_value(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_metadata_line(line):
    match = re.match(r"^([A-Za-zÀ-ÿ _-]+)\s*:\s*(.+)$", line)
    if not match:
        return None

    key = METADATA_KEYS.get(match.group(1).strip().lower())
    if not key:
        return None

    return key, _clean_value(match.group(2))


def extract_metadata(markdown_text):
    lines = markdown_text.splitlines()
    metadata = {}

    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                raw_metadata = "\n".join(lines[1:index])
                data = yaml.safe_load(raw_metadata) or {}
                if not isinstance(data, dict):
                    raise ImportErrorWithContext("Markdown front matter must be a mapping.")
                for key, value in data.items():
                    canonical = METADATA_KEYS.get(str(key).strip().lower())
                    if canonical and value is not None:
                        metadata[canonical] = str(value)
                return metadata, lines[index + 1 :]

    body_start = 0
    for index, line in enumerate(lines):
        if not line.strip():
            body_start = index + 1
            continue

        parsed = _parse_metadata_line(line)
        if not parsed:
            body_start = index
            break

        key, value = parsed
        metadata[key] = value
        body_start = index + 1

    return metadata, lines[body_start:]


def _split_markdown_table_row(line):
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def _is_table_separator(line):
    if "|" not in line:
        return False
    cells = _split_markdown_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _is_table_start(lines, index):
    return (
        index + 1 < len(lines)
        and "|" in lines[index]
        and _is_table_separator(lines[index + 1])
    )


def _list_item(line):
    match = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.+)$", line)
    return match.group(1).strip() if match else None


def _heading(line):
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    return match.group(2).strip() if match else None


def _flush_text(chapter, pending_text):
    if not chapter or not pending_text:
        pending_text.clear()
        return

    while pending_text and pending_text[0] == "":
        pending_text.pop(0)
    while pending_text and pending_text[-1] == "":
        pending_text.pop()

    if not pending_text:
        return

    text = "\n".join(pending_text).strip()
    if text:
        if chapter.get("text"):
            chapter["text"] = f"{chapter['text']}\n\n{text}"
        else:
            chapter["text"] = text
    pending_text.clear()


def _parse_table(lines, index):
    headers = _split_markdown_table_row(lines[index])
    rows = []
    index += 2

    while index < len(lines):
        line = lines[index]
        if not line.strip() or _heading(line) or "|" not in line:
            break
        row = _split_markdown_table_row(line)
        if len(row) != len(headers):
            raise ImportErrorWithContext(
                f"Markdown table row has {len(row)} cells, expected {len(headers)}: {line}"
            )
        rows.append(row)
        index += 1

    if not rows:
        raise ImportErrorWithContext("Markdown table must contain at least one data row.")

    return {"headers": headers, "rows": rows}, index


def parse_markdown_body(lines):
    chapters = []
    current = None
    pending_text = []
    index = 0

    while index < len(lines):
        line = lines[index]
        heading = _heading(line)
        if heading:
            _flush_text(current, pending_text)
            current = {"title": heading}
            chapters.append(current)
            index += 1
            continue

        if current is None and line.strip():
            current = {"title": "Contenu"}
            chapters.append(current)

        if current is not None and _is_table_start(lines, index):
            _flush_text(current, pending_text)
            table, index = _parse_table(lines, index)
            table["title"] = current["title"]
            current.setdefault("tables", []).append(table)
            continue

        item = _list_item(line)
        if current is not None and item:
            _flush_text(current, pending_text)
            current.setdefault("bullets", []).append(item)
            index += 1
            continue

        if current is not None:
            pending_text.append("" if not line.strip() else line.strip())

        index += 1

    _flush_text(current, pending_text)
    return chapters


def markdown_to_document(markdown_text, code, repository_title=None):
    metadata, body_lines = extract_metadata(markdown_text)
    code = code.upper()

    if not metadata.get("reference"):
        metadata["reference"] = code

    if not metadata.get("title"):
        for index, line in enumerate(body_lines):
            heading = _heading(line)
            if heading:
                metadata["title"] = heading
                del body_lines[index]
                break

    if not metadata.get("title") and repository_title:
        metadata["title"] = repository_title

    if not metadata.get("title"):
        raise ImportErrorWithContext(
            "Document title not found. Add 'title: ...' metadata or a top-level Markdown heading."
        )

    document = {
        "reference": metadata["reference"],
        "title": metadata["title"],
    }

    for key in ("subtitle", "revision", "status"):
        if metadata.get(key):
            document[key] = metadata[key]

    chapters = parse_markdown_body(body_lines)
    if not chapters:
        raise ImportErrorWithContext("No Markdown chapter found. Add headings with '#', '##' or '###'.")

    document["chapters"] = chapters
    return document


def dump_document_yaml(document):
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=120)


def run_checked(command):
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ImportErrorWithContext(
            f"Command failed ({' '.join(command)}):\n{result.stdout.strip()}"
        )
    return result.stdout.strip()


def expected_outputs(code, project_config, repository_entry):
    project_code = (project_config.get("project") or {}).get("code", "RHYAD")
    output_docx = resolve_family_output_dir(project_config, "docx", "output/docx", repository_entry)
    output_pdf = resolve_family_output_dir(project_config, "pdf", "output/pdf", repository_entry)
    return (
        output_docx / f"{project_code}-{code}.docx",
        output_pdf / f"{project_code}-{code}.pdf",
    )


def import_validated_content(code):
    code = code.upper()
    markdown_path = INBOX_DIR / f"{code}.md"
    if not markdown_path.exists():
        raise ImportErrorWithContext(f"Validated Markdown not found: {markdown_path}")

    repository_config = load_repository_config(REPOSITORY_CONFIG)
    repository_entry = find_repository_document(repository_config, code)
    if not repository_entry:
        raise ImportErrorWithContext(f"Document code is not declared in config/rhyad_repository.yaml: {code}")

    project_config = load_project_config(PROJECT_CONFIG)
    repository_title = repository_entry["document"].get("title")
    markdown_text = markdown_path.read_text(encoding="utf-8")
    document = markdown_to_document(markdown_text, code, repository_title=repository_title)
    yaml_text = dump_document_yaml(document)

    yaml_path = CONFIG_DIR / f"{code}.yaml"
    yaml_path.write_text(yaml_text, encoding="utf-8")
    validate_document_config(document, yaml_path)

    generation_output = run_checked(["python3", "scripts/main.py", code])
    test_output = run_checked(["python3", "-m", "unittest", "discover"])

    docx_path, pdf_path = expected_outputs(code, project_config, repository_entry)
    if not docx_path.exists():
        raise ImportErrorWithContext(f"DOCX was not created: {docx_path}")
    if not pdf_path.exists():
        raise ImportErrorWithContext(f"PDF was not created: {pdf_path}")

    run_checked(["git", "add", "."])
    commit_output = run_checked(["git", "commit", "-m", f"Integrate validated {code} content"])

    return {
        "yaml_path": yaml_path,
        "yaml_text": yaml_text,
        "docx_path": docx_path,
        "pdf_path": pdf_path,
        "generation_output": generation_output,
        "test_output": test_output,
        "commit_output": commit_output,
    }


def main():
    parser = argparse.ArgumentParser(description="Import validated Markdown content into RHYAD YAML.")
    parser.add_argument("code", help="Document code, for example 002, F01, DB-001 or REG-001.")
    args = parser.parse_args()

    try:
        result = import_validated_content(args.code)
    except ImportErrorWithContext as exc:
        print(exc)
        return 1

    print(f"YAML généré: {result['yaml_path']}")
    print(result["yaml_text"])
    print(f"DOCX produit: {result['docx_path']}")
    print(f"PDF produit: {result['pdf_path']}")
    print("Résultat génération:")
    print(result["generation_output"])
    print("Résultat tests:")
    print(result["test_output"])
    print("Commit créé:")
    print(result["commit_output"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
