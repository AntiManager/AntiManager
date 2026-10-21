"""Structure + banned-token linter for the PS audit toolset.

Checks:
  base    -- 120 criteria, fixed block ranges, 9 columns, no empty cells, banned tokens
  express -- 40 criteria C01-C40, every criterion maps to an existing base criterion,
             every row is identical to its base row (title, anchors 0-5, KPI,
             verification) -- the express may only compress the number of criteria,
             all six blocks are represented, no system-card references, banned tokens

Usage:
  python .kilo/scripts/check_ps_audit.py [VAULT_DIR]

Exit codes: 0 = clean, 1 = errors found, 2 = usage / file not found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE_REL = Path("Аудит ПС") / "Полный-чек-лист-аудита-ПС.md"
EXPRESS_REL = Path("Аудит ПС") / "Экспресс-чек-лист-аудита-ПС.md"

BLOCK_RANGES = {1: 31, 2: 24, 3: 7, 4: 26, 5: 14, 6: 18, 7: 12}
BASE_COLUMNS = 9  # Критерий | 0 | 1 | 2 | 3 | 4 | 5 | KPI | Способ верификации
EXPRESS_COLUMNS = 10  # ID | Критерий | 0 | 1 | 2 | 3 | 4 | 5 | KPI | Способ верификации

# SHA-256 over the normalized rows of blocks 1-6 (criteria 1.1-6.18).
# Any wording change in the published core invalidates the site/express contract.
# Regenerate deliberately with: python check_ps_audit.py --print-fingerprint <vault>
BASE_FINGERPRINT = "da9ad2f2ff70fe6c5695bfa6747098d7dd1549485102218d87956299688b30dd"
BLOCK7_HEAD = "## Блок 7"
BLOCK7_END = "## Связанные документы"

SYSTEM_REF = re.compile(r"(?<![А-Яа-яA-Za-z])(?:S\d{2}|Карточки-систем)(?![А-Яа-яA-Za-z])")

PREFIX_VAGUE = ["эффективн", "качественн", "правильн", "надлежащ"]
WORD_VAGUE = [
    "должным образом", "в основном", "не всегда", "часто", "регулярно",
    "периодически", "эпизодически", "как получится", "по факту",
]
SOFT_FREQ = ["регулярно", "периодически", "эпизодически"]
CLIENT_ORG = [
    "полипластик", "фрпс", "производственное управление",
    "управление складским комплексом", "дивизион", "холдинг",
]
BRAND = ["e-staff", "e‑staff", "1с", "sap"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_rows(text: str) -> list[tuple[int, list[str]]]:
    rows = []
    for raw in text.splitlines():
        if not raw.lstrip().startswith("|"):
            continue
        cells = split_row(raw)
        if not cells or set("".join(cells)) <= set("-: "):
            continue
        rows.append((len(cells), cells))
    return rows


def check_tokens(label: str, text: str, errors: list[str], warns: list[str]) -> None:
    low = text.lower()
    for token in PREFIX_VAGUE:
        for m in re.finditer(re.escape(token), low):
            errors.append(f"{label}: vague token «{token}» at offset {m.start()}")
    for token in WORD_VAGUE:
        pattern = r"(?<![а-яёa-z])" + re.escape(token) + r"(?![а-яёa-z])"
        for m in re.finditer(pattern, low):
            errors.append(f"{label}: vague token «{token}» at offset {m.start()}")
    for token in CLIENT_ORG:
        if re.search(r"(?<![а-яa-z])" + re.escape(token) + r"(?![а-яa-z])", low):
            errors.append(f"{label}: client/org token «{token}»")
    for token in BRAND:
        if token in low:
            errors.append(f"{label}: brand token «{token}»")
    for token in SOFT_FREQ:
        pattern = r"(?<![а-яёa-z])" + re.escape(token) + r"(?![а-яёa-z])"
        if re.search(pattern, low):
            warns.append(f"{label}: soft frequency «{token}» — requires a quantified period in the same cell")


def fingerprint(text: str) -> str:
    """SHA-256 of the normalized rows of blocks 1-6 (published core)."""
    import hashlib

    parts = []
    for cells in (c for n, c in table_rows(text) if n == BASE_COLUMNS):
        m = re.match(r"^\*{0,2}(\d+)\.(\d+)\.", cells[0])
        if not m or int(m.group(1)) > 6:
            continue
        parts.append("|".join(" ".join(c.split()) for c in cells))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def block7_text(text: str) -> str:
    start = text.find(BLOCK7_HEAD)
    if start < 0:
        return ""
    end = text.find(BLOCK7_END, start)
    return text[start:end if end > 0 else len(text)]


def check_base(path: Path, errors: list[str], warns: list[str]) -> None:
    if not path.exists():
        errors.append(f"base file missing: {path}")
        return
    text = read(path)
    rows = [c for n, c in table_rows(text) if n == BASE_COLUMNS]
    found: dict[int, list[str]] = {b: [] for b in BLOCK_RANGES}
    for cells in rows:
        m = re.match(r"^\*{0,2}(\d+)\.(\d+)\.", cells[0])
        if not m:
            continue
        block, num = int(m.group(1)), int(m.group(2))
        if block not in found:
            errors.append(f"base: unexpected block {block} in «{cells[0][:40]}»")
            continue
        found[block].append(f"{block}.{num}")
        for idx, cell in enumerate(cells[1:], start=1):
            if not cell:
                errors.append(f"base: empty cell {idx} in criterion «{cells[0][:60]}»")
    for block, expected in BLOCK_RANGES.items():
        ids = found[block]
        if len(ids) != expected:
            errors.append(
                f"base: block {block} has {len(ids)} criteria, expected {expected}"
            )
        expected_ids = {f"{block}.{i}" for i in range(1, expected + 1)}
        missing = sorted(expected_ids - set(ids))
        if missing:
            errors.append(f"base: block {block} missing {', '.join(missing)}")
    total = sum(len(ids) for ids in found.values())
    if total != sum(BLOCK_RANGES.values()):
        errors.append(
            f"base: {total} criteria, expected {sum(BLOCK_RANGES.values())}"
        )
    if not block7_text(text):
        errors.append("base: block 7 «Контур изменений» not found")
    got = fingerprint(text)
    if BASE_FINGERPRINT != "__FINGERPRINT__" and got != BASE_FINGERPRINT:
        errors.append(
            "base: criteria 1.1-6.18 changed (published core fingerprint mismatch)"
        )
    body = text.split("---", 2)[-1]
    check_tokens("base", body, errors, warns)
    for m in SYSTEM_REF.finditer(block7_text(text)):
        errors.append(f"base: block 7 system-card reference «{m.group(0)}»")


def check_express(path: Path, base_text: str, errors: list[str], warns: list[str]) -> None:
    if not path.exists():
        errors.append(f"express file missing: {path}")
        return
    text = read(path)
    base_rows: dict[str, list[str]] = {}
    for cells in (c for n, c in table_rows(base_text) if n == BASE_COLUMNS):
        m = re.match(r"^\*{0,2}(\d+)\.(\d+)\.", cells[0])
        if m:
            base_rows[f"{m.group(1)}.{m.group(2)}"] = cells

    seen = set()
    blocks = set()
    for cells in (c for n, c in table_rows(text) if n == EXPRESS_COLUMNS):
        if not re.match(r"^C\d{2}", cells[0]):
            continue
        cid = cells[0].split()[0]
        if cid in seen:
            errors.append(f"express: duplicate criterion {cid}")
        seen.add(cid)
        map_match = re.search(r"\((\d+\.\d+)\)", cells[0])
        if not map_match:
            errors.append(f"express: {cid} has no base mapping")
            continue
        base_id = map_match.group(1)
        blocks.add(int(base_id.split(".")[0]))
        if int(base_id.split(".")[0]) > 6:
            errors.append(f"express: {cid} maps to block 7 ({base_id}); express covers blocks 1-6 only")
            continue
        if base_id not in base_rows:
            errors.append(f"express: {cid} maps to missing base criterion {base_id}")
            continue
        expected = base_rows[base_id]
        title = re.sub(r"^\*{0,2}\d+\.\d+\.\s*", "", expected[0]).rstrip("*").strip()
        expected = [title] + expected[1:]
        actual = cells[1:]
        if actual != expected:
            diff = [i for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
            errors.append(
                f"express: {cid} differs from base {base_id} "
                f"in cell(s) {', '.join(str(i + 1) for i in diff)}"
            )
        for idx, cell in enumerate(cells[1:], start=1):
            if not cell:
                errors.append(f"express: empty cell {idx} in {cid}")

    expected_ids = {f"C{i:02d}" for i in range(1, 41)}
    missing = sorted(expected_ids - seen)
    extra = sorted(seen - expected_ids)
    if missing:
        errors.append(f"express: missing criteria {', '.join(missing)}")
    if extra:
        errors.append(f"express: unexpected criteria {', '.join(extra)}")
    if seen and blocks != {1, 2, 3, 4, 5, 6}:
        errors.append(f"express: blocks covered {sorted(blocks)}, expected 1-6")
    for m in SYSTEM_REF.finditer(text):
        errors.append(f"express: system-card reference «{m.group(0)}»")
    check_tokens("express", text, errors, warns)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    vault = Path(args[0]) if args else Path(
        r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault"
    )
    if "--print-fingerprint" in sys.argv:
        base = vault / BASE_REL
        if not base.exists():
            print(f"base file missing: {base}")
            return 2
        print(fingerprint(read(base)))
        return 0
    errors: list[str] = []
    warns: list[str] = []
    base = vault / BASE_REL
    check_base(base, errors, warns)
    base_text = read(base) if base.exists() else ""
    check_express(vault / EXPRESS_REL, base_text, errors, warns)

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
