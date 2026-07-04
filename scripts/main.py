import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.generators.generate_f01 import generate as generate_f01

OUTPUT_DOCX = ROOT / "output" / "docx"

def main():
    OUTPUT_DOCX.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) < 2:
        print("Usage: python3 scripts/main.py F01")
        return

    code = sys.argv[1].upper()

    if code == "F01":
        output = OUTPUT_DOCX / "RHYAD-F01_Gestion_des_Actions_A1.0.docx"
        generate_f01(output)
        print(f"Document generated: {output}")
    else:
        print(f"Unknown document code: {code}")

if __name__ == "__main__":
    main()
