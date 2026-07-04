from datetime import datetime, timezone
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCUMENTS_DIR = ROOT / "config" / "documents"
DEFAULT_INBOX_VALIDATED_DIR = ROOT / "inbox" / "validated"
DEFAULT_KNOWLEDGE_DIR = ROOT / "knowledge"
DEFAULT_REGISTRY_PATH = ROOT / "config" / "document_registry.yaml"
DEFAULT_SUGGESTIONS_PATH = ROOT / "knowledge" / "traceability_suggestions.yaml"

REFERENCE_PATTERN = re.compile(
    r"\b(?:CEVA-RHYAD-[A-Z0-9]+(?:-[A-Z0-9]+)*|RHYAD-\d{3}[A-Z]?|RHYAD-F(?:0[1-9]|1[0-5])|DB-\d{3}|DT-\d{3}|REG-\d{3}|F(?:0[1-9]|1[0-5]))\b"
)


class TraceabilitySuggestionError(ValueError):
    pass


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _dump_yaml(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def _as_mapping(data, label):
    if not isinstance(data, dict):
        raise TraceabilitySuggestionError(f"{label} must be a YAML mapping.")
    return data


def load_document_registry(path=DEFAULT_REGISTRY_PATH):
    path = Path(path)
    if not path.exists():
        return []

    data = _as_mapping(_load_yaml(path), str(path))
    documents = data.get("documents", [])
    if not isinstance(documents, list):
        raise TraceabilitySuggestionError(f"{path}.documents must be a list.")
    return [document for document in documents if isinstance(document, dict)]


def build_reference_aliases(registry_documents):
    aliases = {}
    for document in registry_documents:
        code = str(document.get("code", "")).strip()
        official_code = str(document.get("official_code", "")).strip()
        if not code or not official_code:
            continue

        aliases[official_code.upper()] = official_code
        aliases[f"RHYAD-{code}".upper()] = official_code
        if code.upper().startswith(("F", "DB", "REG", "DT")):
            aliases[code.upper()] = official_code

    return aliases


def _iter_yaml_strings(value, location="$"):
    if isinstance(value, str):
        yield location, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_yaml_strings(item, f"{location}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_yaml_strings(item, f"{location}.{key}")


def _canonical_reference(value, aliases):
    return aliases.get(value.upper(), value)


def _source_aliases(source, path, aliases):
    source_values = {source.upper()}
    code = path.stem.upper()
    source_values.add(code)
    source_values.add(f"RHYAD-{code}")
    if code in aliases:
        source_values.add(aliases[code].upper())
    if f"RHYAD-{code}" in aliases:
        source_values.add(aliases[f"RHYAD-{code}"].upper())
    return source_values


def _make_suggestion(source, destination, matched_reference, evidence_file, location, evidence_text):
    try:
        source_file = str(Path(evidence_file).resolve().relative_to(ROOT))
    except ValueError:
        source_file = str(evidence_file)

    return {
        "source": source,
        "destination": destination,
        "relation": "explicit-reference",
        "status": "proposed",
        "evidence": {
            "source_file": source_file,
            "location": location,
            "matched_reference": matched_reference,
            "text": evidence_text,
        },
    }


def _scan_texts(source, text_entries, evidence_file, aliases, source_aliases):
    suggestions = []
    seen = set()

    for location, text in text_entries:
        for match in REFERENCE_PATTERN.finditer(text):
            matched_reference = match.group(0)
            destination = _canonical_reference(matched_reference, aliases)
            if destination.upper() in source_aliases or matched_reference.upper() in source_aliases:
                continue

            key = (source.upper(), destination.upper())
            if key in seen:
                continue
            seen.add(key)
            suggestions.append(
                _make_suggestion(
                    source,
                    destination,
                    matched_reference,
                    evidence_file,
                    location,
                    text,
                )
            )

    return suggestions


def _document_source_from_yaml(path, data, aliases):
    reference = data.get("reference")
    if isinstance(reference, str) and reference.strip():
        return _canonical_reference(reference.strip(), aliases)

    code = path.stem
    return aliases.get(code.upper()) or aliases.get(f"RHYAD-{code}".upper()) or code


def scan_document_yaml(path, aliases):
    data = _as_mapping(_load_yaml(path), str(path))
    source = _document_source_from_yaml(path, data, aliases)
    return _scan_texts(
        source,
        _iter_yaml_strings(data),
        path,
        aliases,
        _source_aliases(source, path, aliases),
    )


def _markdown_source(path, aliases):
    code = path.stem
    return aliases.get(code.upper()) or aliases.get(f"RHYAD-{code}".upper()) or code


def scan_markdown(path, aliases):
    if path.name.upper() == "README.MD":
        return []

    source = _markdown_source(path, aliases)
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = [(f"line {index}", line) for index, line in enumerate(lines, start=1)]
    return _scan_texts(
        source,
        entries,
        path,
        aliases,
        _source_aliases(source, path, aliases),
    )


def scan_knowledge_yaml(path, aliases):
    if path.name in {"traceability.yaml", "traceability_suggestions.yaml"}:
        return []

    data = _as_mapping(_load_yaml(path), str(path))
    source = f"knowledge:{path.stem}"
    return _scan_texts(source, _iter_yaml_strings(data), path, aliases, {source.upper()})


def suggest_traceability(
    documents_dir=DEFAULT_DOCUMENTS_DIR,
    inbox_validated_dir=DEFAULT_INBOX_VALIDATED_DIR,
    knowledge_dir=DEFAULT_KNOWLEDGE_DIR,
    registry_path=DEFAULT_REGISTRY_PATH,
    suggestions_path=DEFAULT_SUGGESTIONS_PATH,
):
    documents_dir = Path(documents_dir)
    inbox_validated_dir = Path(inbox_validated_dir)
    knowledge_dir = Path(knowledge_dir)
    suggestions_path = Path(suggestions_path)
    registry_documents = load_document_registry(registry_path)
    aliases = build_reference_aliases(registry_documents)

    suggestions = []
    document_paths = sorted(documents_dir.rglob("*.yaml")) if documents_dir.exists() else []
    markdown_paths = sorted(inbox_validated_dir.glob("*.md")) if inbox_validated_dir.exists() else []
    knowledge_paths = sorted(knowledge_dir.glob("*.yaml")) if knowledge_dir.exists() else []

    for path in document_paths:
        suggestions.extend(scan_document_yaml(path, aliases))

    for path in markdown_paths:
        suggestions.extend(scan_markdown(path, aliases))

    for path in knowledge_paths:
        suggestions.extend(scan_knowledge_yaml(path, aliases))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "proposed",
        "traceability_suggestions": suggestions,
    }
    _dump_yaml(payload, suggestions_path)
    return {
        "suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "suggestions_path": suggestions_path,
    }
