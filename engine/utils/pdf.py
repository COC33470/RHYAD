from datetime import date
from functools import partial
from html import escape
from pathlib import Path
from shutil import which
import re
import subprocess

import yaml
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import TableStyle

from engine.styles.colors import CEVA_AQUA, CEVA_BLUE, CEVA_SLATE, LIGHT_GREY


ROOT = Path(__file__).resolve().parents[2]
PROJECT_CONFIG = ROOT / "config" / "project.yaml"
DOCUMENT_REGISTRY_CONFIG = ROOT / "config" / "document_registry.yaml"


class PDFConversionError(RuntimeError):
    pass


def _format_process_output(result):
    parts = []
    if result.stdout:
        parts.append(f"stdout: {result.stdout.strip()}")
    if result.stderr:
        parts.append(f"stderr: {result.stderr.strip()}")
    return "\n".join(parts)


def _hex(value):
    return colors.HexColor(f"#{value}")


def _read_yaml(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_path(path_value):
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path if path.exists() else None


def _source_from_registry(docx_path):
    registry = _read_yaml(DOCUMENT_REGISTRY_CONFIG)
    stem = docx_path.stem
    for document in registry.get("documents", []):
        expected_stem = f"{document.get('official_code')}_{document.get('revision')}"
        if expected_stem != stem:
            continue
        source = Path(document["source"])
        if not source.is_absolute():
            source = ROOT / source
        if source.exists():
            return source
    return None


def _metadata(document_data, project_config):
    project = project_config.get("project") or {}
    document = project_config.get("document") or {}
    authors = project_config.get("authors") or {}
    approval = project_config.get("approval") or {}
    return {
        "reference": document_data.get("reference", ""),
        "title": document_data.get("title", ""),
        "subtitle": document_data.get("subtitle", ""),
        "project_name": project.get("name", ""),
        "client": project.get("client", ""),
        "location": project.get("location", ""),
        "revision": document_data.get("revision", document.get("revision", "")),
        "status": document_data.get("status", document.get("status", "")),
        "confidentiality": document.get("confidentiality", ""),
        "author": authors.get("author", ""),
        "checker": approval.get("checker", ""),
        "approver": approval.get("approver", ""),
        "generated_date": date.today().isoformat(),
    }


def _inline_markup(text):
    value = escape(str(text or ""))
    value = value.replace("---", "—")
    value = value.replace(" -- ", " – ")
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = value.replace("\n", "<br/>")
    return value


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover_project": ParagraphStyle(
            "RHYADCoverProject",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=_hex(CEVA_BLUE),
            spaceAfter=8,
        ),
        "cover_reference": ParagraphStyle(
            "RHYADCoverReference",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=_hex(CEVA_BLUE),
            spaceBefore=22,
            spaceAfter=8,
        ),
        "cover_title": ParagraphStyle(
            "RHYADCoverTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            textColor=_hex(CEVA_SLATE),
            spaceAfter=6,
        ),
        "cover_subtitle": ParagraphStyle(
            "RHYADCoverSubtitle",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=_hex(CEVA_AQUA),
            spaceAfter=20,
        ),
        "body": ParagraphStyle(
            "RHYADBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=_hex(CEVA_SLATE),
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "RHYADBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=_hex(CEVA_SLATE),
            leftIndent=16,
            bulletIndent=7,
            spaceAfter=3,
        ),
        "h1": ParagraphStyle(
            "RHYADHeading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=_hex(CEVA_BLUE),
            spaceBefore=10,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "RHYADHeading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=_hex(CEVA_BLUE),
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "toc_title": ParagraphStyle(
            "RHYADTOCTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=_hex(CEVA_BLUE),
            spaceAfter=10,
        ),
        "toc_level": ParagraphStyle(
            "RHYADTOCLevel",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            leftIndent=12,
            firstLineIndent=-12,
            textColor=_hex(CEVA_SLATE),
        ),
        "table": ParagraphStyle(
            "RHYADTable",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=6.6,
            leading=8.1,
            textColor=_hex(CEVA_SLATE),
        ),
        "table_header": ParagraphStyle(
            "RHYADTableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=6.8,
            leading=8.2,
            textColor=colors.white,
        ),
    }


