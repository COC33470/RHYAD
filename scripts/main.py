import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.core.document_builder import build_document

CONFIG_DIR = ROOT / "config" / "documents"
OUTPUT_DOCX = ROOT / "output" / "docx"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/main.py F01")
        return

    code = sys.argv[1].upper()
    yaml_path = CONFIG_DIR / f"{code}.yaml"
    output_path = OUTPUT_DOCX / f"RHYAD-{code}.docx"

    if not yaml_path.exists():
        print(f"Document configuration not found: {yaml_path}")
        return

    build_document(yaml_path, output_path)
    print(f"Document generated: {output_path}")


if __name__ == "__main__":
    main()
