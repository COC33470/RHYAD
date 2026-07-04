from pathlib import Path
from shutil import which
import subprocess


class PDFConversionError(RuntimeError):
    pass


def _format_process_output(result):
    parts = []
    if result.stdout:
        parts.append(f"stdout: {result.stdout.strip()}")
    if result.stderr:
        parts.append(f"stderr: {result.stderr.strip()}")
    return "\n".join(parts)


def convert_docx_to_pdf(docx_path: Path, pdf_dir: Path):
    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    soffice = which("soffice") or which("libreoffice")
    if not soffice:
        raise PDFConversionError(
            "LibreOffice executable not found. Install LibreOffice or add 'soffice' to PATH."
        )

    pdf_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        soffice,
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pdf_dir),
        str(docx_path),
    ]

    result = subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        details = _format_process_output(result)
        message = f"LibreOffice PDF conversion failed with exit code {result.returncode}."
        if details:
            message = f"{message}\n{details}"
        raise PDFConversionError(message)

    pdf_path = pdf_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        details = _format_process_output(result)
        message = f"LibreOffice completed but PDF was not created: {pdf_path}"
        if details:
            message = f"{message}\n{details}"
        raise PDFConversionError(message)

    return pdf_path
