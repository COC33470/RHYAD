from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from engine.styles.colors import CEVA_BLUE, CEVA_AQUA, CEVA_SLATE


def hex_to_rgb(hex_color):
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def _set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = tc_pr.first_child_found_in("w:shd")
    if shading is None:
        shading = OxmlElement("w:shd")
        tc_pr.append(shading)
    shading.set(qn("w:fill"), fill)


def _set_cell_width(cell, width_twips):
    tc_pr = cell._tc.get_or_add_tcPr()
    width = tc_pr.first_child_found_in("w:tcW")
    if width is None:
        width = OxmlElement("w:tcW")
        tc_pr.append(width)
    width.set(qn("w:w"), str(width_twips))
    width.set(qn("w:type"), "dxa")


def _format_run(run, size=9, bold=False, italic=False, color=CEVA_SLATE):
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = hex_to_rgb(color)


def _add_text(paragraph, text, size=9, bold=False, italic=False, color=CEVA_SLATE):
    run = paragraph.add_run(str(text))
    _format_run(run, size=size, bold=bold, italic=italic, color=color)
    return run


def _add_field(paragraph, field_code):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")
    run._r.append(begin)

    run = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field_code
    run._r.append(instr)

    run = paragraph.add_run()
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    run._r.append(separate)

    run = paragraph.add_run()
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(end)


def _set_update_fields_on_open(document):
    settings = document.settings.element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


def setup_document(document):
    section = document.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)

    styles = document.styles

    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9)
    normal.font.color.rgb = hex_to_rgb(CEVA_SLATE)

    h1 = styles["Heading 1"]
    h1.font.name = "Arial"
    h1.font.size = Pt(18)
    h1.font.bold = True
    h1.font.color.rgb = hex_to_rgb(CEVA_BLUE)

    h2 = styles["Heading 2"]
    h2.font.name = "Arial"
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = hex_to_rgb(CEVA_BLUE)

    h3 = styles["Heading 3"]
    h3.font.name = "Arial"
    h3.font.size = Pt(11)
    h3.font.bold = True
    h3.font.color.rgb = hex_to_rgb(CEVA_AQUA)


def add_optional_logo(document, logo_path):
    if not logo_path:
        return False

    path = Path(logo_path)
    if not path.exists():
        return False

    try:
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(4.0))
        return True
    except Exception:
        return False


def add_optional_logo_to_paragraph(paragraph, logo_path, width=Cm(3.0)):
    if not logo_path:
        return False

    path = Path(logo_path)
    if not path.exists():
        return False

    try:
        paragraph.add_run().add_picture(str(path), width=width)
        return True
    except Exception:
        return False


def setup_document_shell(document, metadata, logo_path=None):
    setup_document(document)
    _set_update_fields_on_open(document)
    add_document_header(document, metadata, logo_path=logo_path)
    add_document_footer(document, metadata)


def add_document_header(document, metadata, logo_path=None):
    section = document.sections[0]
    section.header_distance = Cm(0.7)
    table = section.header.add_table(rows=1, cols=2, width=Cm(17.4))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    left, right = table.rows[0].cells
    _set_cell_width(left, 3600)
    _set_cell_width(right, 6260)
    left.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    right.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    logo_paragraph = left.paragraphs[0]
    logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if not add_optional_logo_to_paragraph(logo_paragraph, logo_path, width=Cm(2.8)):
        _add_text(logo_paragraph, "CEVA", size=16, bold=True, color=CEVA_BLUE)

    info = [
        ("Document", metadata.get("reference", "")),
        ("Title", metadata.get("title", "")),
        ("Revision", metadata.get("revision", "")),
        ("Status", metadata.get("status", "")),
    ]

    first_paragraph = right.paragraphs[0]
    first_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for index, (label, value) in enumerate(info):
        paragraph = first_paragraph if index == 0 else right.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _add_text(paragraph, f"{label}: ", size=8, bold=True, color=CEVA_BLUE)
        _add_text(paragraph, value, size=8)


def add_document_footer(document, metadata):
    section = document.sections[0]
    section.footer_distance = Cm(0.7)
    table = section.footer.add_table(rows=1, cols=3, width=Cm(17.4))
    table.style = "Table Grid"

    left, center, right = table.rows[0].cells
    for cell in (left, center, right):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    left_p = left.paragraphs[0]
    _add_text(left_p, metadata.get("confidentiality", ""), size=8, bold=True, color=CEVA_BLUE)

    center_p = center.paragraphs[0]
    center_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(center_p, "Page ", size=8)
    _add_field(center_p, "PAGE")
    _add_text(center_p, " / ", size=8)
    _add_field(center_p, "NUMPAGES")

    right_p = right.paragraphs[0]
    right_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _add_text(right_p, f"Generated: {metadata.get('generated_date', '')}", size=8)


def add_cover_page(document, metadata, logo_path=None):
    add_optional_logo(document, logo_path)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(p, metadata.get("project_name", ""), size=14, bold=True, color=CEVA_BLUE)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(p, metadata.get("client", ""), size=11)

    document.add_paragraph("")
    document.add_paragraph("")

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(p, metadata.get("reference", ""), size=24, bold=True, color=CEVA_BLUE)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(p, metadata.get("title", ""), size=18, bold=True)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(p, metadata.get("subtitle", ""), size=11, italic=True, color=CEVA_AQUA)

    document.add_paragraph("")

    table = document.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    cover_rows = [
        ("Revision", metadata.get("revision", "")),
        ("Status", metadata.get("status", "")),
        ("Confidentiality", metadata.get("confidentiality", "")),
        ("Generated", metadata.get("generated_date", "")),
    ]
    for label, value in cover_rows:
        row = table.add_row().cells
        _set_cell_shading(row[0], CEVA_BLUE)
        _add_text(row[0].paragraphs[0], label, size=9, bold=True, color="FFFFFF")
        _add_text(row[1].paragraphs[0], value, size=9)

    document.add_page_break()


def add_document_control_table(document, metadata):
    document.add_heading("Document Control", level=1)
    table = document.add_table(rows=1, cols=2)
    table.style = "Table Grid"

    header_cells = table.rows[0].cells
    _set_cell_shading(header_cells[0], CEVA_BLUE)
    _set_cell_shading(header_cells[1], CEVA_BLUE)
    _add_text(header_cells[0].paragraphs[0], "Field", size=9, bold=True, color="FFFFFF")
    _add_text(header_cells[1].paragraphs[0], "Value", size=9, bold=True, color="FFFFFF")

    rows = [
        ("Document Number", metadata.get("reference", "")),
        ("Revision", metadata.get("revision", "")),
        ("Status", metadata.get("status", "")),
        ("Author", metadata.get("author", "")),
        ("Checker", metadata.get("checker", "")),
        ("Approver", metadata.get("approver", "")),
    ]

    for label, value in rows:
        row = table.add_row().cells
        _add_text(row[0].paragraphs[0], label, size=9, bold=True, color=CEVA_BLUE)
        _add_text(row[1].paragraphs[0], value or "-", size=9)

    document.add_paragraph("")


def add_table_of_contents(document):
    document.add_heading("Table of Contents", level=1)
    paragraph = document.add_paragraph()
    _add_field(paragraph, 'TOC \\o "1-3" \\h \\z \\u')
    document.add_page_break()
