#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic article readiness screen (layer 1).

Scans numbered Markdown articles in the vault's ARTICLES_DIR and scores each
against an objective 12-point publish-readiness rubric. Writes a UTF-8 Markdown
report (default: .kilo/reports/article-readiness.md) and prints an ASCII summary.

The editorial layer (intro thesis, case quality, style) is NOT covered here; use
the `article-readiness` skill for that. No vault files are modified.

Usage:
    python .kilo/scripts/article_readiness.py [ARTICLES_DIR] [--out PATH]
                                              [--json PATH]
                                              [--min-words N] [--max-block N]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

CONCL = re.compile(r"итог|вывод|заключ|резюме|эпилог|послесловие|ключев|главное|запомни|что делать", re.I)
CASE = re.compile(r"кейс|пример|истори|практик", re.I)
ACTION = re.compile(r"чек-?лист|протокол|шаг|алгоритм|инструмент|калькулятор|упражнен|шаблон|тест", re.I)
REL_TOOLS = re.compile(r"связанные инструменты", re.I)
REL_CH = re.compile(r"связанные главы", re.I)
PLACEHOLDER = re.compile(r"TODO|TBD|FIXME|XXX|\?\?\?|\[\.\.\.\]|дописать|placeholder|<<<|>>>", re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
WIKILINK = re.compile(r"\[\[[^\]]+\]\]")
FRONTMATTER_KEYS = ("tags", "status", "created", "updated")

CHECK_LABELS = {
    "frontmatter": "frontmatter",
    "has_title": "title",
    "length_ok": "length",
    "rel_tools": "related-tools",
    "rel_chapters": "related-chapters",
    "conclusion": "conclusion",
    "action": "action",
    "case": "case",
    "crosslinks": "crosslinks",
    "no_placeholders": "placeholders",
    "no_heading_jumps": "heading-jumps",
    "encoding_clean": "encoding",
}


def read_articles_dir() -> str:
    env = REPO / ".env"
    if not env.exists():
        return ""
    # .env is user-local and may be UTF-8 or legacy cp1251; try both.
    data = env.read_bytes()
    text = None
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return ""
    for line in text.splitlines():
        if line.strip().startswith("ARTICLES_DIR="):
            return line.split("=", 1)[1].strip()
    return ""


def analyze(text: str, min_words: int, max_block: int):
    has_bom = text.startswith("\ufeff")
    text = text.lstrip("\ufeff")
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line.strip())
                if m:
                    fm[m.group(1)] = m.group(2).strip()
            body = text[end + 4:]

    matches = list(HEADING.finditer(body))
    titles = [m.group(2) for m in matches]
    jumps = sum(1 for i in range(1, len(matches))
                if len(matches[i].group(1)) > len(matches[i - 1].group(1)) + 1)

    blocks = []
    for i, m in enumerate(matches):
        stop = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        blocks.append(len(re.findall(r"\S+", body[m.end():stop])))
    words = len(re.findall(r"\S+", body))
    max_block_words = max(blocks) if blocks else words
    wiki = len(WIKILINK.findall(body))

    checks = {
        "frontmatter": all(k in fm for k in FRONTMATTER_KEYS),
        "has_title": len(matches) >= 1,
        "length_ok": words >= min_words,
        "rel_tools": any(REL_TOOLS.search(t) for t in titles),
        "rel_chapters": any(REL_CH.search(t) for t in titles),
        "conclusion": any(CONCL.search(t) for t in titles),
        "action": any(ACTION.search(t) for t in titles),
        "case": any(CASE.search(t) for t in titles),
        "crosslinks": wiki >= 2,
        "no_placeholders": not PLACEHOLDER.search(body),
        "no_heading_jumps": jumps == 0,
        "encoding_clean": (not has_bom) and "\ufffd" not in text,
    }
    return {
        "status": fm.get("status", ""),
        "tags": fm.get("tags", ""),
        "words": words,
        "headings": len(matches),
        "level_jumps": jumps,
        "max_block_words": max_block_words,
        "monolithic": max_block_words > max_block,
        "first_heading": titles[0] if titles else "",
        "wiki": wiki,
        "placeholders": sorted(set(m.group(0) for m in PLACEHOLDER.finditer(body))),
        "checks": checks,
        "score": sum(1 for v in checks.values() if v),
        "total": len(checks),
    }


def verdict(score: int, total: int) -> str:
    ratio = score / total
    if ratio >= 11 / 12:
        return "READY"
    if ratio >= 8 / 12:
        return "NEEDS-EDIT"
    return "DRAFT"


def main() -> int:
    ap = argparse.ArgumentParser(description="Article readiness screen (layer 1)")
    ap.add_argument("articles_dir", nargs="?", default="")
    ap.add_argument("--out", default=str(REPO / ".kilo" / "reports" / "article-readiness.md"))
    ap.add_argument("--json", dest="json_out", default="")
    ap.add_argument("--min-words", type=int, default=800)
    ap.add_argument("--max-block", type=int, default=2000)
    args = ap.parse_args()

    articles_dir = args.articles_dir or read_articles_dir()
    if not articles_dir or not os.path.isdir(articles_dir):
        print("ERROR: ARTICLES_DIR not found (set it in .env or pass a path)")
        return 2

    rows = []
    for name in sorted(os.listdir(articles_dir)):
        if not name.lower().endswith(".md") or not re.match(r"^\d{2}_", name):
            continue
        raw = (Path(articles_dir) / name).read_bytes()
        text = raw.decode("utf-8", errors="replace")
        info = analyze(text, args.min_words, args.max_block)
        info["num"] = name[:2]
        info["file"] = name
        rows.append(info)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Article readiness report (layer 1)", "",
             "Source: `%s`" % articles_dir, "",
             "| # | status | words | headings | jumps | max block | wiki | score | verdict | failed |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        failed = ", ".join(CHECK_LABELS[k] for k, v in r["checks"].items() if not v) or "—"
        lines.append("| {n} | {s} | {w} | {h} | {j} | {mb} | {wl} | {sc}/{t} | {v} | {f} |".format(
            n=r["num"], s=r["status"] or "-", w=r["words"], h=r["headings"],
            j=r["level_jumps"], mb=r["max_block_words"], wl=r["wiki"],
            sc=r["score"], t=r["total"], v=verdict(r["score"], r["total"]), f=failed))
    lines += ["", "## Flags", ""]
    for r in rows:
        flags = []
        if r["monolithic"]:
            flags.append("monolithic block of %d words (no subheadings)" % r["max_block_words"])
        if r["level_jumps"]:
            flags.append("%d heading-level jump(s)" % r["level_jumps"])
        if r["placeholders"]:
            flags.append("placeholders: " + ", ".join(r["placeholders"]))
        if flags:
            lines.append("- **%s %s** — %s" % (r["num"], r["file"], "; ".join(flags)))
    lines += ["", "Layer 2 (editorial: intro thesis, case quality, style) is in the",
              "`article-readiness` skill. This report only covers objective checks.", ""]
    out.write_text("\n".join(lines), encoding="utf-8")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = {}
    for r in rows:
        counts[verdict(r["score"], r["total"])] = counts.get(verdict(r["score"], r["total"]), 0) + 1
    print("articles: %d" % len(rows))
    for k in ("READY", "NEEDS-EDIT", "DRAFT"):
        if counts.get(k):
            print("  %s: %d" % (k, counts[k]))
    print("report: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
