from pathlib import Path

from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from engine.styles.colors import CEVA_BLUE, CEVA_AQUA, CEVA_SLATE

def hex_to_rgb(hex_color):
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )

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


def add_title(document, ref, title, subtitle, logo_path=None):
    add_optional_logo(document, logo_path)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(ref)
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = hex_to_rgb(CEVA_BLUE)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = hex_to_rgb(CEVA_SLATE)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(subtitle)
    r.italic = True
    r.font.size = Pt(10)
    r.font.color.rgb = hex_to_rgb(CEVA_AQUA)

    document.add_paragraph("")