class _RhyadDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, toc_entries=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.toc_entries = toc_entries

    def afterFlowable(self, flowable):
        level = getattr(flowable, "_rhyad_toc_level", None)
        if level is None:
            return
        bookmark = getattr(flowable, "_rhyad_bookmark", "")
        if bookmark:
            self.canv.bookmarkPage(bookmark)
        if self.toc_entries is not None:
            self.toc_entries.append((level, flowable.getPlainText(), self.page, bookmark))


class _NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, metadata=None, logo_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.metadata = metadata or {}
        self.logo_path = logo_path

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(page_count)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, page_count):
        page_width, page_height = A4
        left = 51
        right = page_width - 51
        blue = _hex(CEVA_BLUE)
        slate = _hex(CEVA_SLATE)

        if self._pageNumber > 1:
            header_y = page_height - 34
            if self.logo_path:
                try:
                    self.drawImage(
                        str(self.logo_path),
                        left,
                        header_y - 14,
                        width=72,
                        height=24,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                except Exception:
                    self._draw_ceva_text(left, header_y)
            else:
                self._draw_ceva_text(left, header_y)

            self.setFillColor(blue)
            self.setFont("Helvetica-Bold", 8)
            self.drawCentredString(page_width / 2, header_y, self.metadata.get("title", ""))

            self.setFont("Helvetica-Bold", 6.7)
            self.drawRightString(right, header_y + 8, f"Reference: {self.metadata.get('reference', '')}")
            self.drawRightString(right, header_y, f"Revision: {self.metadata.get('revision', '')}")
            self.drawRightString(right, header_y - 8, f"Status: {self.metadata.get('status', '')}")

            self.setStrokeColor(blue)
            self.setLineWidth(0.45)
            self.line(left, page_height - 55, right, page_height - 55)

        footer_y = 24
        self.setStrokeColor(colors.HexColor("#D7DAE0"))
        self.setLineWidth(0.25)
        self.line(left, footer_y + 13, right, footer_y + 13)
        self.setFillColor(slate)
        self.setFont("Helvetica", 7)
        self.drawString(left, footer_y, self.metadata.get("confidentiality", ""))
        self.drawCentredString(page_width / 2, footer_y, f"Page {self._pageNumber} / {page_count}")
        self.drawRightString(right, footer_y, f"Generated: {self.metadata.get('generated_date', '')}")

    def _draw_ceva_text(self, x, y):
        self.setFillColor(_hex(CEVA_BLUE))
        self.setFont("Helvetica-Bold", 14)
        self.drawString(x, y - 5, "CEVA")


def _heading(text, style, level=0, bookmark=None):
    paragraph = Paragraph(_inline_markup(text), style)
    if bookmark:
        paragraph._rhyad_toc_level = level
        paragraph._rhyad_bookmark = bookmark
    return paragraph


def _table(data, style_map, available_width, header=True, first_column_width=None):
    rows = []
    for row_index, row in enumerate(data):
        row_style = style_map["table_header"] if header and row_index == 0 else style_map["table"]
        rows.append([Paragraph(_inline_markup(value if value not in (None, "") else "-"), row_style) for value in row])

    if not rows:
        return None

    column_count = max(len(row) for row in rows)
    for row in rows:
        while len(row) < column_count:
            row.append(Paragraph("-", style_map["table"]))

    if first_column_width and column_count == 2:
        col_widths = [first_column_width, available_width - first_column_width]
    else:
        col_widths = [available_width / column_count] * column_count

    pdf_table = LongTable(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#AEB4C0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), _hex(CEVA_BLUE)))
    else:
        commands.append(("BACKGROUND", (0, 0), (0, -1), _hex(CEVA_BLUE)))
        commands.append(("TEXTCOLOR", (0, 0), (0, -1), colors.white))
    pdf_table.setStyle(TableStyle(commands))
    return pdf_table


def _cover_story(metadata, logo_path, style_map, available_width):
    story = []
    if logo_path:
        try:
            logo = Image(str(logo_path), width=115, height=45)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 20))
        except Exception:
            pass

    story.append(Paragraph(_inline_markup(metadata.get("project_name", "")), style_map["cover_project"]))
    story.append(Paragraph(_inline_markup(metadata.get("client", "")), style_map["cover_subtitle"]))
    story.append(Spacer(1, 26))
    story.append(Paragraph(_inline_markup(metadata.get("reference", "")), style_map["cover_reference"]))
    story.append(Paragraph(_inline_markup(metadata.get("title", "")), style_map["cover_title"]))
    if metadata.get("subtitle"):
        story.append(Paragraph(_inline_markup(metadata.get("subtitle", "")), style_map["cover_subtitle"]))
    story.append(Spacer(1, 20))

    cover_rows = [
        ("Revision", metadata.get("revision", "")),
        ("Status", metadata.get("status", "")),
        ("Confidentiality", metadata.get("confidentiality", "")),
        ("Generated", metadata.get("generated_date", "")),
    ]
    table = _table(cover_rows, style_map, available_width * 0.72, header=False, first_column_width=110)
    if table:
        table.hAlign = "CENTER"
        story.append(table)
    story.append(PageBreak())
    return story


