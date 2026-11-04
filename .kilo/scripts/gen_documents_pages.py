"""Generate the /genome/documents/ partials from the Personal Vault.

Source of truth: `Методология ПС/Типовые документы/*.md` (public notes only).
Outputs:
  site/src/content/documents/<slug>.html   — article body partials
  site/src/content/genome/documents.html    — filled <!--DOCS:LIST:*--> region
  site/materials/<slug>.docx                — editable copy (pandoc)

`node build.js` stays vault-independent: this script runs offline after vault
edits. The DOCX is written from the same body the site uses, with wiki links
flattened to plain text.

The SOURCES whitelist is the IP guard: the internal СНУ regulation is never a
source, and every source must declare `public: true` in its frontmatter.

Usage:
  python .kilo/scripts/gen_documents_pages.py [--vault <path>] [--check] [--no-docx]

Exit codes: 0 = ok, 1 = drift in --check, 2 = missing vault/note or parse error.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
DEFAULT_VAULT = Path(r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault")
DOCS_JSON = HERE / "site" / "src" / "data" / "documents.json"
HUB = HERE / "site" / "src" / "content" / "genome" / "documents.html"
OUT = HERE / "site" / "src" / "content" / "documents"
MATERIALS = HERE / "site" / "materials"

DOC_DIR = Path("Методология ПС") / "Типовые документы"
MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
SOURCES = {
    "ritm-soveshchaniy": DOC_DIR / "Ритм-совещаний.md",
    "gemba-obhod": DOC_DIR / "Gemba-обход.md",
    "snu-kontur-uluchsheniy": DOC_DIR / "СНУ-концепт-бриф.md",
    "a3-reshenie-problem": DOC_DIR / "Форма-А3.md",
}

sys.path.insert(0, str(HERE / "pipelines" / "obsidian-to-site"))
from md_to_partial import convert  # noqa: E402


class ParseError(Exception):
    pass


def read(path: Path) -> str:
    if not path.exists():
        raise ParseError("file not found: " + str(path))
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def strip_title_block(md: str) -> str:
    """Drop frontmatter and the title/metadata block (mirrors md_to_partial)."""
    lines = md.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ParseError("source has no frontmatter")
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        i += 1
    if i >= len(lines):
        raise ParseError("frontmatter is not closed")
    body = lines[i + 1:]
    j = 0
    while j < len(body) and body[j].strip() != "---":
        j += 1
    if j >= len(body):
        raise ParseError("title block has no --- separator")
    return "\n".join(body[j + 1:]).strip() + "\n"


def frontmatter_value(md: str, key: str) -> str:
    m = re.search(r"^" + re.escape(key) + r":\s*(.+)$", md, re.M)
    return m.group(1).strip().strip('"\'') if m else ""


def flat_wiki(text: str) -> str:
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)


def ru_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return iso


def esc(value: str) -> str:
    return html.escape(str(value), quote=False)


def render_cards(docs: list[dict]) -> str:
    out = []
    for d in sorted(docs, key=lambda x: x.get("order", 0)):
        href = "/genome/documents/" + d["slug"] + "/"
        meta = "Версия %s · %s · обновлён %s" % (
            esc(d.get("version", "")), esc(d.get("license", "")),
            esc(ru_date(d.get("updated", ""))))
        out.append(
            '<article class="doc-tile">\n'
            '  <div class="doc-tile-meta">' + meta + '</div>\n'
            '  <h3 class="doc-tile-title"><a href="' + html.escape(href, quote=True) + '">'
            + esc(d["title"]) + '</a></h3>\n'
            '  <p class="doc-tile-sub">' + esc(d.get("subtitle", "")) + '</p>\n'
            '  <p>' + esc(d.get("summary", "")) + '</p>\n'
            '  <a class="btn btn-primary btn-sm" href="' + html.escape(href, quote=True)
            + '">Открыть документ</a>\n'
            '</article>'
        )
    return "\n".join(out)


def fill_hub(current: str, cards: str) -> str:
    start = "<!--DOCS:LIST:START-->"
    end = "<!--DOCS:LIST:END-->"
    if start not in current or end not in current:
        raise ParseError("hub marker missing: DOCS:LIST")
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pattern.sub(start + "\n" + cards + "\n" + end, current)


def load_docs() -> list[dict]:
    raw = json.loads(read(DOCS_JSON))
    for d in raw:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", d.get("slug", "")):
            raise ParseError("bad slug in documents.json: " + repr(d.get("slug")))
        if d["slug"] not in SOURCES:
            raise ParseError("documents.json slug has no vault source: " + d["slug"])
        for key in ("title", "subtitle", "summary", "version", "updated", "license"):
            if not d.get(key):
                raise ParseError("documents.json missing " + key + " for " + d["slug"])
        for href, _label, _desc in d.get("links", []):
            if not href.startswith("/"):
                raise ParseError("document link must start with /: " + href)
    return raw


def build(vault: Path, docs: list[dict]) -> tuple[dict[str, str], str, list[tuple[str, str]]]:
    partials = {}
    docx_sources = []
    for d in docs:
        rel = SOURCES[d["slug"]]
        src = vault / rel
        md = read(src)
        if frontmatter_value(md, "public") != "true":
            raise ParseError("source is not public: " + str(rel))
        if frontmatter_value(md, "library") != "documents":
            raise ParseError("source library is not documents: " + str(rel))
        body = strip_title_block(md)
        # The converter understands [[wiki]] links but leaves Markdown links
        # literal; promote them to real anchors (same rule as article partials).
        body_html = MD_LINK.sub(
            lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), convert(md))
        partial = "<!-- Документы: %s -->\n%s" % (d["title"], body_html.rstrip())
        partials[d["slug"]] = partial + "\n"
        docx_md = "# %s\n\nВерсия %s · %s · AntiManager\n\n%s" % (
            d["title"], d["version"], d["license"], flat_wiki(body))
        docx_sources.append((d["slug"], docx_md))
    hub = fill_hub(read(HUB), render_cards(docs))
    return partials, hub, docx_sources


def run_pandoc(md_text: str, dst: Path) -> None:
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                         encoding="utf-8", newline="\n") as tmp:
            tmp.write(md_text)
            tmp_name = tmp.name
        subprocess.run(
            ["pandoc", tmp_name, "-f", "gfm", "-t", "docx", "-o", str(dst)],
            check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise ParseError("pandoc is not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise ParseError("pandoc failed: " + exc.stderr.decode("utf-8", "replace")) from exc
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-docx", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault)
    try:
        docs = load_docs()
        partials, hub, docx_sources = build(vault, docs)
    except ParseError as exc:
        print("ERROR: " + str(exc).encode("ascii", "backslashreplace").decode())
        return 2

    if args.check:
        drift = []
        for slug, text in partials.items():
            target = OUT / (slug + ".html")
            if not target.exists() or read(target) != text:
                drift.append(str(target))
        if read(HUB) != hub:
            drift.append(str(HUB))
        if drift:
            print("DRIFT:")
            for d in drift:
                print("  - " + d.encode("ascii", "backslashreplace").decode())
            return 1
        print("OK no drift")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for slug, text in partials.items():
        (OUT / (slug + ".html")).write_text(text, encoding="utf-8", newline="\n")
    HUB.write_text(hub, encoding="utf-8", newline="\n")

    if not args.no_docx:
        MATERIALS.mkdir(parents=True, exist_ok=True)
        try:
            for slug, md_text in docx_sources:
                run_pandoc(md_text, MATERIALS / (slug + ".docx"))
        except ParseError as exc:
            print("WARNING: " + str(exc))
            return 2

    print("OK: %d document partials, hub cards and DOCX written" % len(partials))
    return 0


if __name__ == "__main__":
    sys.exit(main())
