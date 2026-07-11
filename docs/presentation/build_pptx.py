"""Generates docs/presentation/Municipal-Law-Skill.pptx from content.py.

Run: python docs/presentation/build_pptx.py
Requires: pip install python-pptx (already in requirements-dev.txt)
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

from content import SLIDES

# Color palette - matches docs/demo.html's dark theme for a consistent
# visual identity across every artifact this project ships.
BG = RGBColor(0x0B, 0x0D, 0x12)
PANEL = RGBColor(0x12, 0x15, 0x1C)
BORDER = RGBColor(0x26, 0x2B, 0x36)
TEXT = RGBColor(0xE8, 0xEA, 0xED)
MUTED = RGBColor(0x9A, 0xA4, 0xB2)
ACCENT = RGBColor(0x5B, 0x9D, 0xFF)
ACCENT_2 = RGBColor(0x7E, 0xE0, 0xC3)

FONT = "Segoe UI"
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

OUT_PATH = Path(__file__).parent / "Municipal-Law-Skill.pptx"


def _blank_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    return slide


def _textbox(slide, left, top, width, height, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    return box, tf


def _set_run(run, text, size, color, bold=False, italic=False, font=FONT):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font


def _footer(slide, index, total):
    box, tf = _textbox(slide, Inches(0.5), Inches(7.05), Inches(10.8), Inches(0.35))
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, "Municipal Law Skill for Autonomous Agents", 10, MUTED)

    box2, tf2 = _textbox(slide, Inches(11.8), Inches(7.05), Inches(1.0), Inches(0.35))
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run()
    _set_run(r2, f"{index}/{total}", 10, MUTED)


def _title_bar(slide, title, subtitle=None):
    box, tf = _textbox(slide, Inches(0.7), Inches(0.45), Inches(11.9), Inches(1.1))
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, title, 30, TEXT, bold=True)
    if subtitle:
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        _set_run(r2, subtitle, 14, MUTED, italic=True)
    # accent underline
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.35), Inches(2.2), Pt(3))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()


def render_title(slide, s):
    box, tf = _textbox(slide, Inches(1), Inches(2.3), Inches(11.3), Inches(1.2), MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    _set_run(r, s["title"], 48, TEXT, bold=True)

    box2, tf2 = _textbox(slide, Inches(1), Inches(3.35), Inches(11.3), Inches(0.8))
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    _set_run(r2, s["subtitle"], 26, ACCENT, bold=True)

    box3, tf3 = _textbox(slide, Inches(1.5), Inches(4.4), Inches(10.3), Inches(0.9))
    p3 = tf3.paragraphs[0]
    p3.alignment = PP_ALIGN.CENTER
    r3 = p3.add_run()
    _set_run(r3, s["tagline"], 16, MUTED, italic=True)

    box4, tf4 = _textbox(slide, Inches(1), Inches(6.3), Inches(11.3), Inches(0.5))
    p4 = tf4.paragraphs[0]
    p4.alignment = PP_ALIGN.CENTER
    r4 = p4.add_run()
    _set_run(r4, s["footer"], 13, MUTED)
    p5 = tf4.add_paragraph()
    p5.alignment = PP_ALIGN.CENTER
    r5 = p5.add_run()
    _set_run(r5, s["url"], 14, ACCENT_2, bold=True)


def render_bullets(slide, s, index, total):
    _title_bar(slide, s["title"])
    box, tf = _textbox(slide, Inches(1), Inches(1.9), Inches(11.3), Inches(4.6))
    for i, b in enumerate(s["bullets"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(18)
        r = p.add_run()
        _set_run(r, "▸  " + b, 20, TEXT)
    _footer(slide, index, total)


def render_quote(slide, s, index, total):
    _title_bar(slide, s["title"])
    # quote panel
    panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1.9), Inches(11.3), Inches(1.6))
    panel.fill.solid()
    panel.fill.fore_color.rgb = PANEL
    panel.line.color.rgb = ACCENT
    panel.line.width = Pt(1.5)
    tf = panel.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, "“" + s["quote"].strip("“”") + "”", 20, ACCENT_2, italic=True, bold=True)

    box, tf2 = _textbox(slide, Inches(1), Inches(3.9), Inches(11.3), Inches(2.6))
    for i, b in enumerate(s["bullets"]):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.space_after = Pt(14)
        r = p.add_run()
        _set_run(r, "▸  " + b, 18, TEXT)
    _footer(slide, index, total)


def render_diagram(slide, s, index, total):
    _title_bar(slide, s["title"])
    steps = s["diagram"]
    n = len(steps)
    box_w = Inches(11.3 / n * 0.82)
    gap = Inches(11.3 / n * 0.18)
    left = Inches(1)
    top = Inches(2.6)
    for i, step in enumerate(steps):
        shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, box_w, Inches(1.1))
        shp.fill.solid()
        shp.fill.fore_color.rgb = PANEL
        shp.line.color.rgb = ACCENT if i in (0, n - 1) else BORDER
        shp.line.width = Pt(1.25)
        tf = shp.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        _set_run(r, step, 12, TEXT, bold=(i in (0, n - 1)))
        if i < n - 1:
            arrow_left = Emu(left + box_w)
            arrow, atf = _textbox(slide, arrow_left, Inches(2.85), gap, Inches(0.6), MSO_ANCHOR.MIDDLE)
            ap = atf.paragraphs[0]
            ap.alignment = PP_ALIGN.CENTER
            ar = ap.add_run()
            _set_run(ar, "→", 22, ACCENT, bold=True)
        left = Emu(left + box_w + gap)

    box2, tf2 = _textbox(slide, Inches(1), Inches(4.3), Inches(11.3), Inches(1.2), MSO_ANCHOR.MIDDLE)
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    _set_run(r2, s["callout"], 18, ACCENT_2, italic=True, bold=True)
    _footer(slide, index, total)


def render_stats(slide, s, index, total):
    _title_bar(slide, s["title"])
    groups = s["stat_groups"]
    n = len(groups)
    col_w = Inches(11.3 / n - 0.3)
    left = Inches(1)
    for group in groups:
        panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, Inches(2.0), col_w, Inches(2.8))
        panel.fill.solid()
        panel.fill.fore_color.rgb = PANEL
        panel.line.color.rgb = BORDER
        tf = panel.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        _set_run(r, group["label"], 16, MUTED, bold=True)
        for num, label in group["stats"]:
            p2 = tf.add_paragraph()
            p2.alignment = PP_ALIGN.CENTER
            p2.space_before = Pt(10)
            r2 = p2.add_run()
            _set_run(r2, num, 34, ACCENT, bold=True)
            p3 = tf.add_paragraph()
            p3.alignment = PP_ALIGN.CENTER
            r3 = p3.add_run()
            _set_run(r3, label, 14, TEXT)
        left = Emu(left + col_w + Inches(0.3))

    box, tf2 = _textbox(slide, Inches(1), Inches(5.2), Inches(11.3), Inches(0.8), MSO_ANCHOR.MIDDLE)
    p = tf2.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    _set_run(r, s["footnote"], 16, ACCENT_2, italic=True)
    _footer(slide, index, total)


def render_api_table(slide, s, index, total):
    _title_bar(slide, s["title"], s.get("subtitle"))
    rows = s["rows"]
    top = Inches(2.0) if not s.get("subtitle") else Inches(2.2)
    row_h = Inches(4.7 / (len(rows) + 1))
    table_shape = slide.shapes.add_table(len(rows) + 1, 3, Inches(0.7), top, Inches(12.0), Inches(4.7))
    table = table_shape.table
    table.columns[0].width = Inches(1.0)
    table.columns[1].width = Inches(3.0)
    table.columns[2].width = Inches(8.0)

    headers = ["Method", "Endpoint", "Use case"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT
        tf = cell.text_frame
        tf.margin_top = Pt(4)
        tf.margin_bottom = Pt(4)
        p = tf.paragraphs[0]
        r = p.add_run()
        _set_run(r, h, 14, RGBColor(0x0B, 0x0D, 0x12), bold=True)

    for i, (method, endpoint, use_case) in enumerate(rows, start=1):
        for c, val in enumerate([method, endpoint, use_case]):
            cell = table.cell(i, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PANEL if i % 2 else BG
            tf = cell.text_frame
            tf.word_wrap = True
            tf.margin_top = Pt(6)
            tf.margin_bottom = Pt(6)
            p = tf.paragraphs[0]
            r = p.add_run()
            color = ACCENT_2 if c == 0 else (TEXT if c == 1 else MUTED)
            _set_run(r, val, 13 if c != 2 else 12.5, color, bold=(c in (0, 1)))
    _footer(slide, index, total)


def render_story(slide, s, index, total):
    _title_bar(slide, s["title"])
    box, tf = _textbox(slide, Inches(1), Inches(1.9), Inches(11.3), Inches(0.9))
    p = tf.paragraphs[0]
    r = p.add_run()
    _set_run(r, s["question"], 24, ACCENT_2, italic=True, bold=True)

    top = Inches(3.0)
    for i, step in enumerate(s["steps"]):
        panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), top, Inches(11.3), Inches(1.05))
        panel.fill.solid()
        panel.fill.fore_color.rgb = PANEL
        panel.line.color.rgb = ACCENT if i == len(s["steps"]) - 1 else BORDER
        tf2 = panel.text_frame
        tf2.word_wrap = True
        tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf2.margin_left = Inches(0.25)
        p2 = tf2.paragraphs[0]
        r2 = p2.add_run()
        _set_run(r2, f"{i + 1}.  {step}", 16, TEXT, bold=(i == len(s["steps"]) - 1))
        top = Emu(top + Inches(1.2))
    _footer(slide, index, total)


def render_closing(slide, s, index, total):
    box, tf = _textbox(slide, Inches(1), Inches(1.6), Inches(11.3), Inches(1.2), MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    _set_run(r, s["title"], 34, TEXT, bold=True)

    box2, tf2 = _textbox(slide, Inches(2), Inches(3.0), Inches(9.3), Inches(2.0))
    for i, b in enumerate(s["bullets"]):
        p2 = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        p2.space_after = Pt(10)
        r2 = p2.add_run()
        _set_run(r2, b, 18, ACCENT_2)

    box3, tf3 = _textbox(slide, Inches(1), Inches(5.4), Inches(11.3), Inches(1.0), MSO_ANCHOR.MIDDLE)
    p3 = tf3.paragraphs[0]
    p3.alignment = PP_ALIGN.CENTER
    r3 = p3.add_run()
    _set_run(r3, s["url"], 20, ACCENT, bold=True)
    p4 = tf3.add_paragraph()
    p4.alignment = PP_ALIGN.CENTER
    r4 = p4.add_run()
    _set_run(r4, s["repo"], 14, MUTED)
    _footer(slide, index, total)


RENDERERS = {
    "title": lambda slide, s, i, n: render_title(slide, s),
    "bullets": render_bullets,
    "quote": render_quote,
    "diagram": render_diagram,
    "stats": render_stats,
    "api_table": render_api_table,
    "story": render_story,
    "closing": render_closing,
}


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    total = len(SLIDES)
    for i, s in enumerate(SLIDES, start=1):
        slide = _blank_slide(prs)
        RENDERERS[s["kind"]](slide, s, i, total)

    prs.save(OUT_PATH)
    print(f"wrote {OUT_PATH} ({total} slides)")


if __name__ == "__main__":
    build()
