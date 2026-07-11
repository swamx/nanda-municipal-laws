"""Generates docs/presentation/deck.html from content.py - a browser-based
slide deck styled to match build_pptx.py's palette, meant to be printed to
PDF via a headless browser (see render_pdf.js) for a visually-faithful,
pixel-perfect PDF companion to the .pptx.

Run: python docs/presentation/build_html.py
"""

import html
from pathlib import Path

from content import SLIDES

OUT_PATH = Path(__file__).parent / "deck.html"

CSS = """
:root {
  --bg: #0b0d12;
  --panel: #12151c;
  --border: #262b36;
  --text: #e8eaed;
  --muted: #9aa4b2;
  --accent: #5b9dff;
  --accent-2: #7ee0c3;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #000; }
body { font-family: "Segoe UI", -apple-system, Arial, sans-serif; }
.slide {
  width: 1280px;
  height: 720px;
  background: var(--bg);
  color: var(--text);
  position: relative;
  overflow: hidden;
  page-break-after: always;
  padding: 48px 56px;
}
.slide:last-child { page-break-after: auto; }
.slide h1 {
  font-size: 34px;
  margin: 0 0 4px;
  font-weight: 700;
}
.slide .subtitle { color: var(--muted); font-size: 14px; font-style: italic; margin-bottom: 8px; }
.underline { width: 90px; height: 4px; background: var(--accent); border-radius: 2px; margin-bottom: 28px; }
.footer {
  position: absolute;
  bottom: 28px;
  left: 56px;
  right: 56px;
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 12px;
}
.bullets { list-style: none; margin: 0; padding: 0; font-size: 21px; line-height: 1.7; }
.bullets li { margin-bottom: 16px; padding-left: 28px; position: relative; }
.bullets li::before { content: "▸"; position: absolute; left: 0; color: var(--accent); }
.quote-panel {
  background: var(--panel);
  border: 1.5px solid var(--accent);
  border-radius: 10px;
  padding: 28px 32px;
  font-size: 21px;
  font-style: italic;
  font-weight: 700;
  color: var(--accent-2);
  margin-bottom: 28px;
}
.title-slide { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%; }
.title-slide h1 { font-size: 52px; margin-bottom: 4px; }
.title-slide .sub { color: var(--accent); font-weight: 700; font-size: 28px; margin-bottom: 22px; }
.title-slide .tagline { color: var(--muted); font-style: italic; font-size: 17px; max-width: 900px; margin-bottom: 60px; }
.title-slide .footer-line { color: var(--muted); font-size: 14px; }
.title-slide .url { color: var(--accent-2); font-weight: 700; font-size: 15px; margin-top: 6px; }
.diagram-row { display: flex; align-items: center; margin-top: 40px; }
.diagram-box {
  background: var(--panel);
  border: 1.25px solid var(--border);
  border-radius: 8px;
  padding: 14px 10px;
  text-align: center;
  font-size: 13px;
  flex: 1;
  min-height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.diagram-box.endpoint { border-color: var(--accent); font-weight: 700; }
.diagram-arrow { color: var(--accent); font-size: 26px; font-weight: 700; padding: 0 10px; }
.callout { text-align: center; color: var(--accent-2); font-style: italic; font-weight: 700; font-size: 20px; margin-top: 50px; }
.stats-row { display: flex; gap: 24px; margin-top: 30px; }
.stat-panel {
  flex: 1;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 24px;
  text-align: center;
}
.stat-panel .group-label { color: var(--muted); font-weight: 700; font-size: 17px; margin-bottom: 14px; }
.stat-num { color: var(--accent); font-size: 40px; font-weight: 700; }
.stat-label { font-size: 15px; margin-bottom: 12px; }
.footnote { text-align: center; color: var(--accent-2); font-style: italic; font-size: 17px; margin-top: 30px; }
table.api { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 15px; }
table.api th {
  background: var(--accent);
  color: #0b0d12;
  text-align: left;
  padding: 8px 12px;
  font-size: 14px;
}
table.api td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
table.api tr:nth-child(even) td { background: var(--panel); }
table.api td.method { color: var(--accent-2); font-weight: 700; white-space: nowrap; }
table.api td.endpoint { color: var(--text); font-weight: 700; white-space: nowrap; font-family: monospace; }
table.api td.usecase { color: var(--muted); }
.question { color: var(--accent-2); font-style: italic; font-weight: 700; font-size: 25px; margin-bottom: 30px; }
.step-box {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  font-size: 17px;
  margin-bottom: 14px;
}
.step-box.last { border-color: var(--accent); font-weight: 700; }
.closing { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%; }
.closing h1 { font-size: 36px; margin-bottom: 30px; }
.closing .bullets { list-style: none; padding: 0; }
.closing .bullets li { color: var(--accent-2); font-size: 19px; margin-bottom: 10px; text-align: center; padding-left: 0; }
.closing .bullets li::before { content: ""; }
.closing .url { color: var(--accent); font-weight: 700; font-size: 22px; margin-top: 30px; }
.closing .repo { color: var(--muted); font-size: 15px; margin-top: 6px; }
@media print {
  body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .slide { page-break-after: always; }
}
"""


