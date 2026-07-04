from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_DIR = ROOT / "knowledge"
DEFAULT_REGISTRY_PATH = ROOT / "config" / "document_registry.yaml"


class ImpactEngineError(ValueError):
    pass


def _require_mapping(data, label):
    if not isinstance(data, dict):
        raise ImpactEngineError(f"{label} must be a YAML mapping.")


def _load_yaml_mapping(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _require_mapping(data, str(path))
    return data


def load_traceability(path: Path):
    path = Path(path)
    data = _load_yaml_mapping(path)
    relations = data.get("traceability")

    if not isinstance(relations, list):
        raise ImpactEngineError(f"{path}.traceability must be a list.")

    parsed = []
    for index, relation in enumerate(relations, start=1):
        label = f"{path}.traceability[{index}]"
        _require_mapping(relation, label)

        source = relation.get("source")
        destination = relation.get("destination")
        relation_type = relation.get("relation")

        if not isinstance(source, str) or not source.strip():
            raise ImpactEngineError(f"{label}.source must be a non-empty string.")
        if not isinstance(relation_type, str) or not relation_type.strip():
            raise ImpactEngineError(f"{label}.relation must be a non-empty string.")

        destinations = destination if isinstance(destination, list) else [destination]
        for destination_value in destinations:
            if not isinstance(destination_value, str) or not destination_value.strip():
                raise ImpactEngineError(f"{label}.destination must contain non-empty strings.")
            parsed.append(
                {
                    "source": source.strip(),
                    "destination": destination_value.strip(),
                    "relation": relation_type.strip(),
                }
            )

    return parsed


def load_registry_official_codes(path: Path):
    path = Path(path)
    if not path.exists():
        return set()

    data = _load_yaml_mapping(path)
    documents = data.get("documents", [])
    if not isinstance(documents, list):
        raise ImpactEngineError(f"{path}.documents must be a list.")

    official_codes = set()
    for document in documents:
        if isinstance(document, dict) and isinstance(document.get("official_code"), str):
            official_codes.add(document["official_code"].strip().upper())

    return official_codes


def get_impacts(source, knowledge_dir: Path = None, registry_path: Path = None):
    knowledge_dir = DEFAULT_KNOWLEDGE_DIR if knowledge_dir is None else Path(knowledge_dir)
    registry_path = DEFAULT_REGISTRY_PATH if registry_path is None else Path(registry_path)
    source_value = str(source).strip()
    traceability_path = knowledge_dir / "traceability.yaml"
    relations = load_traceability(traceability_path)
    registered_documents = load_registry_official_codes(registry_path)

    matched = []
    impacted_documents = []
    seen_documents = set()
    source_key = source_value.upper()

    for relation in relations:
        if relation["source"].upper() != source_key:
            continue

        destination = relation["destination"]
        destination_key = destination.upper()
        matched.append(
            {
                "destination": destination,
                "relation": relation["relation"],
                "registered": destination_key in registered_documents,
            }
        )
        if destination_key not in seen_documents:
            impacted_documents.append(destination)
            seen_documents.add(destination_key)

    return {
        "source": source_value,
        "impacts": matched,
        "impacted_documents": impacted_documents,
        "impact_count": len(impacted_documents),
        "traceability_path": str(traceability_path),
    }
