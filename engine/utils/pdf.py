from pathlib import Path
import subprocess


def convert_docx_to_pdf(docx_path: Path, pdf_dir: Path):
    pdf_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pdf_dir),
        str(docx_path),
    ]

    subprocess.run(cmd, check=True)