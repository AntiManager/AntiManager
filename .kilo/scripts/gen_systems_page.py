"""Generate the /genome/systems/ page, the owner document and the blank card template.

Source of truth: the Obsidian vault note `Карточки-систем.md`.
Outputs:
  site/src/content/genome/systems.html          — filled <!--SYSTEMS:*--> regions
  <vault>/Карта-систем-собственнику.md           — compact owner document
  <vault>/Карта-систем-собственнику.docx         — sendable copy (pandoc)
  site/materials/ps-systems-map/system-card-template.md/.docx — blank 12-field template

`node build.js` stays vault-independent: this script runs offline after vault edits.

Usage:
  python .kilo/scripts/gen_systems_page.py [--vault <path>] [--check] [--no-docx]

Exit codes: 0 = ok, 1 = drift in --check, 2 = missing vault/note or parse error.
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
DEFAULT_VAULT = Path(r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault")
NOTE_REL = Path("Карточки-систем.md")
PARTIAL = HERE / "site" / "src" / "content" / "genome" / "systems.html"
OWNER_MD_REL = Path("Карта-систем-собственнику.md")
OWNER_DOCX_REL = Path("Карта-систем-собственнику.docx")
TEMPLATE_DIR = HERE / "site" / "materials" / "ps-systems-map"
TEMPLATE_MD = TEMPLATE_DIR / "system-card-template.md"
TEMPLATE_DOCX = TEMPLATE_DIR / "system-card-template.docx"

MARKERS = ["META", "SUMMARY", "CARDS"]
CARD_RE = re.compile(r"^## (S\d{2}) — (.+?)\s*$", re.M)
FIELD_RE = re.compile(r"^(\d{1,2})\. \*\*(.+?)\*\*\s*(.*)$")
ARTIFACT_RE = re.compile(r"^(S\d{2}-A\d{2})\s+(.+)$")
PROC_RE = re.compile(r"\b[A-Z]{2,5}(?:_[A-Z]+)?-\d{2}(?:-\d{2})?(?:-\d{2})?\b")
ROLE_RE = re.compile(r"\((ГД|РП|ГИ|ГТ|РК|РС|ГМ|HR|НЦ|НС)\)")
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]


class ParseError(Exception):
    pass


def read(path: Path) -> str:
    if not path.exists():
        raise ParseError(f"file not found: {path}")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def parse_cards(path: Path) -> list[dict]:
    text = read(path)
    matches = list(CARD_RE.finditer(text))
    if len(matches) != 14:
        raise ParseError(f"expected 14 cards, found {len(matches)}")
    cards = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        fields: dict[int, dict] = {}
        current: int | None = None
        for line in body.split("\n"):
            fm = FIELD_RE.match(line)
            if fm:
                current = int(fm.group(1))
                rest = fm.group(3).strip()
                fields[current] = {"label": fm.group(2).strip(),
                                   "body": [rest] if rest else [], "items": []}
                continue
            if current is None:
                continue
            s = line.strip()
            if not s or s == "---":
                continue
            if s.startswith("- "):
                fields[current]["items"].append(s[2:].strip())
            else:
                fields[current]["body"].append(s)
        missing = [n for n in range(1, 13) if n not in fields]
        if missing:
            raise ParseError(f"{m.group(1)}: missing fields {missing}")
        cards.append({"id": m.group(1), "title": m.group(2).strip(), "fields": fields})
    return cards


def ftext(card: dict, n: int) -> str:
    return " ".join(card["fields"][n]["body"]).strip()


def plain(s: str) -> str:
    s = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), s)
    return s


def first_sentence(s: str, limit: int = 170) -> str:
    s = plain(s)
    m = re.match(r"^(.+?[.!?])(?:\s|$)", s)
    out = m.group(1) if m else s
    if len(out) > limit:
        out = out[:limit].rsplit(" ", 1)[0] + "…"
    return out


def role_of(card: dict) -> str:
    m = ROLE_RE.search(ftext(card, 3))
    return m.group(1) if m else plain(ftext(card, 3))


def artifacts(card: dict, field: int) -> list[tuple[str, str]]:
    out = []
    for item in card["fields"][field]["items"]:
        m = ARTIFACT_RE.match(item)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def artifact_name(item: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", item).strip()


def process_count(card: dict) -> int:
    return len(set(PROC_RE.findall(ftext(card, 4))))


def render_meta(cards: list[dict]) -> str:
    total_codes = sum(process_count(c) for c in cards)
    total_art = sum(len(artifacts(c, 5)) + len(artifacts(c, 6)) for c in cards)
    return (f"{len(cards)} систем · 12 полей · {total_codes} кодов процессов · "
            f"{total_art} артефактов P1/P2")


def render_summary(cards: list[dict]) -> str:
    rows = []
    for c in cards:
        rows.append(
            "        <tr>"
            f"<td class=\"cv\"><a href=\"#{c['id'].lower()}\">{c['id']}</a></td>"
            f"<td>{inline(c['title'])}</td>"
            f"<td>{html.escape(role_of(c))}</td>"
            f"<td>{html.escape(first_sentence(ftext(c, 1)))}</td>"
            f"<td class=\"num\">{len(artifacts(c, 5))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_field(card: dict, n: int) -> str:
    f = card["fields"][n]
    label = inline(f["label"])
    items = f["items"]
    body = " ".join(f["body"]).strip()
    if n in (5, 6) and items:
        lis = []
        for item in items:
            m = ARTIFACT_RE.match(item)
            if m:
                lis.append(f"<li><code>{html.escape(m.group(1))}</code> {inline(m.group(2))}</li>")
            else:
                lis.append(f"<li>{inline(item)}</li>")
        prefix = f"<p><strong>{n}. {label}</strong></p>" if not body else \
                 f"<p><strong>{n}. {label}</strong> {inline(body)}</p>"
        return prefix + "<ul class=\"sys-artifacts\">" + "".join(lis) + "</ul>"
    text = inline(body)
    return f"<p><strong>{n}. {label}</strong> {text}</p>"


def render_cards(cards: list[dict]) -> str:
    out = []
    for c in cards:
        owner = html.escape(plain(ftext(c, 3)))
        p1 = len(artifacts(c, 5))
        out.append(
            f"      <article class=\"doc-card sys-card\" id=\"{c['id'].lower()}\">\n"
            f"        <div class=\"dc-head\"><span class=\"dc-no\">{c['id']}</span>"
            f"<h3>{inline(c['title'])}</h3></div>\n"
            f"        <p class=\"dc-desc\">{inline(ftext(c, 1))}</p>\n"
            f"        <div class=\"dc-meta\"><span>Владелец: {owner}</span>"
            f"<span>Процессов: {process_count(c)}</span><span>Артефактов P1: {p1}</span></div>\n"
            "        <details class=\"doc-full\"><summary>Открыть карточку · 12 полей</summary>\n"
            "          <div class=\"doc-body\">\n"
            + "\n".join("            " + render_field(c, n) for n in range(1, 13)) + "\n"
            "          </div>\n"
            "        </details>\n"
            "      </article>"
        )
    return "\n".join(out)


def fill_markers(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        start = f"<!--SYSTEMS:{key}:START-->"
        end = f"<!--SYSTEMS:{key}:END-->"
        if start not in text or end not in text:
            raise ParseError(f"partial marker missing: {key}")
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        text = pattern.sub(start + "\n" + value + "\n" + end, text)
    return text


def build_partial(current: str, cards: list[dict]) -> str:
    return fill_markers(current, {
        "META": render_meta(cards),
        "SUMMARY": render_summary(cards),
        "CARDS": render_cards(cards),
    })


def owner_markdown(cards: list[dict], updated: str) -> str:
    lines = [
        "# Карта систем производственной системы",
        "",
        f"> Краткая версия для собственника · {len(cards)} систем · обновлено {updated}",
        "",
        "## Зачем эта карта",
        "",
        "Производственная система состоит из четырнадцати управляемых систем. "
        "У каждой есть владелец, минимальный набор артефактов, показатели результата и "
        "типовой разрыв. Карта показывает, где система держится на людях, а где — на "
        "документированной практике, и что ломается, если минимум не собран.",
        "",
        "## Как читать",
        "",
        "- **Система** — контур управления, а не оргподразделение.",
        "- **Владелец** — роль, которая отвечает за результат системы.",
        "- **Минимум** — артефакты, без которых практика не существует.",
        "- **Типовой разрыв** — самое частое отставание.",
        "- **Риск** — что происходит, если минимум не собран.",
        "",
        "## Обзор",
        "",
        "| Система | Владелец | Ключевой KPI |",
        "| --- | --- | --- |",
    ]
    for c in cards:
        kpi = re.split(r"\.\s+", plain(ftext(c, 7)))[0].strip(" .")
        kpi = re.sub(r"\.?\s*Ведутся по Ф-KPI\.?$", "", kpi).strip()
        if len(kpi) > 90:
            kpi = kpi[:90].rsplit(" ", 1)[0] + "…"
        lines.append(f"| {c['id']} {plain(c['title'])} | {role_of(c)} | {kpi} |")
    lines += ["", "## Системы", ""]
    for c in cards:
        names = [artifact_name(x[1]) for x in artifacts(c, 5)[:4]]
        minimum = "; ".join(names) if names else "—"
        lines += [
            f"### {c['id']}. {plain(c['title'])}",
            "",
            f"**Владелец:** {plain(ftext(c, 3))}",
            "",
            f"**Задача.** {plain(ftext(c, 1))}",
            "",
            f"**Минимум.** {minimum}.",
            "",
            f"**Типовой разрыв.** {plain(ftext(c, 10))}",
            "",
            f"**Риск.** {plain(ftext(c, 12))}",
            "",
        ]
    lines += [
        "## Что дальше",
        "",
        "Полная карта с процессами, критериями чек-листа и полным составом артефактов — "
        "на сайте: /genome/systems/.",
        "",
        "Разбор под конкретное предприятие — через форму на /contact/ или в Штабе.",
        "",
    ]
    return "\n".join(lines)


def template_markdown() -> str:
    return "\n".join([
        "# Шаблон карточки системы",
        "",
        "Одна карточка — одна система. Скопируйте блок ниже и заполните двенадцать полей.",
        "Карточка описывает контур управления, а не оргподразделение.",
        "",
        "## S__ — Название системы",
        "",
        "1. **Назначение.** Что система делает и зачем она нужна.",
        "2. **Границы.** Входит: … Не входит: … **Проектный интерфейс:** …",
        "3. **Владелец.** Роль из канонического реестра (код).",
        "4. **Процессы.** Коды процессов из библиотеки.",
        "5. **Артефакты P1 (минимум).**",
        "   - S__-A01 Артефакт (критерий чек-листа или «вне полного чек-листа»; код процесса)",
        "6. **Артефакты P2 (зрелость).** Артефакты уровней 4–5.",
        "7. **KPI и паспорт.** Показатели результата; ведутся по `Ф-KPI`.",
        "8. **Ритм управления.** Периодичность обзора; каденция по `Ф-СРС`.",
        "9. **Целевое состояние (уровень 3).** Как выглядит регулярная практика.",
        "10. **Типовые разрывы.** Безличные, самые частые отставания.",
        "11. **Критерии чек-листа.** Базовые номера полного чек-листа.",
        "12. **Риски при отсутствии артефактов.** Что ломается без минимума.",
        "",
    ])


def run_pandoc(src: Path, dst: Path) -> None:
    try:
        subprocess.run(
            ["pandoc", str(src), "-f", "gfm", "-t", "docx", "-o", str(dst),
             "--metadata", "lang=ru-RU"],
            check=True, capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ParseError("pandoc is not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise ParseError("pandoc failed: " + exc.stderr.decode("utf-8", "replace")) from exc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-docx", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault)
    note = vault / NOTE_REL
    try:
        cards = parse_cards(note)
        updated = datetime.fromtimestamp(note.stat().st_mtime)
        updated_s = f"{updated.day} {MONTHS[updated.month - 1]} {updated.year}"
        partial_new = build_partial(read(PARTIAL), cards)
        owner_md = owner_markdown(cards, updated_s)
        template_md = template_markdown()
    except ParseError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.check:
        drift = []
        if read(PARTIAL) != partial_new:
            drift.append(str(PARTIAL))
        if not (vault / OWNER_MD_REL).exists() or read(vault / OWNER_MD_REL) != owner_md:
            drift.append(str(vault / OWNER_MD_REL))
        if not TEMPLATE_MD.exists() or read(TEMPLATE_MD) != template_md:
            drift.append(str(TEMPLATE_MD))
        if drift:
            print("DRIFT:")
            for d in drift:
                print("  -", d)
            return 1
        print("OK no drift")
        return 0

    PARTIAL.write_text(partial_new, encoding="utf-8", newline="\n")
    (vault / OWNER_MD_REL).write_text(owner_md, encoding="utf-8", newline="\n")
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_MD.write_text(template_md, encoding="utf-8", newline="\n")

    if not args.no_docx:
        try:
            run_pandoc(vault / OWNER_MD_REL, vault / OWNER_DOCX_REL)
            run_pandoc(TEMPLATE_MD, TEMPLATE_DOCX)
        except ParseError as exc:
            print(f"WARNING: {exc}")
            return 2

    print(f"OK: {len(cards)} cards; page, owner md/docx and template written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
