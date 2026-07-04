import argparse
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.core.document_builder import validate_document_config
from scripts.main import (
    DOCUMENT_REGISTRY_CONFIG,
    PROJECT_CONFIG,
    REPOSITORY_CONFIG,
    find_repository_document,
    find_registry_document,
    load_document_registry_config,
    load_project_config,
    load_repository_config,
    resolve_family_output_dir,
    resolve_document_yaml_path,
    resolve_output_stem,
)

INBOX_ROOT = ROOT / "inbox"
INBOX_VALIDATED_DIR = INBOX_ROOT / "validated"
INBOX_PROCESSED_DIR = INBOX_ROOT / "processed"
INBOX_REJECTED_DIR = INBOX_ROOT / "rejected"
INBOX_DIR = INBOX_VALIDATED_DIR
CONFIG_DIR = ROOT / "config" / "documents"
LOG_PATH = ROOT / "logs" / "import.log"

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


def normalize_document_code(value):
    code = str(value).strip().upper()

    db_match = re.fullmatch(r"DB[-_ ]?(\d{1,3})", code)
    if db_match:
        return f"DB-{int(db_match.group(1)):03d}"

    reg_match = re.fullmatch(r"REG[-_ ]?(\d{1,3})", code)
    if reg_match:
        return f"REG-{int(reg_match.group(1)):03d}"

    dt_match = re.fullmatch(r"DT[-_ ]?(\d{1,3})", code)
    if dt_match:
        return f"DT-{int(dt_match.group(1)):03d}"

    return code


def ensure_pipeline_directories():
    for path in (INBOX_VALIDATED_DIR, INBOX_PROCESSED_DIR, INBOX_REJECTED_DIR, LOG_PATH.parent):
        path.mkdir(parents=True, exist_ok=True)


def find_validated_markdown(document):
    raw_code = str(document).strip()
    code = normalize_document_code(raw_code)
    candidates = []
    for candidate in (raw_code, raw_code.upper(), code):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        path = INBOX_VALIDATED_DIR / f"{candidate}.md"
        if path.exists():
            return code, path

    expected = ", ".join(f"{candidate}.md" for candidate in candidates)
    raise ImportErrorWithContext(f"Validated Markdown not found in {INBOX_VALIDATED_DIR}: {expected}")


def _unique_destination(directory, source_path):
    destination = directory / source_path.name
    if not destination.exists():
        return destination

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return directory / f"{source_path.stem}_{timestamp}{source_path.suffix}"


def archive_markdown(source_path, destination_dir):
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(destination_dir, source_path)
    shutil.move(str(source_path), str(destination))
    return destination


def write_rejection_log(rejected_markdown_path, error):
    log_path = rejected_markdown_path.with_suffix(rejected_markdown_path.suffix + ".log")
    log_path.write_text(str(error).strip() + "\n", encoding="utf-8")
    return log_path