def _document_control_story(metadata, style_map, available_width):
    rows = [
        ("Field", "Value"),
        ("Document Number", metadata.get("reference", "")),
        ("Revision", metadata.get("revision", "")),
        ("Status", metadata.get("status", "")),
        ("Author", metadata.get("author", "")),
        ("Checker", metadata.get("checker", "")),
        ("Approver", metadata.get("approver", "")),
    ]
    story = [_heading("Document Control", style_map["h1"]), _table(rows, style_map, available_width, header=True)]
    story.append(Spacer(1, 12))
    return story


def _toc_story(style_map, chapters, toc_entries, available_width):
    page_by_title = {}
    for _level, title, page, _bookmark in toc_entries or []:
        page_by_title.setdefault(title, page)

    rows = [["Section", "Page"]]
    for chapter in chapters:
        title = chapter["title"]
        page = page_by_title.get(title, "")
        rows.append([title, str(page) if page else ""])

    story = [_heading("Table of Contents", style_map["toc_title"])]
    table = _table(rows, style_map, available_width, header=True, first_column_width=available_width - 46)
    if table:
        story.append(table)
    story.append(PageBreak())
    return story


def _render_text_blocks(story, blocks, style_map, available_width, chapter_title):
    for block in blocks:
        block_type = block["type"]
        if block_type == "text":
            story.append(Paragraph(_inline_markup(block["text"]), style_map["body"]))
        elif block_type == "list":
            for item in block["items"]:
                story.append(Paragraph(_inline_markup(item), style_map["bullet"], bulletText="•"))
        elif block_type == "table":
            table_title = block.get("title")
            if table_title and table_title.strip() != chapter_title.strip():
                story.append(_heading(table_title, style_map["h2"]))
            table_rows = [block["headers"], *block["rows"]]
            table = _table(table_rows, style_map, available_width, header=True)
            if table:
                story.append(table)
                story.append(Spacer(1, 8))


def _render_legacy_chapter(story, chapter, style_map, available_width):
    if chapter.get("text"):
        story.append(Paragraph(_inline_markup(chapter["text"]), style_map["body"]))
    for item in chapter.get("bullets", []):
        story.append(Paragraph(_inline_markup(item), style_map["bullet"], bulletText="•"))
    for table_data in chapter.get("tables", []):
        table_title = table_data.get("title")
        if table_title and table_title.strip() != chapter["title"].strip():
            story.append(_heading(table_title, style_map["h2"]))
        table_rows = [table_data["headers"], *table_data["rows"]]
        table = _table(table_rows, style_map, available_width, header=True)
        if table:
            story.append(table)
            story.append(Spacer(1, 8))


