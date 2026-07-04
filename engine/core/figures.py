from pathlib import Path

import yaml


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
FUTURE_FIGURE_EXTENSIONS = {".svg", ".pdf", ".mmd", ".mermaid", ".drawio"}


def _require_mapping(data, label):
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping.")


def _require_string(data, key, label):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string.")
    return value


def load_figures_registry(path):
    path = Path(path)
    if not path.exists():
        return {"figures": []}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    _require_mapping(data, str(path))
    figures = data.get("figures", [])
    if not isinstance(figures, list):
        raise ValueError(f"{path}.figures must be a list.")

    for index, figure in enumerate(figures, start=1):
        label = f"{path}.figures[{index}]"
        _require_mapping(figure, label)
        for key in ("id", "title", "family", "file", "caption", "source", "status"):
            _require_string(figure, key, label)
        used_in = figure.get("used_in")
        if used_in is None:
            figure["used_in"] = []
        elif not isinstance(used_in, list):
            raise ValueError(f"{label}.used_in must be a list.")
        else:
            for used_index, document in enumerate(used_in, start=1):
                if not isinstance(document, str) or not document.strip():
                    raise ValueError(f"{label}.used_in[{used_index}] must be a non-empty string.")

    return data


def figure_index(registry):
    return {figure["id"]: figure for figure in registry.get("figures", [])}


def resolve_figure_path(root, figure):
    path = Path(figure["file"])
    if not path.is_absolute():
        path = Path(root) / path
    return path


def validate_figure_extension(path):
    return path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def check_figures(root, registry_path):
    registry = load_figures_registry(registry_path)
    existing = []
    missing = []
    unsupported = []
    unused = []

    for figure in registry.get("figures", []):
        figure_path = resolve_figure_path(root, figure)
        if not validate_figure_extension(figure_path):
            unsupported.append(figure)
        if figure_path.exists():
            existing.append(figure)
        else:
            missing.append(figure)
        if not figure.get("used_in"):
            unused.append(figure)

    return {
        "registry": registry,
        "declared": len(registry.get("figures", [])),
        "existing": existing,
        "missing": missing,
        "unsupported": unsupported,
        "unused": unused,
    }
