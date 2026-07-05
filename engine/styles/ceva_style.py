from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from engine.styles.colors import CEVA_BLUE, CEVA_AQUA, CEVA_SLATE


TWIPS_PER_EMU = 635


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


def _content_width(section):
    return section.page_width - section.left_margin - section.right_margin


def _width_twips(width):
    return int(round(int(width) / TWIPS_PER_EMU))


def _set_table_width(table, width):
    tbl_pr = table._tbl.tblPr
    tbl_width = tbl_pr.first_child_found_in("w:tblW")
    if tbl_width is None:
        tbl_width = OxmlElement("w:tblW")
        tbl_pr.append(tbl_width)
    tbl_width.set(qn("w:w"), str(_width_twips(width)))
    tbl_width.set(qn("w:type"), "dxa")


def _set_table_borders(table, bottom_color=None, bottom_size=4):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)

    border_values = {
        "top": ("nil", "0", "auto"),
        "left": ("nil", "0", "auto"),
        "right": ("nil", "0", "auto"),
        "insideH": ("nil", "0", "auto"),
        "insideV": ("nil", "0", "auto"),
        "bottom": (
            "single" if bottom_color else "nil",
            str(bottom_size if bottom_color else 0),
            bottom_color or "auto",
        ),
    }
    for edge, (value, size, color) in border_values.items():
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), value)
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


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
    section.different_first_page_header_footer = True
    section.header_distance = Cm(0.7)
    width = _content_width(section)
    table = section.header.add_table(rows=1, cols=3, width=width)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _set_table_width(table, width)
    _set_table_borders(table, bottom_color=CEVA_BLUE, bottom_size=4)

    left, center, right = table.rows[0].cells
    width_twips = _width_twips(width)
    left_width = int(width_twips * 0.22)
    right_width = int(width_twips * 0.34)
    center_width = width_twips - left_width - right_width
    _set_cell_width(left, left_width)
    _set_cell_width(center, center_width)
    _set_cell_width(right, right_width)
    left.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    center.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    right.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    logo_paragraph = left.paragraphs[0]
    logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if not add_optional_logo_to_paragraph(logo_paragraph, logo_path, width=Cm(2.8)):
        _add_text(logo_paragraph, "CEVA", size=16, bold=True, color=CEVA_BLUE)

    title_paragraph = center.paragraphs[0]
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text(title_paragraph, metadata.get("title", ""), size=9, bold=True, color=CEVA_BLUE)

    info = [
        ("Reference", metadata.get("reference", "")),
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


def _add_footer_content(footer, section, metadata):
    width = _content_width(section)
    table = footer.add_table(rows=1, cols=3, width=width)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _set_table_width(table, width)

    left, center, right = table.rows[0].cells
    width_twips = _width_twips(width)
    _set_cell_width(left, int(width_twips * 0.33))
    _set_cell_width(center, int(width_twips * 0.34))
    _set_cell_width(right, width_twips - int(width_twips * 0.33) - int(width_twips * 0.34))
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


def add_document_footer(document, metadata):
    section = document.sections[0]
    section.footer_distance = Cm(0.7)
    _add_footer_content(section.footer, section, metadata)
    _add_footer_content(section.first_page_footer, section, metadata)


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


def add_data_table(document, table_data):
    title = table_data.get("title")
    headers = table_data["headers"]
    rows = table_data["rows"]

    if title:
        document.add_heading(title, level=2)

    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    width = _content_width(document.sections[0])
    width_twips = _width_twips(width)
    _set_table_width(table, width)
    column_widths = [width_twips // len(headers)] * len(headers)
    column_widths[-1] = width_twips - sum(column_widths[:-1])

    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        _set_cell_width(cell, column_widths[index])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _set_cell_shading(cell, CEVA_BLUE)
        _add_text(cell.paragraphs[0], header, size=8, bold=True, color="FFFFFF")

    for data_row in rows:
        row = table.add_row().cells
        for index, value in enumerate(data_row):
            _set_cell_width(row[index], column_widths[index])
            row[index].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            display_value = "-" if value is None or value == "" else value
            _add_text(row[index].paragraphs[0], display_value, size=8)

    document.add_paragraph("")


def add_table_of_contents(document):
    document.add_heading("Table of Contents", level=1)
    paragraph = document.add_paragraph()
    _add_field(paragraph, 'TOC \\o "1-3" \\h \\z \\u')
    document.add_page_break()
