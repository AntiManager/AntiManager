#!/usr/bin/env python3
"""Derive the unified event grid from the source ФРПС grid (plan 1791810263662, Phase D).

Source (client grid, read-only):
  Proc_library/library/reglaments/ФРПС/Сетка_регулярных_событий.md   (11 sections)
Target (unified artifact, one file):
  <vault>/library/artifacts/Сетка_регулярных_событий.md

Rules (specs/T4.3):
  - 11 source sections -> 11 output sections (Принципы ... Гемба).
  - only cadence sections (Ежедневные/Еженедельные/Ежемесячные/Квартальные/
    Годовые) carry the contract grid table; the others are ported token-free.
  - owner text -> exactly one canonical role code (`Имя (КОД)`);
    participants -> de-duplicated role codes; workers dropped.
  - every row gets a section-consistent `Горизонт` (H3/H4).
  - every row references >=1 valid library code (H7); shorthands expanded.
  - client/holding tokens stripped (H6).

Usage:
  python author_event_grid.py --analyze
  python author_event_grid.py --emit <vault> [--out <file>]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import check_artifacts  # noqa: E402
import author_priority_matrix as apm  # noqa: E402 (reuse de-id CLEAN list)

SRC_DEFAULT = os.path.join(
    os.path.dirname(HERE), "..", "..", "Proc_library", "library",
    "reglaments", "ФРПС", "Сетка_регулярных_событий.md")

SEC_RE = re.compile(r"^##\s+(\d+)\.\s*(.*?)\s*$")
GRID_HEADER = ("| Триггер/Период | Событие | Длительность | Владелец | "
               "Участники | Повестка | Вход | Выход | Процессы | Горизонт |")
GRID_SEP = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"

# section number -> (cadence-horizon default, is-cadence-table)
CADENCE = {"2": "shift", "3": "week", "4": "month", "5": "quarter", "6": "year"}
# titles whose source form carries parentheses (must be paren-free: T4.9 §3)
RETITLE = {
    "10": "10. Календарный план на год",
    "11": "11. Гемба-обходы: типология и регламенты",
}
# grid-specific de-identification: phrase rules run BEFORE apm.CLEAN (so they
# see the original client tokens), generic fallbacks AFTER it.
GRID_PRE = [
    (re.compile(r"Начальник ПЭО"), "Руководитель экономической службы"),
    (re.compile(r"форм[аы]?\s+УПЛ"), "установленная форма"),
    (re.compile(r"в УПЛ\b"), "на вышестоящий уровень управления"),
    (re.compile(r"от УСИС\b"), "от органа по сертификации"),
    (re.compile(r"по графику ЦСМ"), "по графику поверки"),
    (re.compile(r"договор с ЦСМ"), "договор на поверку"),
]
GRID_POST = [
    (re.compile(r"\bУПЛ\b"), "вышестоящий уровень управления"),
    (re.compile(r"\bУСИС\b"), "орган по сертификации"),
    (re.compile(r"\bЦСМ\b"), "метрологическая служба"),
    # H6 flags the client cross-ref phrase «Регламент 8.x» (case-sensitive).
    # Keep the number for traceability, neutralise only the client wording.
    (re.compile(r"Регламент\s*(8\.\d+)"), r"регламент \1"),
]
# NB: never strip a bare `8.x` — it is the artifact's own §8 subsection number
# (`### 8.1. …`); doing so shatters the heading into `### .` and mangles §10.
# The H6 stop-word only matches the capitalised phrase «Регламент 8.x».

# owner/participant labels with no registry synonym -> explicit code
# (specs/T4.3 §4). Consulted only AFTER `roles_for_string` yields nothing, so
# the registry stays authoritative; only genuinely unresolved labels live here.
OWNER_OVERRIDE = [
    ("специалист по развитию", "ГТ"),
]

CODE_FULL = re.compile(r"^[A-Z][A-Z0-9_-]*-\d{2}(?:-\d{2})*$")
CODE_CONT = re.compile(r"^-(\d{2}(?:-\d{2})*)$")


def clean(s: str) -> str:
    for pat, repl in GRID_PRE + apm.CLEAN + GRID_POST:
        s = pat.sub(repl, s)
    s = re.sub(r"\s*,\s*(?=[,|])", " ", s)   # drop dangling comma-after-number lists
    s = re.sub(r"\s*,\s*$", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def short_name(name):
    """Registry display name without a trailing domain qualifier in parens.

    Renders owner cells as `Имя (КОД)` (specs/T4.3 §4) without the double
    parentheses a qualified name (e.g. `Главный механик (техслужба)`) would
    otherwise produce.
    """
    return re.sub(r"\s*\([^()]*\)\s*$", "", name or "").strip()


def parse_source(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    sections, cur = [], None
    for ln in lines:
        m = SEC_RE.match(ln)
        if m:
            cur = {"num": m.group(1), "title": m.group(2), "body": []}
            sections.append(cur)
            continue
        if cur is not None:
            cur["body"].append(ln)
    return sections


def _cells(ln):
    return [c.strip() for c in ln.strip().strip("|").split("|")]


def parse_grid_table(body):
    """Return the data rows of the first source table in a cadence section.

    §2–§3 carry a `Структура повестки` column (9 cols); §4–§6 do not (8 cols).
    """
    rows, started = [], False
    for ln in body:
        if not ln.strip().startswith("|"):
            if started:
                break
            continue
        cells = _cells(ln)
        if not started:
            if cells[:2] == ["Время / Триггер", "Событие"] or \
               cells[:2] == ["Декада / Дата", "Событие"] or \
               cells[:2] == ["Месяц квартала", "Событие"] or \
               cells[:2] == ["Период", "Событие"] or \
               cells[:2] == ["День недели", "Событие"]:
                started = True
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if len(cells) >= 8:
            rows.append(cells)
    return rows


def norm_codes(raw, lib, unknown):
    out, last = [], None
    for tok in re.split(r"[,\s]+", raw or ""):
        tok = tok.strip().strip(".")
        if not tok:
            continue
        if CODE_FULL.match(tok):
            last, cand = tok, tok
        elif CODE_CONT.match(tok) and last:
            cand = last[: last.rfind("-")] + tok
        else:
            continue
        if cand in lib.by_code:
            if cand not in out:
                out.append(cand)
        elif cand not in unknown:
            unknown.append(cand)
    return out


def override_code(cell):
    """Explicit code for a label the registry cannot resolve (specs/T4.3 §4)."""
    low = (cell or "").lower()
    for needle, code in OWNER_OVERRIDE:
        if needle in low:
            return code
    return None


def owner_code(reg, cell):
    codes = check_artifacts.roles_for_string(reg, cell)
    if codes:
        return codes[0]
    return override_code(cell)


def participant_codes(reg, cell):
    out = []
    for part in re.split(r"[,/;]|\(|\)", cell or ""):
        p = part.strip()
        if not p:
            continue
        if p in reg["code_set"]:
            cand = p
            if cand not in out:
                out.append(cand)
            continue
        codes = check_artifacts.roles_for_string(reg, p)
        if not codes:
            oc = override_code(p)
            codes = [oc] if oc else []
        for c in codes:
            if c not in out:
                out.append(c)
    return out


def horizon_daily(event):
    e = event.lower()
    if "tier 1" in e:
        return "shift"
    if "tier 2" in e or "tier 3" in e:
        return "day"
    if any(k in e for k in ("обход", "гемба", "сводка", "входной контроль")):
        return "shift"
    return "day"


def render_cadence(sec, reg, lib, unknown, names):
    num = sec["num"]
    default = CADENCE[num]
    rows = parse_grid_table(sec["body"])
    out = []
    for cells in rows:
        trigger, event, dur = clean(cells[0]), clean(cells[1]), clean(cells[2])
        owner = owner_code(reg, cells[3])
        owner_txt = "%s (%s)" % (names[owner], owner) if owner else "—"
        if len(cells) >= 9:
            participants = participant_codes(reg, cells[4])
            agenda, inp, outp = clean(cells[5]), clean(cells[6]), clean(cells[7])
            raw_codes = cells[8]
        else:
            participants = participant_codes(reg, cells[4])
            agenda, inp, outp = "–", clean(cells[5]), clean(cells[6])
            raw_codes = cells[7]
        codes = norm_codes(raw_codes, lib, unknown)
        if not codes:
            continue  # H7: a grid row must reference a valid code
        part_txt = ", ".join(participants) if participants else "–"
        hz = horizon_daily(event) if num == "2" else default
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            trigger, event, dur or "–", owner_txt, part_txt, agenda or "–",
            inp or "–", outp or "–", ", ".join(codes), hz))
    return out


def render_body(sec):
    """Ported (unparsed) section body, token-cleaned; cadence tables skipped."""
    out = []
    for ln in sec["body"]:
        if "Методологическая основа" in ln:
            out.append("> **Методологическая основа:** сетка реализует управление "
                       "временем и данными (TDM) и подтверждение процесса "
                       "(гемба с Т-картами).")
            continue
        if ln.strip().startswith("*Документ разработан") or \
           ln.strip().startswith("*Дата следующего пересмотра"):
            continue
        out.append(clean(ln))
    return out


def render(sections, reg, lib, unknown, names, order):
    L = ["---", "artifact: event-grid",
         "roles: [%s]" % ", ".join(order),
         "status: draft", "updated: 2026-10-13",
         "tags: [library, artifacts, schedule]", "---", "",
         "# Сетка регулярных событий производственного подразделения", "",
         "> Артефакт единой цепочки управления (КТК → приоритеты руководителей → "
         "сетка регулярных событий). В каденционных таблицах (§2–§6) владелец "
         "каждого события — одна из 10 канонических ролей (`Имя (КОД)`); "
         "портированные разделы (§7, §9, §11) сохраняют исходные формулировки "
         "ролей. Реестр ролей — `Роли.md`; спецификация — `specs/T4.3` (EN).", ""]
    for sec in sections:
        num = sec["num"]
        title = RETITLE.get(num, "%s. %s" % (num, sec["title"]))
        L.append("## " + title)
        L.append("")
        if num in CADENCE:
            L.append(GRID_HEADER)
            L.append(GRID_SEP)
            L.extend(render_cadence(sec, reg, lib, unknown, names))
            L.append("")
        else:
            L.extend(render_body(sec))
            L.append("")
    # collapse runs of blank lines, keep one final newline
    collapsed = []
    for ln in L:
        if ln == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(ln)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()
    return "\n".join(collapsed) + "\n"


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--emit")
    ap.add_argument("--out")
    ap.add_argument("--src", default=SRC_DEFAULT)
    args = ap.parse_args(argv)

    sections = parse_source(args.src)
    if args.analyze:
        for s in sections:
            n = len(parse_grid_table(s["body"])) if s["num"] in CADENCE else 0
            print(f"§{s['num']:>2} {s['title'][:44]:<44} rows={n}")
        return 0

    if not args.emit:
        ap.error("choose --analyze or --emit <vault>")
    vault = args.emit
    reg = check_artifacts.load_registry()
    lib = check_artifacts.parse_library(vault)
    names = {r["code"]: short_name(r["name"]) for r in reg["roles"]}
    order = [r["code"] for r in reg["roles"]]
    unknown = []
    text = render(sections, reg, lib, unknown, names, order)

    out = args.out or os.path.join(vault, "library", "artifacts",
                                   "Сетка_регулярных_событий.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {out}")
    if unknown:
        print("  unknown codes dropped:", ", ".join(sorted(set(unknown))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
