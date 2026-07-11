"""Generates docs/presentation/DECK_CONTENT.md from content.py - a plain,
reviewable/editable markdown mirror of the deck, one section per slide,
grouped logically. This is the easiest format to mark up changes in; once
edited, port the changes back into content.py (the actual source of truth)
and regenerate the .pptx/.pdf/.html from that.

Run: python docs/presentation/build_markdown.py
"""

from pathlib import Path

from content import SLIDES

OUT_PATH = Path(__file__).parent / "DECK_CONTENT.md"

# (group title, slide indices in that group - 0-based into SLIDES)
GROUPS = [
    ("Hook & positioning", [0, 1, 2]),
    ("Stories", [3, 4, 5]),
    ("Architecture & scale", [6, 7]),
    ("Engineering & why not an LLM", [8, 9]),
    ("API reference & trust", [10, 11]),
    ("Close", [12, 13]),
]


def render_slide_body(s: dict) -> str:
    kind = s["kind"]
    lines = []

    if kind == "title":
        lines.append(f"**{s['title']} {s['subtitle']}**")
        lines.append("")
        lines.append(f"*{s['tagline']}*")
        lines.append("")
        lines.append(f"{s['footer']}  ")
        lines.append(f"{s['url']}")

    elif kind == "bullets":
        for b in s["bullets"]:
            lines.append(f"- {b}")

    elif kind == "quote":
        lines.append(f"> {s['quote']}")
        lines.append("")
        if s.get("flows"):
            for flow in s["flows"]:
                lines.append(f"- **{flow['label']}**: {' → '.join(flow['steps'])}")
            lines.append("")
        for b in s.get("bullets", []):
            lines.append(f"- {b}")
        if s.get("emphasis"):
            lines.append("")
            lines.append(f"**{s['emphasis']}**")

    elif kind == "myth":
        lines.append(f"❌ **{s['wrong_label']}**: {s['wrong_claim']}")
        lines.append("")
        lines.append(f"✅ **{s['right_label']}**: {s['right_claim']} {s['right_detail']}")
        lines.append("")
        lines.append(f"*{s['footer_line']}*")

    elif kind == "comparison":
        lines.append(f"**{s['left_label']}**")
        for item in s["left_items"]:
            lines.append(f"- ✗ {item}")
        lines.append("")
        lines.append(f"**{s['right_label']}**")
        for item in s["right_items"]:
            lines.append(f"- ✓ {item}")

    elif kind == "diagram":
        if s.get("lead"):
            lines.append(f"**{s['lead']}**")
            lines.append("")
        lines.append(" → ".join(s["diagram"]))
        lines.append("")
        lines.append(f"*{s['callout']}*")

    elif kind == "stats":
        for g in s["stat_groups"]:
            stat_str = " · ".join(f"{num} {label}" for num, label in g["stats"])
            lines.append(f"- **{g['label']}**: {stat_str}")
        lines.append("")
        lines.append(f"*{s['footnote']}*")
        if s.get("callout"):
            lines.append("")
            lines.append(f"**{s['callout']}**")

    elif kind == "capability_table":
        if s.get("subtitle"):
            lines.append(f"*{s['subtitle']}*")
            lines.append("")
        lines.append("| Capability | Endpoint | Returns |")
        lines.append("|---|---|---|")
        for capability, endpoint, returns in s["rows"]:
            lines.append(f"| {capability} | `{endpoint}` | {returns} |")
        if s.get("admin_note"):
            lines.append("")
            lines.append(f"*{s['admin_note']}*")

    elif kind == "story":
        lines.append(f"**Question:** {s['question']}")
        lines.append("")
        citation_index = s.get("citation_index")
        flow_str = " → ".join(
            f"**{step}**" if i == citation_index else step
            for i, step in enumerate(s["flow"])
        )
        lines.append(flow_str)
        if s.get("answer"):
            lines.append("")
            lines.append(f"*{s['answer']}*")

    elif kind == "closing":
        for b in s["bullets"]:
            lines.append(f"- {b}")
        lines.append("")
        lines.append(f"**{s['url']}**  ")
        lines.append(f"{s['repo']}")

    else:
        raise ValueError(f"unknown slide kind: {kind}")

    return "\n".join(lines)


def build():
    total = len(SLIDES)
    out = ["# Pitch deck content (editable review copy)", ""]
    out.append(
        "One section per slide, grouped below. Edit this file freely to review/comment - "
        "when you're happy with changes, port them back into `content.py` (the real source "
        "of truth both `build_pptx.py` and `build_html.py` render from) and regenerate."
    )
    out.append("")

    for group_title, indices in GROUPS:
        out.append(f"## {group_title}")
        out.append("")
        for idx in indices:
            s = SLIDES[idx]
            slide_no = idx + 1
            title = s.get("title", "(untitled)")
            out.append(f"### Slide {slide_no}/{total} — {title}")
            out.append("")
            out.append(f"*kind: `{s['kind']}`*")
            out.append("")
            out.append(render_slide_body(s))
            out.append("")
        out.append("---")
        out.append("")

    OUT_PATH.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({total} slides, {len(GROUPS)} groups)")


if __name__ == "__main__":
    build()