def append_import_log(document, duration_seconds, result, commit, details=""):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("date | document | duration | result | commit | details\n", encoding="utf-8")

    date_value = datetime.now(timezone.utc).isoformat()
    detail_text = str(details).replace("\n", " ").strip()
    line = (
        f"{date_value} | document={document} | duration={duration_seconds:.2f}s | "
        f"result={result} | commit={commit} | details={detail_text}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


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


def markdown_to_document(
    markdown_text,
    code,
    repository_title=None,
    default_reference=None,
    default_revision=None,
    default_status=None,
):
    metadata, body_lines = extract_metadata(markdown_text)
    code = code.upper()

    if not metadata.get("reference"):
        metadata["reference"] = default_reference or code

    if not metadata.get("revision") and default_revision:
        metadata["revision"] = default_revision

    if not metadata.get("status") and default_status:
        metadata["status"] = default_status

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


def expected_outputs(code, project_config, routing_entry, registry_entry=None):
    project_code = (project_config.get("project") or {}).get("code", "RHYAD")
    output_docx = resolve_family_output_dir(project_config, "docx", "output/docx", routing_entry)
    output_pdf = resolve_family_output_dir(project_config, "pdf", "output/pdf", routing_entry)
    output_stem = resolve_output_stem(project_code, code, registry_entry)
    return (
        output_docx / f"{output_stem}.docx",
        output_pdf / f"{output_stem}.pdf",
    )


def _prepare_document_import(code, markdown_path):
    repository_config = load_repository_config(REPOSITORY_CONFIG)
    registry_config = load_document_registry_config(DOCUMENT_REGISTRY_CONFIG)
    repository_entry = find_repository_document(repository_config, code)
    registry_entry = find_registry_document(registry_config, code)
    if not repository_entry and not registry_entry:
        raise ImportErrorWithContext(
            f"Document code is not declared in config/rhyad_repository.yaml or config/document_registry.yaml: {code}"
        )

    project_config = load_project_config(PROJECT_CONFIG)
    repository_title = repository_entry["document"].get("title") if repository_entry else None
    if repository_title is None and registry_entry:
        repository_title = registry_entry.get("title")
    markdown_text = markdown_path.read_text(encoding="utf-8")
    default_reference = registry_entry.get("official_code") if registry_entry else None
    default_revision = registry_entry.get("revision") if registry_entry else None
    default_status = registry_entry.get("status") if registry_entry else None
    document = markdown_to_document(
        markdown_text,
        code,
        repository_title=repository_title,
        default_reference=default_reference,
        default_revision=default_revision,
        default_status=default_status,
    )
    yaml_text = dump_document_yaml(document)

    yaml_path = resolve_document_yaml_path(code, registry_entry)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(yaml_text, encoding="utf-8")
    validate_document_config(document, yaml_path)

    routing_entry = registry_entry or repository_entry
    docx_path, pdf_path = expected_outputs(code, project_config, routing_entry, registry_entry)

    family = None
    if registry_entry:
        family = registry_entry.get("family")
    elif repository_entry:
        family = repository_entry.get("family_code")

    return {
        "document": document,
        "yaml_path": yaml_path,
        "yaml_text": yaml_text,
        "docx_path": docx_path,
        "pdf_path": pdf_path,
        "family": family,
        "registry_entry": registry_entry,
        "repository_entry": repository_entry,
    }


def _run_generation_checks(code, prepared, run_command):
    generation_output = run_command(["python3", "scripts/main.py", code])
    test_output = run_command(["python3", "-m", "unittest", "discover"])

    docx_path = prepared["docx_path"]
    pdf_path = prepared["pdf_path"]
    if not docx_path.exists():
        raise ImportErrorWithContext(f"DOCX was not created: {docx_path}")
    if not pdf_path.exists():
        raise ImportErrorWithContext(f"PDF was not created: {pdf_path}")

    return {
        **prepared,
        "generation_output": generation_output,
        "test_output": test_output,
    }


def import_validated_content(document, run_command=run_checked):
    ensure_pipeline_directories()
    start_time = time.monotonic()
    code = normalize_document_code(document)
    markdown_path = None
    archived = False

    try:
        code, markdown_path = find_validated_markdown(document)
        prepared = _prepare_document_import(code, markdown_path)
        result = _run_generation_checks(code, prepared, run_command)
        archive_path = archive_markdown(markdown_path, INBOX_PROCESSED_DIR)
        archived = True
        duration = time.monotonic() - start_time
        commit_message = f"Integrate validated {code}"
        append_import_log(code, duration, "success", commit_message)

        run_command(["git", "add", "."])
        commit_output = run_command(["git", "commit", "-m", commit_message])
        result["archive_path"] = archive_path
        result["duration_seconds"] = duration
        result["result"] = "success"
        result["commit_message"] = commit_message
        result["commit_output"] = commit_output
        return result
    except Exception as exc:
        duration = time.monotonic() - start_time
        rejected_path = None
        rejection_log_path = None

        if markdown_path and markdown_path.exists() and not archived:
            rejected_path = archive_markdown(markdown_path, INBOX_REJECTED_DIR)
            rejection_log_path = write_rejection_log(rejected_path, exc)

        append_import_log(code, duration, "rejected", "-", exc)

        if isinstance(exc, ImportErrorWithContext):
            exc.rejected_path = rejected_path
            exc.rejection_log_path = rejection_log_path
            raise

        wrapped = ImportErrorWithContext(str(exc))
        wrapped.rejected_path = rejected_path
        wrapped.rejection_log_path = rejection_log_path
        raise wrapped


def main():
    parser = argparse.ArgumentParser(description="Import validated Markdown content into RHYAD YAML.")
    parser.add_argument("code", help="Document code, for example 002, F01, DB-001 or REG-001.")
    args = parser.parse_args()

    try:
        result = import_validated_content(args.code)
    except ImportErrorWithContext as exc:
        print(exc)
        rejected_path = getattr(exc, "rejected_path", None)
        rejection_log_path = getattr(exc, "rejection_log_path", None)
        if rejected_path:
            print(f"Markdown rejeté: {rejected_path}")
        if rejection_log_path:
            print(f"Log rejet: {rejection_log_path}")
        return 1

    print(f"YAML généré: {result['yaml_path']}")
    print(result["yaml_text"])
    print(f"DOCX produit: {result['docx_path']}")
    print(f"PDF produit: {result['pdf_path']}")
    print(f"Famille documentaire: {result['family']}")
    print(f"Markdown archivé: {result['archive_path']}")
    print("Résultat génération:")
    print(result["generation_output"])
    print("Résultat tests:")
    print(result["test_output"])
    print("Commit demandé:")
    print(result["commit_message"])
    print("Sortie Git:")
    print(result["commit_output"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