def esc(s):
    return html.escape(s, quote=False)


def render_title_bar(title, subtitle=None):
    out = f'<h1>{esc(title)}</h1>'
    if subtitle:
        out += f'<div class="subtitle">{esc(subtitle)}</div>'
    out += '<div class="underline"></div>'
    return out


def render_footer(index, total):
    return f'<div class="footer"><span>Municipal Law Skill for Autonomous Agents</span><span>{index}/{total}</span></div>'


def render_slide(s, index, total):
    kind = s["kind"]
    if kind == "title":
        return f"""
        <div class="slide title-slide">
          <h1>{esc(s['title'])}</h1>
          <div class="sub">{esc(s['subtitle'])}</div>
          <div class="tagline">{esc(s['tagline'])}</div>
          <div class="footer-line">{esc(s['footer'])}</div>
          <div class="url">{esc(s['url'])}</div>
        </div>
        """

    if kind == "bullets":
        items = "".join(f"<li>{esc(b)}</li>" for b in s["bullets"])
        return f"""
        <div class="slide">
          {render_title_bar(s['title'])}
          <ul class="bullets">{items}</ul>
          {render_footer(index, total)}
        </div>
        """

    if kind == "quote":
        items = "".join(f"<li>{esc(b)}</li>" for b in s["bullets"])
        return f"""
        <div class="slide">
          {render_title_bar(s['title'])}
          <div class="quote-panel">&ldquo;{esc(s['quote'].strip('“”'))}&rdquo;</div>
          <ul class="bullets">{items}</ul>
          {render_footer(index, total)}
        </div>
        """

    if kind == "diagram":
        steps = s["diagram"]
        boxes = []
        for i, step in enumerate(steps):
            cls = "diagram-box endpoint" if i in (0, len(steps) - 1) else "diagram-box"
            boxes.append(f'<div class="{cls}">{esc(step)}</div>')
            if i < len(steps) - 1:
                boxes.append('<div class="diagram-arrow">&rarr;</div>')
        return f"""
        <div class="slide">
          {render_title_bar(s['title'])}
          <div class="diagram-row">{''.join(boxes)}</div>
          <div class="callout">{esc(s['callout'])}</div>
          {render_footer(index, total)}
        </div>
        """

    if kind == "stats":
        groups = []
        for g in s["stat_groups"]:
            stat_html = "".join(
                f'<div class="stat-num">{esc(num)}</div><div class="stat-label">{esc(label)}</div>'
                for num, label in g["stats"]
            )
            groups.append(f'<div class="stat-panel"><div class="group-label">{esc(g["label"])}</div>{stat_html}</div>')
        return f"""
        <div class="slide">
          {render_title_bar(s['title'])}
          <div class="stats-row">{''.join(groups)}</div>
          <div class="footnote">{esc(s['footnote'])}</div>
          {render_footer(index, total)}
        </div>
        """

    if kind == "api_table":
        rows = "".join(
            f'<tr><td class="method">{esc(m)}</td><td class="endpoint">{esc(e)}</td><td class="usecase">{esc(u)}</td></tr>'
            for m, e, u in s["rows"]
        )
        return f"""
        <div class="slide">
          {render_title_bar(s['title'], s.get('subtitle'))}
          <table class="api">
            <tr><th>Method</th><th>Endpoint</th><th>Use case</th></tr>
            {rows}
          </table>
          {render_footer(index, total)}
        </div>
        """

    if kind == "story":
        steps = "".join(
            f'<div class="step-box{" last" if i == len(s["steps"]) - 1 else ""}">{i + 1}.&nbsp; {esc(step)}</div>'
            for i, step in enumerate(s["steps"])
        )
        return f"""
        <div class="slide">
          {render_title_bar(s['title'])}
          <div class="question">{esc(s['question'])}</div>
          {steps}
          {render_footer(index, total)}
        </div>
        """

    if kind == "closing":
        items = "".join(f"<li>{esc(b)}</li>" for b in s["bullets"])
        return f"""
        <div class="slide closing">
          <h1>{esc(s['title'])}</h1>
          <ul class="bullets">{items}</ul>
          <div class="url">{esc(s['url'])}</div>
          <div class="repo">{esc(s['repo'])}</div>
        </div>
        """

    raise ValueError(f"unknown slide kind: {kind}")


def build():
    total = len(SLIDES)
    slides_html = "\n".join(render_slide(s, i, total) for i, s in enumerate(SLIDES, start=1))
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Municipal Law Skill - Pitch Deck</title>
<style>{CSS}</style>
</head>
<body>
{slides_html}
</body>
</html>
"""
    OUT_PATH.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT_PATH} ({total} slides)")


if __name__ == "__main__":
    build()
