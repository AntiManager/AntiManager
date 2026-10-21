"""Structure linter for the system cards (`Карточки-систем.md`).

Checks:
  C1  14 cards S01-S14, one each, in order
  C2  field count: all cards S01-S14 = 12 numbered fields
  C3  no express references (C01-C40) anywhere
  C4  every criterion reference resolves to a full-checklist base row
      (blocks 1-6 for S01-S13, block 7 for S14), and S14 references only 7.x
  C5  every process code in field 4 resolves in the process library
  C6  artifact ids `S<NN>-A<NN>` are unique, sequential per card and carry
      the card's own prefix
  C7  each card has a «Проектный интерфейс» sentence in field 2
  C8  orphan artifacts (FPY, COQ, KPI passport, master data) are marked
      «вне полного чек-листа» with a library process reference
  C9  UTF-8 clean, no U+FFFD
  C10 project-type appendices A-D live in `Проектная-модель.md`, not here
  C11 S14 references the separate project model document

Policy for duplicate artifact names (same name in two systems, e.g. the
master-data registry in S01/S13) is NOT enforced: the contract is id-level.
Known duplicates are recorded in the plan report.

Usage:
  python .kilo/scripts/check_system_cards.py [VAULT_DIR]
Exit: 0 = clean, 1 = errors, 2 = usage / file not found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CARDS_REL = Path("\u041a\u0430\u0440\u0442\u043e\u0447\u043a\u0438-\u0441\u0438\u0441\u0442\u0435\u043c.md")
CHECKLIST_REL = Path("\u0410\u0443\u0434\u0438\u0442 \u041f\u0421") / "\u041f\u043e\u043b\u043d\u044b\u0439-\u0447\u0435\u043a-\u043b\u0438\u0441\u0442-\u0430\u0443\u0434\u0438\u0442\u0430-\u041f\u0421.md"
LIBRARY_REL = Path("\u0411\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0430 \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u043e\u0432") / "library"

CARD_RE = re.compile(r"^## (S\d{2}) .*$", re.M)
FIELD_RE = re.compile(r"^(\d{1,2})\. \*\*", re.M)
EXPRESS_REF = re.compile(r"\bC\d{2}\b")
BASE_REF = re.compile(r"\((\d{1,2}\.\d{1,2})\)")
PROC_RE = re.compile(r"\b([A-Z][A-Z0-9_]*-\d{2}(?:-\d{2}){0,2})\b")
ARTIFACT_RE = re.compile(r"^(S\d{2})-A(\d{2})\s")
LIB_CODE_RE = re.compile(
    r"^#{1,5}\s+(?:\u0413\u0440\u0443\u043f\u043f\u0430|\u041f\u0440\u043e\u0446\u0435\u0441\u0441|"
    r"\u041f\u043e\u0434\u043f\u0440\u043e\u0446\u0435\u0441\u0441|\u041e\u043f\u0435\u0440\u0430\u0446\u0438\u044f)"
    r"\s+([A-Z][A-Z0-9_-]*)",
    re.M,
)
CHECK_ROW_RE = re.compile(r"^\|\s*\*{0,2}(\d{1,2})\.(\d{1,2})\.")

ORPHANS = {
    "FPY": "QUAL-06",
    "COQ": "ANLZ-01-03",
    "KPI-\u043f\u0430\u0441\u043f\u043e\u0440\u0442": "ANLZ-01-02",
    "\u043c\u0430\u0441\u0442\u0435\u0440-\u0434\u0430\u043d\u043d\u044b\u0435": "PLAN-02-01",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def library_codes(root: Path) -> set[str]:
    codes: set[str] = set()
    if not root.exists():
        return codes
    for f in root.glob("*.md"):
        try:
            codes.update(LIB_CODE_RE.findall(read(f)))
        except (OSError, UnicodeDecodeError):
            continue
    return codes


def checklist_ids(path: Path) -> dict[str, set[int]]:
    """block -> set of criterion numbers."""
    ids: dict[str, set[int]] = {}
    if not path.exists():
        return ids
    for line in read(path).splitlines():
        m = CHECK_ROW_RE.match(line)
        if m:
            ids.setdefault(m.group(1), set()).add(int(m.group(2)))
    return ids


def expand_ranges(text: str) -> list[str]:
    codes = [m.group(1) for m in PROC_RE.finditer(text)]
    for m in re.finditer(
        r"\b([A-Z][A-Z0-9_]*-\d{2}(?:-\d{2})?)\u2026([A-Z][A-Z0-9_]*-\d{2})\b", text
    ):
        start, end = m.group(1), m.group(2)
        prefix = start[: start.rfind("-") + 1]
        try:
            a = int(start[start.rfind("-") + 1:])
            b = int(end[end.rfind("-") + 1:])
        except ValueError:
            continue
        for i in range(a, b + 1):
            codes.append(f"{prefix}{i:02d}")
    return codes


def main() -> int:
    vault = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault"
    )
    cards_path = vault / CARDS_REL
    if not cards_path.exists():
        print(f"ERROR cards file missing: {cards_path}")
        return 2

    raw = cards_path.read_bytes()
    errors: list[str] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"ERROR cards file is not valid UTF-8: {exc}")
        return 1
    if "\ufffd" in text:
        errors.append("cards: U+FFFD replacement character present")

    handles = CARD_RE.findall(text)
    expected = [f"S{i:02d}" for i in range(1, 15)]
    if handles != expected:
        errors.append(f"cards: found {handles}, expected S01-S14 in order")

    lib = library_codes(vault / LIBRARY_REL)
    if not lib:
        errors.append("library: no process codes parsed — check LIBRARY_REL")
    check = checklist_ids(vault / CHECKLIST_REL)
    valid_ids = {f"{b}.{n}" for b, nums in check.items() for n in nums}

    body = text
    positions = [(m.group(1), m.start()) for m in CARD_RE.finditer(body)]
    sections: dict[str, str] = {}
    for i, (handle, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(body)
        sec = body[start:end]
        if i + 1 == len(positions):
            cut = re.search(r"^## (?!S\d{2} ).*$", sec, re.M)
            if cut:
                sec = sec[: cut.start()]
        sections[handle] = sec

    if EXPRESS_REF.search(body):
        found = sorted(set(EXPRESS_REF.findall(body)))
        errors.append(f"cards: express references present: {', '.join(found)}")

    if re.search(r"^## \u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435", text, re.M):
        errors.append("cards: project-type appendices must live in \u041f\u0440\u043e\u0435\u043a\u0442\u043d\u0430\u044f-\u043c\u043e\u0434\u0435\u043b\u044c.md")

    for handle, sec in sections.items():
        fields = [int(n) for n in FIELD_RE.findall(sec)]
        want = 12
        if fields[:want] != list(range(1, want + 1)):
            errors.append(f"{handle}: fields {fields}, expected 1-{want}")
        elif len(fields) != want:
            errors.append(f"{handle}: {len(fields)} numbered fields, expected {want}")

        if handle == "S14" and "\u041f\u0440\u043e\u0435\u043a\u0442\u043d\u0430\u044f-\u043c\u043e\u0434\u0435\u043b\u044c" not in sec:
            errors.append("S14: no reference to \u041f\u0440\u043e\u0435\u043a\u0442\u043d\u0430\u044f-\u043c\u043e\u0434\u0435\u043b\u044c.md")

        m2 = re.search(r"^2\. \*\*\u0413\u0440\u0430\u043d\u0438\u0446\u044b\.\*\*.*$", sec, re.M)
        if not m2 or "\u041f\u0440\u043e\u0435\u043a\u0442\u043d\u044b\u0439 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441:" not in m2.group(0):
            errors.append(f"{handle}: no «Проектный интерфейс» sentence in field 2")

        # criterion references (parenthesised base ids + field 11 numbers)
        for ref in BASE_REF.findall(sec):
            if ref not in valid_ids:
                errors.append(f"{handle}: criterion {ref} not in the full checklist")
            elif handle != "S14" and ref.startswith("7."):
                errors.append(f"{handle}: references block 7 criterion {ref}")
            elif handle == "S14" and not ref.startswith("7."):
                errors.append(f"{handle}: S14 must reference only block 7, got {ref}")

        m4 = re.search(r"^4\. \*\*\u041f\u0440\u043e\u0446\u0435\u0441\u0441\u044b\.\*\*.*$", sec, re.M)
        if not m4:
            errors.append(f"{handle}: no process field")
        elif lib:
            for code in expand_ranges(m4.group(0)):
                if code not in lib:
                    errors.append(f"{handle}: process {code} not in library")

        ids = []
        for line in sec.splitlines():
            s = line.lstrip("- ").strip()
            m = ARTIFACT_RE.match(s)
            if m:
                if m.group(1) != handle:
                    errors.append(f"{handle}: artifact {m.group(1)}-A{m.group(2)} has a foreign prefix")
                ids.append(f"{m.group(1)}-A{m.group(2)}")
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            errors.append(f"{handle}: duplicate artifact ids {sorted(dupes)}")
        nums = sorted(int(i.split("-A")[1]) for i in ids)
        if nums and nums != list(range(1, len(nums) + 1)):
            errors.append(f"{handle}: artifact numbering {nums} is not sequential")

        m11 = re.search(r"^11\. \*\*\u041a\u0440\u0438\u0442\u0435\u0440\u0438\u0438 \u0447\u0435\u043a-\u043b\u0438\u0441\u0442\u0430\.\*\*(.*)$", sec, re.M)
        if not m11:
            errors.append(f"{handle}: no criterion field")
        else:
            for token in re.findall(r"\b\d{1,2}\.\d{1,2}\b", m11.group(1)):
                if token not in valid_ids:
                    errors.append(f"{handle}: field 11 criterion {token} unknown")
            if handle == "S14" and "7.1" not in m11.group(1):
                errors.append("S14: field 11 must list block 7 criteria")

    # orphan marking: any card that carries an orphan token must mark it
    for token in ORPHANS:
        for handle, sec in sections.items():
            low = sec.lower()
            if token.lower() in low and "\u0432\u043d\u0435 \u043f\u043e\u043b\u043d\u043e\u0433\u043e \u0447\u0435\u043a-\u043b\u0438\u0441\u0442\u0430" not in low:
                errors.append(f"{handle}: orphan «{token}» is not marked «вне полного чек-листа»")

    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