def _yaml_story(document_data, metadata, logo_path, style_map, available_width, toc_entries=None):
    story = []
    story.extend(_cover_story(metadata, logo_path, style_map, available_width))
    story.extend(_document_control_story(metadata, style_map, available_width))
    story.extend(_toc_story(style_map, document_data.get("chapters", []), toc_entries, available_width))

    for index, chapter in enumerate(document_data.get("chapters", []), start=1):
        bookmark = f"chapter_{index}"
        story.append(_heading(chapter["title"], style_map["h1"], level=0, bookmark=bookmark))
        if chapter.get("blocks"):
            _render_text_blocks(story, chapter["blocks"], style_map, available_width, chapter["title"])
        else:
            _render_legacy_chapter(story, chapter, style_map, available_width)
    return story


def _new_doc_template(path, toc_entries=None):
    return _RhyadDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=51,
        rightMargin=51,
        topMargin=70,
        bottomMargin=48,
        toc_entries=toc_entries,
    )


def _fallback_yaml_to_pdf(yaml_path: Path, pdf_path: Path):
    document_data = _read_yaml(yaml_path)
    project_config = _read_yaml(PROJECT_CONFIG)
    metadata = _metadata(document_data, project_config)
    logo_path = _resolve_path((project_config.get("branding") or {}).get("logo_ceva"))
    style_map = _styles()

    draft_path = pdf_path.with_name(f"{pdf_path.stem}.toc-draft.pdf")
    toc_entries = []
    draft_doc = _new_doc_template(draft_path, toc_entries=toc_entries)
    available_width = A4[0] - draft_doc.leftMargin - draft_doc.rightMargin
    draft_doc.build(_yaml_story(document_data, metadata, logo_path, style_map, available_width))
    if draft_path.exists():
        draft_path.unlink()

    if pdf_path.exists():
        pdf_path.unlink()

    final_doc = _new_doc_template(pdf_path)
    canvasmaker = partial(_NumberedCanvas, metadata=metadata, logo_path=logo_path)
    final_doc.build(
        _yaml_story(document_data, metadata, logo_path, style_map, available_width, toc_entries=toc_entries),
        canvasmaker=canvasmaker,
    )
    if not pdf_path.exists():
        raise PDFConversionError(f"Fallback PDF was not created: {pdf_path}")
    return pdf_path


def _docx_body_blocks(document):
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield DocxParagraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield DocxTable(child, document)


def _paragraph_style(paragraph, style_map):
    style_name = (paragraph.style.name or "").lower() if paragraph.style else ""
    if style_name.startswith("heading 1"):
        return style_map["h1"]
    if style_name.startswith("heading 2") or style_name.startswith("heading 3"):
        return style_map["h2"]
    return style_map["body"]


def _fallback_docx_extract_to_pdf(docx_path: Path, pdf_path: Path):
    document = Document(docx_path)
    style_map = _styles()
    metadata = {"title": docx_path.stem, "generated_date": date.today().isoformat()}
    doc = _RhyadDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=51,
        rightMargin=51,
        topMargin=70,
        bottomMargin=48,
    )
    available_width = A4[0] - doc.leftMargin - doc.rightMargin

    story = []
    for block in _docx_body_blocks(document):
        if isinstance(block, DocxParagraph):
            text = block.text.strip()
            if text:
                story.append(Paragraph(_inline_markup(text), _paragraph_style(block, style_map)))
        elif isinstance(block, DocxTable):
            rows = []
            for row in block.rows:
                rows.append(["\n".join(paragraph.text for paragraph in cell.paragraphs).strip() for cell in row.cells])
            table = _table(rows, style_map, available_width, header=True)
            if table:
                story.append(table)
                story.append(Spacer(1, 8))

    if not story:
        story.append(Paragraph("", style_map["body"]))

    canvasmaker = partial(_NumberedCanvas, metadata=metadata, logo_path=None)
    doc.build(story, canvasmaker=canvasmaker)
    if not pdf_path.exists():
        raise PDFConversionError(f"Fallback PDF was not created: {pdf_path}")
    return pdf_path


def _fallback_docx_to_pdf(docx_path: Path, pdf_path: Path):
    yaml_path = _source_from_registry(docx_path)
    if yaml_path:
        return _fallback_yaml_to_pdf(yaml_path, pdf_path)
    return _fallback_docx_extract_to_pdf(docx_path, pdf_path)


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
