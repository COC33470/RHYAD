from pathlib import Path
from shutil import which
import subprocess
from html import escape

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import TableStyle


class PDFConversionError(RuntimeError):
    pass


def _format_process_output(result):
    parts = []
    if result.stdout:
        parts.append(f"stdout: {result.stdout.strip()}")
    if result.stderr:
        parts.append(f"stderr: {result.stderr.strip()}")
    return "\n".join(parts)


def _docx_body_blocks(document):
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield DocxParagraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield DocxTable(child, document)


def _paragraph_text(text):
    return escape(str(text or "")).replace("\n", "<br/>")


def _fallback_styles():
    styles = getSampleStyleSheet()
    return {
        "normal": ParagraphStyle(
            "RHYADFallbackNormal",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            spaceAfter=5,
        ),
        "heading1": ParagraphStyle(
            "RHYADFallbackHeading1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=7,
        ),
        "heading2": ParagraphStyle(
            "RHYADFallbackHeading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "table": ParagraphStyle(
            "RHYADFallbackTable",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=6,
            leading=7,
        ),
    }


def _paragraph_style(paragraph, styles):
    style_name = (paragraph.style.name or "").lower() if paragraph.style else ""
    if style_name.startswith("heading 1"):
        return styles["heading1"]
    if style_name.startswith("heading 2") or style_name.startswith("heading 3"):
        return styles["heading2"]
    return styles["normal"]


def _table_flowable(table, styles, available_width):
    rows = []
    max_columns = 0
    for row in table.rows:
        cells = []
        for cell in row.cells:
            cell_text = "\n".join(paragraph.text for paragraph in cell.paragraphs).strip()
            cells.append(Paragraph(_paragraph_text(cell_text), styles["table"]))
        max_columns = max(max_columns, len(cells))
        rows.append(cells)

    if not rows or not max_columns:
        return None

    for row in rows:
        while len(row) < max_columns:
            row.append(Paragraph("", styles["table"]))

    column_width = available_width / max_columns
    pdf_table = LongTable(rows, colWidths=[column_width] * max_columns, repeatRows=1)
    pdf_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9CA3AF")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return pdf_table


def _fallback_docx_to_pdf(docx_path: Path, pdf_path: Path):
    document = Document(docx_path)
    styles = _fallback_styles()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    available_width = A4[0] - doc.leftMargin - doc.rightMargin

    story = []
    for block in _docx_body_blocks(document):
        if isinstance(block, DocxParagraph):
            text = block.text.strip()
            if text:
                story.append(Paragraph(_paragraph_text(text), _paragraph_style(block, styles)))
        elif isinstance(block, DocxTable):
            table = _table_flowable(block, styles, available_width)
            if table is not None:
                story.append(table)
                story.append(Spacer(1, 6))

    if not story:
        story.append(Paragraph("", styles["normal"]))

    doc.build(story)
    if not pdf_path.exists():
        raise PDFConversionError(f"Fallback PDF was not created: {pdf_path}")
    return pdf_path


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
        pdf_path = pdf_dir / f"{docx_path.stem}.pdf"
        try:
            return _fallback_docx_to_pdf(docx_path, pdf_path)
        except Exception as fallback_error:
            raise PDFConversionError(f"{message}\nFallback PDF conversion failed: {fallback_error}") from fallback_error

    pdf_path = pdf_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        details = _format_process_output(result)
        message = f"LibreOffice completed but PDF was not created: {pdf_path}"
        if details:
            message = f"{message}\n{details}"
        raise PDFConversionError(message)

    return pdf_path
