import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.core.document_builder import build_document
from engine.utils.pdf import convert_docx_to_pdf

CONFIG_DIR = ROOT / "config" / "documents"
OUTPUT_DOCX = ROOT / "output" / "docx"
OUTPUT_PDF = ROOT / "output" / "pdf"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/main.py F01")
        return

    code = sys.argv[1].upper()
    yaml_path = CONFIG_DIR / f"{code}.yaml"
    docx_path = OUTPUT_DOCX / f"RHYAD-{code}.docx"

    if not yaml_path.exists():
        print(f"Document configuration not found: {yaml_path}")
        return

    build_document(yaml_path, docx_path)
    print(f"DOCX generated: {docx_path}")

    try:
        convert_docx_to_pdf(docx_path, OUTPUT_PDF)
        print(f"PDF generated in: {OUTPUT_PDF}")
    except Exception as exc:
        print("PDF export skipped or failed.")
        print(exc)


if __name__ == "__main__":
    main()