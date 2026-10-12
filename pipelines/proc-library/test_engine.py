"""Tests for the process-library engine (T0.9).

Run:  python -m pytest -q   (from pipelines/proc-library)
"""
import json
import os
import re
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402
import rollup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

VOCAB = {
    "version": "0.1",
    "ids": {"Партия", "Протокол", "Документ", "Сертификат", "Сырьё", "Материал",
            "Комплект", "План", "Заявка", "Измерение", "Показатель", "Отходы",
            "Полуфабрикат", "ГотоваяПродукция"},
    "parents": {},
}

VAULT = os.environ.get(
    "PROC_LIB_VAULT",
    r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов")


def parse(text, name="lib.md"):
    lib = engine.Library()
    engine.parse_text(text, name, lib)
    return lib


def parse_dir(files: dict):
    d = tempfile.mkdtemp()
    for name, text in files.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)
    return engine.parse_paths(d)


STUB = """# Библиотека тест
**Цель библиотеки:** контур.
## Группа TMPL: Демонстрационная
**Цель группы:** показать конвенцию.
### Процесс TMPL-01: процесс
**Цель:** провести поток.
**APQC:** 4.0
#### Подпроцесс TMPL-01-01: подпроцесс
**Цель:** зафиксировать и оформить.
##### Операция TMPL-01-01-01: регистрация
- **Тип:** `Simple`
- **Цель:** зафиксировать поступление
- **Выходы:** `Партия@Поступила`
- **decomposition:** ATOMIC
##### Операция TMPL-01-01-02: оформление
- **Тип:** `Simple`
- **Цель:** оформить протокол
- **Входы:** `Партия@Поступила`
- **Выходы:** `Протокол`
- **decomposition:** ATOMIC
##### Операция TMPL-01-01-03: передача
- **Тип:** `Simple`
- **Цель:** передать протокол
- **Входы:** `Протокол`
- **decomposition:** ATOMIC
### Карта связей
| Источник (Операция.Выход) | → | Приёмник (Операция.Вход) | Условие |
|---------------------------|:---:|---------------------------|---------|
| TMPL-01-01-01.Партия@Поступила | → | TMPL-01-01-02.Партия@Поступила | авто |
| TMPL-01-01-02.Протокол | → | TMPL-01-01-03.Протокол | всегда |
"""


def _group(tag):
    return f"""## Группа {tag}: группа {tag}
**Цель группы:** x
### Процесс {tag}-01: процесс
**Цель:** x
**APQC:** 4.0
#### Подпроцесс {tag}-01-01: подпроцесс
**Цель:** x
##### Операция {tag}-01-01-01: вход
- **Тип:** `Simple`
- **Цель:** x
- **Выходы:** `Протокол`
##### Операция {tag}-01-01-02: выход
- **Тип:** `Simple`
- **Цель:** x
- **Входы:** `Протокол`
| {tag}-01-01-01.Протокол | → | {tag}-01-01-02.Протокол | c |
"""


def test_stub_is_valid():
    lib = parse(STUB)
    errs, _ = engine.validate(lib, VOCAB)
    assert errs == [], errs


def test_stub_operations_parsed():
    lib = parse(STUB)
    codes = {n.code for n in engine._iter_nodes(lib) if n.level == "OPERATION"}
    assert codes == {"TMPL-01-01-01", "TMPL-01-01-02", "TMPL-01-01-03"}
    assert len(lib.links) == 2


def test_legacy_container_synthesizes_codes_and_flags_free_text():
    legacy = """# Библиотека
## Группа LEG: Тест
**Цель группы:** x
### Процесс LEG-01: p
**Цель:** x
**APQC:** 4.0
#### Подпроцесс LEG-01-01: s
**Цель:** x
##### Операции подпроцесса LEG-01-01:

1. **Первая операция**
\t- Исполнитель: Кто
\t\t- Входы: Текст входа
\t\t- Выходы: Текст выхода
\t\t- КПЭ: 15 мин
2. **Вторая операция**
\t- Исполнитель: Кто
\t\t- Входы: Текст выхода
\t\t- Выходы: Готово
"""
    lib = parse(legacy)
    codes = {n.code for n in engine._iter_nodes(lib) if n.level == "OPERATION"}
    assert codes == {"LEG-01-01-01", "LEG-01-01-02"}
    _, warns = engine.validate(lib, VOCAB)
    assert any("FREE-TEXT" in w for w in warns)


def test_unknown_type_is_invalid():
    text = STUB.replace("`Протокол`", "`НеизвестныйТип`")
    lib = parse(text)
    errs, _ = engine.validate(lib, VOCAB)
    assert any("UNKNOWN TYPE" in e for e in errs)


def test_dangling_output_is_invalid():
    text = STUB.replace(
        "| TMPL-01-01-02.Протокол | → | TMPL-01-01-03.Протокол | всегда |", "")
    lib = parse(text)
    errs, _ = engine.validate(lib, VOCAB)
    assert any("DANGLING output" in e for e in errs)


def test_missing_goal_is_invalid():
    text = STUB.replace("- **Цель:** оформить протокол\n", "")
    lib = parse(text)
    errs, _ = engine.validate(lib, VOCAB)
    assert any("MISSING GOAL" in e and "TMPL-01-01-02" in e for e in errs)


def test_missing_apqc_is_invalid():
    text = STUB.replace("**APQC:** 4.0\n", "")
    lib = parse(text)
    errs, _ = engine.validate(lib, VOCAB)
    assert any("MISSING APQC" in e for e in errs)


def test_attr_block_after_blank_line_is_parsed():
    # The source library lays out every heading as: heading, blank line, block.
    # Before the T1.2 fix the blank line ended the block, so every goal/APQC was
    # silently dropped; this asserts the block is still collected.
    text = (
        "# Библиотека t\n"
        "**Цель библиотеки:** цель библиотеки\n\n"
        "## Группа BLK: группа\n\n"
        "**Код:** BLK\n"
        "**Владелец:** x\n"
        "**Цель группы:** цель группы\n"
        "### Процесс BLK-01: процесс\n\n"
        "**Код:** BLK-01\n"
        "**Цель:** цель процесса\n"
        "**APQC:** 4.0\n"
        "#### Подпроцесс BLK-01-01: подпроцесс\n\n"
        "**Цель:** цель подпроцесса\n"
        "##### Операция BLK-01-01-01: операция\n"
        "- **Цель:** цель операции\n"
        "- **Выходы:** `Протокол`\n"
    )
    lib = parse(text)
    assert lib.by_code["BLK"].goal() == "цель группы"
    assert lib.by_code["BLK-01"].goal() == "цель процесса"
    assert lib.by_code["BLK-01"].attrs.get("APQC") == "4.0"
    assert lib.by_code["BLK-01-01"].goal() == "цель подпроцесса"
    errs, _ = engine.validate(lib, VOCAB)
    assert not any("MISSING GOAL" in e for e in errs)


def test_split_regression_identical_graph():
    one = parse_dir({"all.md": "# Библиотека t\n" + _group("TSTA") + _group("TSTB")})
    two = parse_dir({"a.md": "# Библиотека t\n" + _group("TSTA"),
                     "b.md": _group("TSTB")})
    sig_one = engine.graph_signature(one)
    sig_two = engine.graph_signature(two)
    assert sig_one == sig_two
    assert len(sig_one["nodes"]) > 0


def test_split_library_preserves_graph(tmp_path):
    import split_library
    src = tmp_path / "Proc_lib.md"
    src.write_text("---\nversion: '1'\n---\n"
                   "# Библиотека t\n*Версия: `= this.version`*\n"
                   "## Содержание\n1. A\n\n---\n\n"
                   "## Реестр\n\n| a |\n\n---\n"
                   + _group("TSTA") + "\n---\n\n" + _group("TSTB"),
                   encoding="utf-8")
    out = tmp_path / "library"
    assert split_library.main([str(src), str(out)]) == 0
    assert (out / "INDEX.md").exists()
    assert (out / "TSTA.md").exists() and (out / "TSTB.md").exists()

    before = engine.graph_signature(engine.parse_paths(str(src)))
    after = engine.graph_signature(engine.parse_paths(str(out)))
    assert before == after and len(before["nodes"]) > 0

    index = (out / "INDEX.md").read_text(encoding="utf-8")
    assert "= this.version" not in index and "[[TSTA|" in index
    assert "## Реестр" in index  # separator structure preserved


def test_cycle_without_exit_is_invalid():
    text = _group("CYC") + """### Карта связей
| CYC-01-01-01.Протокол | → | CYC-01-01-02.Протокол | c |
| CYC-01-01-02.Протокол | → | CYC-01-01-01.Протокол | c |
"""
    # second op must emit Протокол to close the loop
    text = text.replace("- **Входы:** `Протокол`\n",
                        "- **Входы:** `Протокол`\n- **Выходы:** `Протокол`\n")
    lib = parse("# B\n" + text)
    errs, _ = engine.validate(lib, VOCAB)
    assert any("CYCLE WITHOUT EXIT" in e for e in errs)


def test_operation_economics_domains_validated():
    # T0.5/T0.6: out-of-domain economics values are errors.
    text = STUB.replace(
        "- **decomposition:** ATOMIC\n",
        "- **Критичность:** urgent\n"
        "- **Периодичность:** sometimes\n"
        "- **Трудоёмкость:** много ч\n"
        "- **Стоимость:** дорого руб\n"
        "- **decomposition:** MAYBE\n", 1)
    lib = parse(text)
    errs, _ = engine.validate(lib, VOCAB)
    for rule in ("BAD CRITICALITY", "BAD PERIODICITY", "BAD LABOUR",
                 "BAD COST", "BAD DECOMPOSITION"):
        assert any(rule in e for e in errs), rule


def test_operation_economics_valid_values_accepted():
    text = STUB.replace(
        "- **decomposition:** ATOMIC\n",
        "- **Критичность:** high\n"
        "- **Периодичность:** shift ×3\n"
        "- **Трудоёмкость:** 0,25 ч\n"
        "- **Стоимость:** 300 руб\n"
        "- **decomposition:** ATOMIC\n", 1)
    lib = parse(text)
    errs, _ = engine.validate(lib, VOCAB)
    assert not any(e.startswith("BAD ") for e in errs), errs


@pytest.mark.skipif(not os.path.exists(os.path.join(VAULT, "specs", "_template-stub.md")),
                    reason="vault not present")
def test_vault_template_stub_valid():
    stub = os.path.join(VAULT, "specs", "_template-stub.md")
    lib = engine.parse_paths(stub, include_all=True)
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    assert vocab is not None
    errs, _ = engine.validate(lib, vocab)
    assert errs == [], errs


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_subprocess_freeze_errors_are_operation_only():
    """T1.5 freeze: every validator error must be OPERATION-level.

    The subprocess skeleton (LIBRARY/GROUP/PROCESS/SUBPROCESS) must be clean:
    goals present, APQC present, no hierarchy/duplicate errors. Operation-level
    free-text I/O and goals are Phase-2 (T2.2) and are the ONLY allowed errors.
    """
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, _ = engine.validate(lib, vocab)

    # every error is attributable to an OPERATION node
    for e in errs:
        m = re.search(r"\b([A-Z][A-Z0-9_-]*-\d[A-Z0-9_-]*)\b", e)
        assert m, f"freeze violation: error has no node code: {e}"
        node = lib.by_code.get(m.group(1))
        assert node is not None, f"freeze violation: unknown node in error: {e}"
        assert node.level == "OPERATION", f"freeze violation (non-operation error): {e}"

    # explicit subprocess-level invariants (falsifiable, independent of the loop)
    for n in engine._iter_nodes(lib):
        if n.level in ("GROUP", "PROCESS", "SUBPROCESS"):
            assert n.goal(), f"missing goal at {n.level} {n.code}"
        if n.level == "PROCESS":
            assert n.attrs.get("APQC"), f"missing APQC on {n.code}"
    assert not any("§4.7" in e or "§4.9" in e or "§4.10" in e for e in errs)
    assert not any("DUPLICATE CODE" in e for e in errs)


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_planning_pilot_has_no_dangling():
    """T2.3/T2.4: the Planning pilot (PLAN + SL_PLAN) is fully clean.

    After the flow-link pass (T2.3) and the economics pass (T2.4) the pilot must
    have zero findings of any kind (goals, typing, dangling, flow-conservation,
    duplicates): the ABC/XYZ §7.9 duplicate was resolved in T2.4 Decision 5.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)
    scoped_errs = engine_filter.scoped(errs, ["PLAN-", "SL_PLAN-"])
    assert scoped_errs == [], scoped_errs
    scoped_warns = engine_filter.scoped(warns, ["PLAN-", "SL_PLAN-"])
    assert scoped_warns == [], scoped_warns


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_planning_boundary_ops_are_sensor_or_actor():
    """T2.3: the pilot perimeter is explicit sensors/actors.

    Sensors have no inputs and >=1 output; actors have >=1 input and no output.
    """
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    sensors = ("PLAN-01-01-01", "SL_PLAN-02-01-01",
               "PLAN-03-01-05", "SL_PLAN-02-01-04")
    actors = ("PLAN-02-03-04", "PLAN-03-02-06", "PLAN-03-03-05")
    for c in sensors:
        n = lib.by_code.get(c)
        assert n is not None and not n.io_in and n.io_out, c
    for c in actors:
        n = lib.by_code.get(c)
        assert n is not None and n.io_in and not n.io_out, c


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_planning_pilot_has_full_characteristics():
    """T2.4: every pilot operation carries the full T0.5 economics block."""
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    pilot = [n for n in engine._iter_nodes(lib)
             if n.level == "OPERATION"
             and (n.code.startswith("PLAN-") or n.code.startswith("SL_PLAN-"))]
    assert len(pilot) == 66, len(pilot)
    for n in pilot:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_planning_rollup_converges_on_sample():
    """T2.4: reference roll-up on subprocess PLAN-01-01 (T0.5 Decision 2)."""
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    ops = [lib.by_code[f"PLAN-01-01-0{i}"] for i in range(1, 6)]
    executions_per_year = {"shift": 3 * 365, "day": 365, "week": 52,
                           "month": 12, "quarter": 4, "year": 1}
    annual_fund = 1700
    rank = {"low": 0, "medium": 1, "high": 2}

    def num(s):
        return float(s.split()[0].replace(",", "."))

    def freq(periodicity):
        return executions_per_year[periodicity.split()[0]]

    fte = sum(num(o.attrs["Трудоёмкость"]) * freq(o.attrs["Периодичность"])
              / annual_fund for o in ops)
    layer_cost = sum(num(o.attrs["Стоимость"]) * freq(o.attrs["Периодичность"])
                     for o in ops)
    criticality = max(ops, key=lambda o: rank[o.attrs["Критичность"]])
    assert round(fte, 3) == 0.138, fte
    assert int(layer_cost) == 234000, layer_cost
    assert criticality.attrs["Критичность"] == "high"


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_has_no_client_identity_tokens():
    """T1.5 freeze: zero client-identity tokens (T0.6).

    Checks legal-entity names, monetary figures/targets, plant codes and person
    names. This test would have caught QUAL-06-02 '500 тыс. руб.'.
    """
    import token_scan
    res = token_scan.scan(os.path.join(VAULT, "library"))
    assert res["identity"] == [], res["identity"]


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_apqc_crosswalk_covers_every_process():
    # T1.3: mapping and library must not drift; every PROCESS carries the attr,
    # and every mapped code must exist in the APQC L3 catalog fixture.
    mapping = json.load(open(os.path.join(HERE, "apqc_mapping.json"),
                             encoding="utf-8"))["processes"]
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    procs = {n.code for n in engine._iter_nodes(lib) if n.level == "PROCESS"}
    assert procs == set(mapping), procs ^ set(mapping)
    for n in engine._iter_nodes(lib):
        if n.level == "PROCESS":
            assert n.attrs.get("APQC"), f"{n.code} has no APQC attribute"

    cat = os.path.join(HERE, "apqc_catalog.json")
    if os.path.exists(cat):
        valid = {x["hier"] for x in
                 json.load(open(cat, encoding="utf-8"))["l3"]}
        for code, codes in mapping.items():
            for c in codes:
                assert c in valid, f"{code} -> unknown APQC L3 {c}"


# --------------------------------------------------------------------------
# T2.5 — economic roll-up (reference FTE and layer cost)
# --------------------------------------------------------------------------
def test_rollup_executions_and_num():
    """T2.5: frequency unit -> executions/year and number parsing."""
    assert rollup.executions("week \u00d71") == 52
    assert rollup.executions("shift \u00d73") == 3 * 365 * 3
    assert rollup.executions("month \u00d72") == 24
    assert rollup.executions("event \u00d75") == 5
    assert rollup.executions("nonsense") is None
    assert rollup.num("0,5 \u0447") == 0.5
    assert rollup.num("300 \u0440\u0443\u0431") == 300.0


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_planning_rollup_matrix_is_additive_and_reproducible():
    """T2.5: the pilot matrix is finite, additive and identical on re-run."""
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    rows = rollup.rollup_matrix(lib, scope=["PLAN", "SL_PLAN"])
    by = {r["code"]: r for r in rows}

    # scope defaults to nodes carrying economics: exactly the two pilot groups.
    assert {r["code"] for r in rows if r["level"] == "GROUP"} == {"PLAN", "SL_PLAN"}

    total = rollup.totals(rows, "GROUP")
    assert total["ops"] == 66, total
    assert total["fte"] == pytest.approx(11.008, abs=1e-3), total
    assert total["cost"] == pytest.approx(18713750, abs=1.0), total

    # identity: cost = hours * REF_RATE = fte * AnnualFund * REF_RATE
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE, abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r

    # additivity: every parent equals the sum of its children.
    for code in ("PLAN-01", "PLAN-02", "PLAN-03", "SL_PLAN-01", "SL_PLAN-02",
                 "SL_PLAN-03", "PLAN", "SL_PLAN"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # control-set continuity with T2.4.
    sample = by["PLAN-01-01"]
    assert sample["fte"] == pytest.approx(0.138, abs=1e-3), sample
    assert sample["cost"] == pytest.approx(234000, abs=1.0), sample
    assert sample["criticality"] == "high"

    # deterministic roll-up.
    assert rollup.rollup_matrix(lib, scope=["PLAN", "SL_PLAN"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mfg_process_01_is_typed_and_goaled():
    """T2.6: production-core tranche MFG-01 converted to typed OPERATION nodes.

    Every operation of process MFG-01 (subprocesses 01-03, 17 ops) carries a goal
    and vocabulary-typed I/O: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE finding
    in the MFG-01 scope. Dangling (§4.2) is the next replication step (flow graph)
    and is deliberately not asserted here.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("MFG-01-01", "MFG-01-02", "MFG-01-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 17, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD "))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mfg_processes_02_to_05_are_typed_and_goaled():
    """T2.6: production-core tranche 2 — MFG-02..MFG-05 converted.

    MFG-02/03 came from the legacy container form, MFG-04/05 were already
    `##### Операция` nodes with free-text I/O; both are now typed operations.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE /
    BAD / TYPE-CARDINALITY in the scope (dangling §4.2 is the flow-graph step).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("MFG-02-01", "MFG-02-02", "MFG-02-03", "MFG-02-04",
            "MFG-03-01", "MFG-03-02", "MFG-03-03",
            "MFG-04-01", "MFG-04-02", "MFG-04-03",
            "MFG-05-01", "MFG-05-02", "MFG-05-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 46, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mnt_flow_graph_is_closed():
    """T2.6 sub-step 3: the equipment-maintenance flow graph closes every I/O.

    `MNT.md` carries a «Потоки (Flow Links)» table (internal MNT→MNT flow plus
    cross-domain seams to PLAN / MFG / SL_MNT / SL_PLAN / SL_ANL / INF) and **7
    explicit boundary operations** (2 sensors + 5 actors for the enterprise
    perimeter: manufacturer/external standards, HR; ERP/archive, HRP, IMPR,
    management/finance, production). Assert the domain gate: no DANGLING §4.2 and
    no CYCLE WITHOUT EXIT §4.5 in the MNT scope, and no warnings; every boundary
    op is a sensor (no inputs) or an actor (no outputs).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["MNT-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["MNT-"]) == [], \
        engine_filter.scoped(warns, ["MNT-"])

    for code in ("MNT-01-03-06", "MNT-03-03-03"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in ("MNT-01-04-06", "MNT-02-01-04", "MNT-02-03-04", "MNT-04-03-04",
                 "MNT-05-02-03"):
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mfg_flow_graph_is_closed():
    """T2.6 sub-step 3: the production-core flow graph closes every I/O.

    `MFG.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    PLAN/ENG/QUAL/SL_LOG/INF/MNT/HRP/ORG/ANLZ/STRAT seams). Assert the domain
    gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the MFG scope.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["MFG"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["MFG"]) == [], \
        engine_filter.scoped(warns, ["MFG"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mfg_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 63 MFG ops + domain roll-up.

    Every production-core operation carries the T0.5 economics block with
    in-domain values; the domain scope stays clean (0 errors / 0 warnings) and
    the MFG roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("MFG-")]
    assert len(ops) == 63, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["MFG"]) == []

    rows = rollup.rollup_matrix(lib, scope=["MFG"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 63, group
    assert group["fte"] == pytest.approx(22.748676, abs=1e-4), group
    assert group["cost"] == pytest.approx(38672750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("MFG-01", "MFG-02", "MFG-03", "MFG-04", "MFG-05"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["MFG"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_log_process_01_is_typed_and_goaled():
    """T2.6: logistics replication tranche SL_LOG-01 converted to typed nodes.

    Every operation of process SL_LOG-01 (subprocesses 01-05, 38 ops — the 33
    converted operations plus 5 boundary sensors added by the flow-graph pass)
    carries a goal, a valid `Тип` and vocabulary-typed I/O: no MISSING GOAL /
    FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY finding in the SL_LOG-01
    scope. Dangling (§4.2) is closed by `test_vault_sl_log_flow_graph_is_closed`.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_LOG-01-01", "SL_LOG-01-02", "SL_LOG-01-03",
            "SL_LOG-01-04", "SL_LOG-01-05")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 38, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_log_processes_02_to_04_are_typed_and_goaled():
    """T2.6: logistics replication tranche 2 — SL_LOG-02..04 converted.

    Processes SL_LOG-02 (4 subprocesses), SL_LOG-03 (2) and SL_LOG-04 (1) came
    from the legacy container form; they are now typed operations (40 ops — the
    35 converted operations plus 5 boundary operations added by the flow pass).
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE /
    BAD / TYPE-CARDINALITY in the scope (dangling §4.2 is the flow-graph step).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_LOG-02-01", "SL_LOG-02-02", "SL_LOG-02-03", "SL_LOG-02-04",
            "SL_LOG-03-01", "SL_LOG-03-02", "SL_LOG-04-01")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 40, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_log_flow_graph_is_closed():
    """T2.6 sub-step 3: the logistics flow graph closes every I/O.

    `SL_LOG.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    MFG/PLAN/SL_PLAN/QUAL/SL_QUAL/ENV/SL_MNT/SL_ANL/ORG seams) plus explicit
    boundary sensor/actor operations for the external supplier/customer/recycler
    perimeter. Assert the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT
    §4.5 in the SL_LOG scope, and no warnings.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["SL_LOG"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["SL_LOG"]) == [], \
        engine_filter.scoped(warns, ["SL_LOG"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_log_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 78 SL_LOG ops + domain roll-up.

    Every logistics operation (4 processes / 12 subprocesses, including the 11
    explicit boundary sensors/actors) carries the T0.5 economics block with
    in-domain values; the domain scope stays clean (0 errors / 0 warnings) and
    the SL_LOG roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("SL_LOG-")]
    assert len(ops) == 78, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["SL_LOG"]) == []

    rows = rollup.rollup_matrix(lib, scope=["SL_LOG"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 78, group
    assert group["fte"] == pytest.approx(7.848824, abs=1e-4), group
    assert group["cost"] == pytest.approx(13343000, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("SL_LOG-01", "SL_LOG-02", "SL_LOG-03", "SL_LOG-04"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["SL_LOG"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_qual_processes_are_typed_and_goaled():
    """T2.6: logistics-quality replication — all 5 processes converted.

    The whole quality-in-storage-and-transport group (5 processes / 8
    subprocesses / 26 operations — the 21 converted operations plus 5 boundary
    sensors/actors added by the flow pass) carries a goal, a valid `Тип` and
    vocabulary-typed I/O. Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT
    / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in the SL_QUAL scope (dangling §4.2 is
    closed by `test_vault_sl_qual_flow_graph_is_closed`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_QUAL-01-01", "SL_QUAL-02-01", "SL_QUAL-02-02", "SL_QUAL-03-01",
            "SL_QUAL-04-01", "SL_QUAL-04-02", "SL_QUAL-06-01", "SL_QUAL-06-02")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 26, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_qual_flow_graph_is_closed():
    """T2.6 sub-step 3: the logistics-quality flow graph closes every I/O.

    `SL_QUAL.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    QUAL/SL_LOG/MFG/SL_ANL/ORG/SL_MNT seams) plus explicit boundary sensor/actor
    operations for the standards/claims perimeter. Assert the domain gate: no
    DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the SL_QUAL scope, and no
    warnings.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["SL_QUAL"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["SL_QUAL"]) == [], \
        engine_filter.scoped(warns, ["SL_QUAL"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_qual_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 26 SL_QUAL ops + domain roll-up.

    Every logistics-quality operation (5 processes / 8 subprocesses, including the
    5 explicit boundary sensors/actors) carries the T0.5 economics block with
    in-domain values; the domain scope stays clean (0 errors / 0 warnings) and the
    SL_QUAL roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("SL_QUAL-")]
    assert len(ops) == 26, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["SL_QUAL"]) == []

    rows = rollup.rollup_matrix(lib, scope=["SL_QUAL"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 26, group
    assert group["fte"] == pytest.approx(1.2240, abs=1e-3), group
    assert group["cost"] == pytest.approx(2080750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("SL_QUAL-01", "SL_QUAL-02", "SL_QUAL-03", "SL_QUAL-04",
                 "SL_QUAL-06"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["SL_QUAL"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_mnt_processes_are_typed_and_goaled():
    """T2.6: logistics-fleet-maintenance replication — all 3 processes converted.

    The whole maintenance group (3 processes / 5 subprocesses / 12 operations —
    the 11 converted operations plus 1 boundary sensor added by the flow pass)
    carries a goal, a valid `Тип` and vocabulary-typed I/O. Assert the sub-step-2
    gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in
    the SL_MNT scope (dangling §4.2 is closed by
    `test_vault_sl_mnt_flow_graph_is_closed`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_MNT-01-01", "SL_MNT-01-02", "SL_MNT-02-01", "SL_MNT-02-02",
            "SL_MNT-03-01")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 12, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_mnt_flow_graph_is_closed():
    """T2.6 sub-step 3: the logistics-fleet flow graph closes every I/O.

    `SL_MNT.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    SL_LOG/MNT/INF/SL_ANL seams) plus one explicit boundary sensor for the
    regulator's certification requirements. Assert the domain gate: no DANGLING
    §4.2 and no CYCLE WITHOUT EXIT §4.5 in the SL_MNT scope, and no warnings.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["SL_MNT"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["SL_MNT"]) == [], \
        engine_filter.scoped(warns, ["SL_MNT"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_mnt_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 12 SL_MNT ops + domain roll-up.

    Every maintenance operation (3 processes / 5 subprocesses, including the
    boundary sensor) carries the T0.5 economics block with in-domain values; the
    domain scope stays clean (0 errors / 0 warnings) and the SL_MNT roll-up is
    finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("SL_MNT-")]
    assert len(ops) == 12, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["SL_MNT"]) == []

    rows = rollup.rollup_matrix(lib, scope=["SL_MNT"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 12, group
    assert group["fte"] == pytest.approx(0.5403, abs=1e-3), group
    assert group["cost"] == pytest.approx(918500, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("SL_MNT-01", "SL_MNT-02", "SL_MNT-03"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["SL_MNT"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_hrp_processes_are_typed_and_goaled():
    """T2.6: logistics-personnel replication — all 3 processes converted.

    The whole personnel-of-logistics group (3 processes / 5 subprocesses /
    17 operations — the 11 converted operations plus 6 boundary sensors/actors
    added by the flow pass) carries a goal, a valid `Тип` and vocabulary-typed
    I/O. Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE /
    BAD / TYPE-CARDINALITY in the SL_HRP scope (dangling §4.2 is closed by
    `test_vault_sl_hrp_flow_graph_is_closed`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_HRP-01-01", "SL_HRP-01-02", "SL_HRP-02-01", "SL_HRP-02-02",
            "SL_HRP-03-01")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 17, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_hrp_flow_graph_is_closed():
    """T2.6 sub-step 3: the logistics-personnel flow graph closes every I/O.

    `SL_HRP.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    HRP/ORG/PLAN/SL_LOG/SL_MNT seams) plus explicit boundary sensor/actor
    operations for the external labour-market / training-provider perimeter and
    the internal-standards / budget contour. Assert the domain gate: no DANGLING
    §4.2 and no CYCLE WITHOUT EXIT §4.5 in the SL_HRP scope, and no warnings.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["SL_HRP"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["SL_HRP"]) == [], \
        engine_filter.scoped(warns, ["SL_HRP"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_hrp_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 17 SL_HRP ops + domain roll-up.

    Every personnel-of-logistics operation (3 processes / 5 subprocesses,
    including the 6 boundary sensors/actors) carries the T0.5 economics block
    with in-domain values; the domain scope stays clean (0 errors / 0 warnings)
    and the SL_HRP roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("SL_HRP-")]
    assert len(ops) == 17, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["SL_HRP"]) == []

    rows = rollup.rollup_matrix(lib, scope=["SL_HRP"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 17, group
    assert group["fte"] == pytest.approx(0.042794, abs=1e-4), group
    assert group["cost"] == pytest.approx(72750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("SL_HRP-01", "SL_HRP-02", "SL_HRP-03"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["SL_HRP"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_emg_processes_are_typed_and_goaled():
    """T2.6: logistics-emergency replication — all 3 processes converted.

    The whole emergency group (3 processes / 5 subprocesses / 16 operations —
    the 11 converted operations plus 5 boundary sensors/actors added by the flow
    pass) carries a goal, a valid `Тип` and vocabulary-typed I/O. Assert the
    sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the SL_EMG scope (dangling §4.2 is closed by
    `test_vault_sl_emg_flow_graph_is_closed`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_EMG-01-01", "SL_EMG-01-02", "SL_EMG-02-01", "SL_EMG-02-02",
            "SL_EMG-03-01")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 16, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_emg_flow_graph_is_closed():
    """T2.6 sub-step 3: the logistics-emergency flow graph closes every I/O.

    `SL_EMG.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    SL_LOG/SL_QUAL/SL_ANL seams) plus explicit boundary sensor/actor operations
    for the ДТП / emergency-services / ГИБДД / insurance and client-return
    perimeter. Assert the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT
    §4.5 in the SL_EMG scope, and no warnings.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["SL_EMG"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["SL_EMG"]) == [], \
        engine_filter.scoped(warns, ["SL_EMG"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_emg_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 16 SL_EMG ops + domain roll-up.

    Every emergency operation (3 processes / 5 subprocesses, including the 5
    boundary sensors/actors) carries the T0.5 economics block with in-domain
    values; the domain scope stays clean (0 errors / 0 warnings) and the SL_EMG
    roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("SL_EMG-")]
    assert len(ops) == 16, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["SL_EMG"]) == []

    rows = rollup.rollup_matrix(lib, scope=["SL_EMG"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 16, group
    assert group["fte"] == pytest.approx(0.007059, abs=1e-4), group
    assert group["cost"] == pytest.approx(12000, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("SL_EMG-01", "SL_EMG-02", "SL_EMG-03"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["SL_EMG"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_anl_processes_are_typed_and_goaled():
    """T2.6: logistics-analytics replication — all 4 processes converted.

    The whole analytics/KPI group (4 processes / 5 subprocesses / 15 operations —
    the 12 converted operations plus 3 boundary sensors/actor added by the flow
    pass) carries a goal, a valid `Тип` and vocabulary-typed I/O. Assert the
    sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the SL_ANL scope (dangling §4.2 is closed by
    `test_vault_sl_anl_flow_graph_is_closed`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("SL_ANL-01-01", "SL_ANL-02-01", "SL_ANL-03-01", "SL_ANL-04-01",
            "SL_ANL-04-02")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 15, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_anl_flow_graph_is_closed():
    """T2.6 sub-step 3: the logistics-analytics flow graph closes every I/O.

    `SL_ANL.md` carries a «Потоки (Flow Links)» table (internal + cross-domain
    SL_LOG/SL_QUAL/SL_MNT/SL_PLAN/STRAT seams) plus explicit boundary operations
    for the ERP/accounting data feed, the transport portal / carrier contracts
    feed and the operational-management consumer of the summary report. Assert
    the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the
    SL_ANL scope, and no warnings.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["SL_ANL"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["SL_ANL"]) == [], \
        engine_filter.scoped(warns, ["SL_ANL"])


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_sl_anl_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 15 SL_ANL ops + domain roll-up.

    Every analytics/KPI operation (4 processes / 5 subprocesses, including the 3
    boundary sensors/actor) carries the T0.5 economics block with in-domain
    values; the domain scope stays clean (0 errors / 0 warnings) and the SL_ANL
    roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("SL_ANL-")]
    assert len(ops) == 15, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["SL_ANL"]) == []

    rows = rollup.rollup_matrix(lib, scope=["SL_ANL"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 15, group
    assert group["fte"] == pytest.approx(0.317353, abs=1e-4), group
    assert group["cost"] == pytest.approx(539500, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("SL_ANL-01", "SL_ANL-02", "SL_ANL-03", "SL_ANL-04"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["SL_ANL"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_process_01_is_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 1 (INF-01).

    Process INF-01 (Управление зданиями, сооружениями и прилегающей
    территорией; 5 subprocesses / 22 operations) is converted to typed
    `##### Операция` nodes. Assert the sub-step-2 gate: no MISSING GOAL /
    FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in the INF-01 scope
    (dangling §4.2 is closed by the later flow-graph pass).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-01-01", "INF-01-02", "INF-01-03", "INF-01-04", "INF-01-05")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 22, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_processes_02_to_03_are_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 2 (INF-02, INF-03).

    Processes INF-02 (Управление энергоресурсами; 5 subprocesses / 27 ops) and
    INF-03 (Управление инженерными сетями; 3 subprocesses / 11 ops) are
    converted to typed `##### Операция` nodes. Assert the sub-step-2 gate: no
    MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in the
    INF-02 / INF-03 scopes (dangling §4.2 is closed by the later flow-graph pass).
    The count below includes the flow-pass boundary op hosted in INF-02-01.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-02-01", "INF-02-02", "INF-02-03", "INF-02-04", "INF-02-05",
            "INF-03-01", "INF-03-02", "INF-03-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 39, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_processes_04_to_05_are_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 3 (INF-04, INF-05).

    Processes INF-04 (Управление грузоподъёмными механизмами; 5 subprocesses /
    24 ops) and INF-05 (Управление компрессорным и холодильным оборудованием;
    4 subprocesses / 20 ops) are converted to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE /
    BAD / TYPE-CARDINALITY in the INF-04 / INF-05 scopes (dangling §4.2 is
    closed by the later flow-graph pass).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-04-01", "INF-04-02", "INF-04-03", "INF-04-04", "INF-04-05",
            "INF-05-01", "INF-05-02", "INF-05-03", "INF-05-04")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 44, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_processes_06_to_07_are_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 4 (INF-06, INF-07).

    Processes INF-06 (Управление водоснабжением и водоотведением; 4
    subprocesses / 20 ops) and INF-07 (Управление газовым хозяйством; 4
    subprocesses / 20 ops) are converted to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE /
    BAD / TYPE-CARDINALITY in the INF-06 / INF-07 scopes (dangling §4.2 is
    closed by the later flow-graph pass).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-06-01", "INF-06-02", "INF-06-03", "INF-06-04",
            "INF-07-01", "INF-07-02", "INF-07-03", "INF-07-04")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 40, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


def test_vault_inf_processes_08_to_09_are_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 5 (INF-08, INF-09).

    Processes INF-08 (Капитальное строительство, реконструкция и модернизация;
    4 subprocesses / 20 ops) and INF-09 (Промышленная безопасность, охрана
    труда и экология; 4 subprocesses / 20 ops) are converted to typed
    `##### Операция` nodes. Assert the sub-step-2 gate: no MISSING GOAL /
    FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in the INF-08 / INF-09
    scopes (dangling §4.2 is closed by the later flow-graph pass).
    The count below includes the three flow-pass boundary ops hosted in
    INF-08-02, INF-08-04 and INF-09-03.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-08-01", "INF-08-02", "INF-08-03", "INF-08-04",
            "INF-09-01", "INF-09-02", "INF-09-03", "INF-09-04")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 43, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


def test_vault_inf_processes_10_to_11_are_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 6 (INF-10, INF-11).

    Processes INF-10 (Бюджетирование и экономика ТОиР; 3 subprocesses / 15 ops)
    and INF-11 (Управление персоналом СГИ; 4 subprocesses / 20 ops) are
    converted to typed `##### Операция` nodes. Assert the sub-step-2 gate: no
    MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in the
    INF-10 / INF-11 scopes (dangling §4.2 is closed by the flow-graph pass).
    The count below includes the flow-pass boundary op hosted in INF-10-01.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-10-01", "INF-10-02", "INF-10-03",
            "INF-11-01", "INF-11-02", "INF-11-03", "INF-11-04")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 36, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


def test_vault_inf_processes_12_to_13_are_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 7 (INF-12, INF-13).

    Processes INF-12 (Непрерывное совершенствование и повышение надёжности;
    4 subprocesses / 21 ops) and INF-13 (Стратегия развития инфраструктуры и
    управления активами; 3 subprocesses / 11 ops) are converted to typed
    `##### Операция` nodes. Assert the sub-step-2 gate: no MISSING GOAL /
    FREE-TEXT / UNKNOWN TYPE / BAD / TYPE-CARDINALITY in the INF-12 / INF-13
    scopes (dangling §4.2 is closed by the later flow-graph pass).
    The count below includes the two flow-pass boundary ops hosted in INF-12-04
    and INF-13-03.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-12-01", "INF-12-02", "INF-12-03", "INF-12-04",
            "INF-13-01", "INF-13-02", "INF-13-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 34, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_flow_graph_is_closed():
    """T2.6 sub-step 3: the infrastructure flow graph closes every I/O.

    `INF.md` carries a «Потоки (Flow Links)» table (internal INF→INF flow plus
    cross-domain seams to SL_HRP / SL_LOG / SL_QUAL / PLAN / MFG) and **11
    explicit boundary operations** (6 sensors + 5 actors for the enterprise
    perimeter: АСУТП/телеметрия, учётная база ОС, НСИ, заявители, внешний
    рынок, финансовый контур; управление, ЕРП/архив, надзор, подрядчики,
    исполнители). Assert the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT
    EXIT §4.5 in the INF scope, and no warnings; every boundary op is a sensor
    (no inputs) or an actor (no outputs).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["INF-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["INF-"]) == [], \
        engine_filter.scoped(warns, ["INF-"])

    for code in ("INF-02-01-08", "INF-14-04-06", "INF-14-01-06", "INF-13-03-04",
                 "INF-08-02-06", "INF-10-01-06"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in ("INF-12-04-06", "INF-14-04-07", "INF-09-03-06", "INF-08-04-06",
                 "INF-14-02-06"):
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_process_14_is_typed_and_goaled():
    """T2.6: infrastructure replication — tranche 8 (INF-14, final sub-step-2).

    Process INF-14 (Эксплуатация и техническое обслуживание инженерных систем;
    4 subprocesses / 21 ops) is converted to typed `##### Операция` nodes. With
    this tranche the whole `INF` domain (14 processes / 128 operations) is typed.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD
    / TYPE-CARDINALITY in the INF-14 scope (dangling §4.2 is closed by the
    later flow-graph pass). The count below includes the four flow-pass boundary
    ops hosted in INF-14-01, INF-14-02 and INF-14-04.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("INF-14-01", "INF-14-02", "INF-14-03", "INF-14-04")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 25, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_inf_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 283 INF ops + domain roll-up.

    Every infrastructure operation (14 processes / 56 subprocesses, including the
    11 flow-pass boundary sensors/actors) carries the T0.5 economics block with
    in-domain values; the domain scope stays clean (0 errors / 0 warnings) and
    the INF roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("INF-")]
    assert len(ops) == 283, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["INF-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["INF-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 283, group
    assert group["fte"] == pytest.approx(3.764706, abs=1e-4), group
    assert group["cost"] == pytest.approx(6400000, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("INF-01", "INF-02", "INF-03", "INF-04", "INF-05", "INF-06",
                 "INF-07", "INF-08", "INF-09", "INF-10", "INF-11", "INF-12",
                 "INF-13", "INF-14"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code
    procs = [by["INF-%02d" % i] for i in range(1, 15)]
    assert by["INF"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["INF-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mnt_processes_01_to_02_are_typed_and_goaled():
    """T2.6: equipment-maintenance replication — tranche 1 (MNT-01, MNT-02).

    Processes MNT-01 (Мониторинг технического состояния оборудования;
    5 subprocesses / 21 ops) and MNT-02 (Планирование ресурсов; 3 subprocesses /
    9 ops) are converted from the legacy container form to typed `##### Операция`
    nodes. Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE
    / BAD / TYPE-CARDINALITY in the MNT-01 / MNT-02 scope (dangling §4.2 is closed
    by the later flow-graph pass). The count includes the two flow-pass boundary
    ops hosted in MNT-01-03 / MNT-01-04 and the two hosted in MNT-02-01 / MNT-02-03.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("MNT-01-01", "MNT-01-02", "MNT-01-03", "MNT-01-04", "MNT-01-05",
            "MNT-02-01", "MNT-02-02", "MNT-02-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 34, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mnt_processes_03_to_07_are_typed_and_goaled():
    """T2.6: equipment-maintenance replication — tranche 2 (MNT-03..MNT-07).

    The remaining processes MNT-03 (Планирование и подготовка ТОиР; 5
    subprocesses), MNT-04 (Выполнение ТОиР; 3), MNT-05 (Контроль/анализ; 3),
    MNT-06 (Участие в переналадках; 2) and MNT-07 (Модернизация; 2) are converted
    from the legacy container form to typed `##### Операция` nodes (43 ops; the
    scope also hosts three flow-pass boundary ops → 46). Assert
    the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the MNT-03..07 scope (dangling §4.2 is closed by the
    later flow-graph pass).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("MNT-03-01", "MNT-03-02", "MNT-03-03", "MNT-03-04", "MNT-03-05",
            "MNT-04-01", "MNT-04-02", "MNT-04-03",
            "MNT-05-01", "MNT-05-02", "MNT-05-03",
            "MNT-06-01", "MNT-06-02", "MNT-07-01", "MNT-07-02")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 46, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_mnt_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 80 MNT ops + domain roll-up.

    Every equipment-maintenance operation (7 processes / 23 subprocesses, i.e. the
    73 typed ops plus the 7 flow-pass boundary sensors/actors) carries the T0.5
    economics block with in-domain values; the domain scope stays clean
    (0 errors / 0 warnings) and the MNT roll-up is finite, additive and
    cost-identical (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("MNT-")]
    assert len(ops) == 80, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["MNT-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["MNT-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 80, group
    assert group["fte"] == pytest.approx(2.961029, abs=1e-4), group
    assert group["cost"] == pytest.approx(5033750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("MNT-01", "MNT-02", "MNT-03", "MNT-04", "MNT-05", "MNT-06",
                 "MNT-07"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code
    procs = [by["MNT-%02d" % i] for i in range(1, 8)]
    assert by["MNT"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["MNT-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_eng_process_is_typed_and_goaled():
    """T2.6: technology-preparation replication — sub-step 2 (ENG-01-01..04).

    The whole `ENG` group (1 process `ENG-01` / 4 subprocesses / 15 operations)
    is converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the ENG scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the four flow-pass boundary sensors hosted in
    ENG-01-01 (two), ENG-01-03 and ENG-01-04.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("ENG-01-01", "ENG-01-02", "ENG-01-03", "ENG-01-04")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 19, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_eng_flow_graph_is_closed():
    """T2.6 sub-step 3: the technology-preparation flow graph closes every I/O.

    `ENG.md` carries a «Потоки (Flow Links)» table (internal ENG→ENG flow plus
    cross-domain seams to PLAN / MNT / IMPR / QUAL / ANLZ / ORG / STRAT / MFG /
    INF) and **4 explicit boundary sensors** (design documentation from the
    constructor/customer, the technology reference base, the measurement contour
    and the external GOST/TU standards). Assert the domain gate: no DANGLING
    §4.2 and no CYCLE WITHOUT EXIT §4.5 in the ENG scope, and no warnings; every
    boundary op is a sensor (no inputs).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["ENG-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["ENG-"]) == [], \
        engine_filter.scoped(warns, ["ENG-"])

    for code in ("ENG-01-01-06", "ENG-01-01-07", "ENG-01-03-05",
                 "ENG-01-04-04"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code

    # The MFG / PLAN cross-domain pins on the design outputs stay coherent:
    # the design operation must really emit the pinned document tokens.
    design_out = {it["raw"] for it in lib.by_code["ENG-01-01-02"].io_out}
    assert "ТехнологическаяКарта@КартаКонтроля" in design_out, design_out
    assert "СОП@Сборки" in design_out, design_out
    assert "Чертёж" in {it["raw"] for it in lib.by_code["ENG-01-01-01"].io_out}


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_eng_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 19 ENG ops + domain roll-up.

    Every technology-preparation operation (1 process / 4 subprocesses, i.e. the
    15 typed ops plus the 4 flow-pass boundary sensors) carries the T0.5
    economics block with in-domain values; the domain scope stays clean
    (0 errors / 0 warnings) and the ENG roll-up is finite, additive and
    cost-identical (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("ENG-")]
    assert len(ops) == 19, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["ENG-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["ENG-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 19, group
    assert group["fte"] == pytest.approx(0.125147, abs=1e-4), group
    assert group["cost"] == pytest.approx(212750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    subs = [by[c.code] for c in lib.by_code["ENG-01"].children if c.code in by]
    assert by["ENG-01"]["fte"] == pytest.approx(
        sum(s["fte"] for s in subs), abs=1e-3)
    assert by["ENG"]["fte"] == pytest.approx(
        by["ENG-01"]["fte"], abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["ENG-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_anlz_processes_are_typed_and_goaled():
    """T2.6: production-efficiency-analysis replication — sub-step 2 (ANLZ-01-01..07).

    The whole `ANLZ` group (1 process `ANLZ-01` / 7 subprocesses / 32 operations)
    is converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the ANLZ scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the five flow-pass boundary ops (4 sensors + 1 actor).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("ANLZ-01-01", "ANLZ-01-02", "ANLZ-01-03", "ANLZ-01-04",
            "ANLZ-01-05", "ANLZ-01-06", "ANLZ-01-07")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 37, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_anlz_flow_graph_is_closed():
    """T2.6 sub-step 3: the production-efficiency-analysis flow graph closes every I/O.

    `ANLZ.md` carries a «Потоки (Flow Links)» table (internal ANLZ→ANLZ flow plus
    cross-domain seams to PLAN / QUAL / MFG / STRAT / MNT / IMPR / HRP) and **5
    explicit boundary ops** (4 sensors: ERP/BI+NSI reference data, accounting
    actual-costs, commercial/strategy data, ОТ/5S standards; 1 actor: management).
    Assert the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the
    ANLZ scope, and no warnings; every sensor has no inputs, the actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["ANLZ-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["ANLZ-"]) == [], \
        engine_filter.scoped(warns, ["ANLZ-"])

    for code in ("ANLZ-01-01-04", "ANLZ-01-03-05", "ANLZ-01-06-08",
                 "ANLZ-01-07-06"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    actor = lib.by_code["ANLZ-01-02-05"]
    assert actor.io_out == [] and actor.io_in, "ANLZ-01-02-05"

    # The PLAN / ENG / MFG cross-domain pins on ANLZ-01-01-01 stay coherent:
    # the reporting operation must really carry the pinned tokens.
    out = {it["raw"] for it in lib.by_code["ANLZ-01-01-01"].io_out}
    inp = {it["raw"] for it in lib.by_code["ANLZ-01-01-01"].io_in}
    for tok in ("Показатель@OEE", "Показатель@Простой", "Показатель@Отклонение",
                "Показатель@ВремяПереналадки", "Отчёт@АнализОтклонений"):
        assert tok in out, (tok, out)
    for tok in ("Норматив@Расхода", "Отчёт@Аналитика"):
        assert tok in inp, (tok, inp)


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_anlz_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 37 ANLZ ops + domain roll-up.

    Every production-efficiency-analysis operation (1 process / 7 subprocesses,
    i.e. the 32 typed ops plus the 5 flow-pass boundary ops) carries the T0.5
    economics block with in-domain values; the domain scope stays clean
    (0 errors / 0 warnings) and the ANLZ roll-up is finite, additive and
    cost-identical (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("ANLZ-")]
    assert len(ops) == 37, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["ANLZ-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["ANLZ-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 37, group
    assert group["fte"] == pytest.approx(1.309265, abs=1e-4), group
    assert group["cost"] == pytest.approx(2225750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    subs = [by[c.code] for c in lib.by_code["ANLZ-01"].children if c.code in by]
    assert by["ANLZ-01"]["fte"] == pytest.approx(
        sum(s["fte"] for s in subs), abs=1e-3)
    assert by["ANLZ"]["fte"] == pytest.approx(
        by["ANLZ-01"]["fte"], abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["ANLZ-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_emg_processes_are_typed_and_goaled():
    """T2.6: unplanned-situation-management replication — sub-step 2 (EMG-01-01..03).

    The whole `EMG` group (3 processes / 9 subprocesses / 34 operations) is
    converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the EMG scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the five flow-pass boundary ops (3 sensors + 2 actors).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("EMG-01-01", "EMG-01-02", "EMG-01-03", "EMG-01-04",
            "EMG-02-01", "EMG-02-02",
            "EMG-03-01", "EMG-03-02", "EMG-03-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 39, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_emg_flow_graph_is_closed():
    """T2.6 sub-step 3: the unplanned-situation flow graph closes every I/O.

    `EMG.md` carries a «Потоки (Flow Links)» table (internal EMG→EMG flow plus
    cross-domain seams to ENG / STRAT / QUAL / MNT / HRP / ENV / IMPR) and **5
    explicit boundary ops** (3 sensors: monitoring/signal contour, emergency
    reserve + stop norms, ОТ/промбезопасность standards+passports; 2 actors:
    external emergency services, management/supervisory bodies). Assert the domain
    gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the EMG scope, and no
    warnings; every sensor has no inputs, the actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["EMG-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["EMG-"]) == [], \
        engine_filter.scoped(warns, ["EMG-"])

    for code in ("EMG-01-01-04", "EMG-01-02-05", "EMG-03-01-05"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in ("EMG-01-02-06", "EMG-01-03-05"):
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code

    # Coherence of the cross-domain seams that EMG depends on / feeds.
    out = {it["raw"] for it in lib.by_code["EMG-01-04-02"].io_out}
    for tok in ("Заказ@Ремонт", "Документ@АктОБраке",
                "Заявка@НаРасследованиеТравмы", "Заявка@ВнеплановыйМониторинг"):
        assert tok in out, (tok, out)
    inp = {it["raw"] for it in lib.by_code["EMG-03-02-01"].io_in}
    for tok in ("СОП@ДействияПриНС", "ПланПроизводства",
                "График@Учений@Актуализирован"):
        assert tok in inp, (tok, inp)


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_emg_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 39 EMG ops + domain roll-up.

    Every unplanned-situation operation (3 processes / 9 subprocesses, i.e. the 34
    typed ops plus the 5 flow-pass boundary ops) carries the T0.5 economics block
    with in-domain values; the domain scope stays clean (0 errors / 0 warnings)
    and the EMG roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("EMG-")]
    assert len(ops) == 39, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["EMG-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["EMG-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 39, group
    assert group["fte"] == pytest.approx(0.095294, abs=1e-4), group
    assert group["cost"] == pytest.approx(162000, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    procs = [by[c.code] for c in lib.by_code["EMG"].children if c.code in by]
    assert by["EMG"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["EMG-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_env_processes_are_typed_and_goaled():
    """T2.6: environmental-management replication — sub-step 2 (ENV-01..03).

    The whole `ENV` group (3 processes / 7 subprocesses / 27 operations) is
    converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the ENV scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the seven flow-pass boundary ops (4 sensors + 3
    actors).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("ENV-01-01", "ENV-01-02", "ENV-01-03",
            "ENV-02-01", "ENV-02-02",
            "ENV-03-01", "ENV-03-02")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 34, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_env_flow_graph_is_closed():
    """T2.6 sub-step 3: the environmental flow graph closes every I/O.

    `ENV.md` carries a «Потоки (Flow Links)» table (internal ENV→ENV flow plus
    cross-domain seams to ENG / STRAT / IMPR; the SL_LOG and EMG pins are kept
    coherent) and **7 explicit boundary ops** (4 sensors: FKKO/standards contour,
    permit/oversight contour, accredited laboratory, external recycler; 3 actors:
    external reporting, finance, supervisory body). Assert the domain gate: no
    DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the ENV scope, and no
    warnings; every sensor has no inputs, the actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["ENV-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["ENV-"]) == [], \
        engine_filter.scoped(warns, ["ENV-"])

    for code in ("ENV-01-01-05", "ENV-02-01-05", "ENV-02-01-06",
                 "ENV-01-03-05"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in ("ENV-01-02-05", "ENV-01-03-06", "ENV-03-02-05"):
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code

    # Coherence of the cross-domain seams that ENV depends on / feeds.
    out = {it["raw"] for it in lib.by_code["ENV-01-01-01"].io_out}
    assert "Норматив@КлассификаторОтходов" in out, out
    out = {it["raw"] for it in lib.by_code["ENV-01-01-02"].io_out}
    assert "Отходы" in out, out
    inp = {it["raw"] for it in lib.by_code["ENV-01-02-02"].io_in}
    assert "Протокол@ПриёмкиОтходов" in inp, inp
    inp = {it["raw"] for it in lib.by_code["ENV-01-03-03"].io_in}
    assert "Отходы@Отсортированы" in inp, inp
    inp = {it["raw"] for it in lib.by_code["ENV-02-02-01"].io_in}
    assert "Заявка@ВнеплановыйМониторинг" in inp, inp


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_env_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 34 ENV ops + domain roll-up.

    Every environmental-management operation (3 processes / 7 subprocesses, i.e.
    the 27 typed ops plus the 7 flow-pass boundary ops) carries the T0.5
    economics block with in-domain values; the domain scope stays clean
    (0 errors / 0 warnings) and the ENV roll-up is finite, additive and
    cost-identical (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("ENV-")]
    assert len(ops) == 34, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["ENV-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["ENV-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 34, group
    assert group["fte"] == pytest.approx(3.938353, abs=1e-4), group
    assert group["cost"] == pytest.approx(6695250, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    procs = [by[c.code] for c in lib.by_code["ENV"].children if c.code in by]
    assert by["ENV"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["ENV-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_hrp_processes_are_typed_and_goaled():
    """T2.6: production-personnel replication — sub-step 2 (HRP-01..02).

    The whole `HRP` group (2 processes / 11 subprocesses / 65 operations) is
    converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the HRP scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the six flow-pass boundary ops (3 sensors + 3 actors).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("HRP-01-01", "HRP-01-02", "HRP-01-03", "HRP-01-04",
            "HRP-01-05", "HRP-01-06", "HRP-01-07", "HRP-01-08",
            "HRP-02-01", "HRP-02-02", "HRP-02-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 71, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_hrp_flow_graph_is_closed():
    """T2.6 sub-step 3: the HRP flow graph closes every I/O.

    `HRP.md` carries a «Потоки (Flow Links)» table (internal HRP→HRP flow plus
    cross-domain seams to ENG / MNT / ANLZ / STRAT / PLAN / SL_HRP / EMG) and
    **6 explicit boundary ops** (3 sensors: external training market, involvement
    survey/HR-analytics contour, external ОТ/ПБ standards; 3 actors: finance,
    management, state labour inspectorate). Assert the domain gate: no DANGLING
    §4.2 and no CYCLE WITHOUT EXIT §4.5 in the HRP scope, and no warnings; every
    sensor has no inputs, the actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["HRP-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["HRP-"]) == [], \
        engine_filter.scoped(warns, ["HRP-"])

    for code in ("HRP-01-02-07", "HRP-01-06-05", "HRP-02-02-06"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in ("HRP-01-04-06", "HRP-01-06-06", "HRP-02-03-06"):
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code

    # Coherence of the cross-domain seams that HRP depends on / feeds.
    out = {it["raw"] for it in lib.by_code["HRP-01-05-01"].io_out}
    assert "Документ@СписокНовыхСотрудников" in out, out
    out = {it["raw"] for it in lib.by_code["HRP-01-03-07"].io_out}
    assert "Сотрудник@Квалификация" in out, out
    out = {it["raw"] for it in lib.by_code["HRP-01-01-06"].io_out}
    assert "Документ@RACI" in out, out
    out = {it["raw"] for it in lib.by_code["HRP-01-04-02"].io_out}
    assert "Документ@ДолжностнаяИнструкция" in out, out
    inp = {it["raw"] for it in lib.by_code["HRP-01-05-01"].io_in}
    assert "Сотрудник@Ознакомлен" in inp, inp
    inp = {it["raw"] for it in lib.by_code["HRP-01-03-04"].io_in}
    assert "Сотрудник@Аттестован" in inp, inp
    inp = {it["raw"] for it in lib.by_code["HRP-02-01-01"].io_in}
    assert "Отчёт@УстранениеЗамечаний" in inp, inp
    inp = {it["raw"] for it in lib.by_code["HRP-02-03-01"].io_in}
    assert "Заявка@НаРасследованиеТравмы" in inp, inp
    inp = {it["raw"] for it in lib.by_code["HRP-01-01-01"].io_in}
    assert "ЗаявкаНаОбучение" in inp, inp


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_hrp_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 71 HRP ops + domain roll-up.

    Every production-personnel operation (2 processes / 11 subprocesses, i.e. the
    65 typed ops plus the 6 flow-pass boundary ops) carries the T0.5 economics
    block with in-domain values; the domain scope stays clean (0 errors /
    0 warnings) and the HRP roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("HRP-")]
    assert len(ops) == 71, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["HRP-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["HRP-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 71, group
    assert group["fte"] == pytest.approx(1.214118, abs=1e-4), group
    assert group["cost"] == pytest.approx(2064000, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    procs = [by[c.code] for c in lib.by_code["HRP"].children if c.code in by]
    assert by["HRP"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["HRP-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_impr_processes_are_typed_and_goaled():
    """T2.6: continuous-improvement replication — sub-step 2 (IMPR-01..03).

    The whole `IMPR` group (3 processes / 10 subprocesses / 36 operations) is
    converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the IMPR scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the three flow-pass boundary ops (2 sensors + 1 actor).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("IMPR-01-01", "IMPR-01-02", "IMPR-01-03", "IMPR-01-04",
            "IMPR-02-01", "IMPR-02-02", "IMPR-02-03",
            "IMPR-03-01", "IMPR-03-02", "IMPR-03-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 39, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_impr_flow_graph_is_closed():
    """T2.6 sub-step 3: the IMPR flow graph closes every I/O.

    `IMPR.md` carries a «Потоки (Flow Links)» table (internal IMPR→IMPR flow plus
    cross-domain seams to PLAN / QUAL / ANLZ / EMG / ENV / ENG / HRP) and **3
    explicit boundary ops** (2 sensors: the employee idea feed, the external
    benchmarking sources; 1 actor: the corporate-media recognition channel).
    Assert the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the
    IMPR scope, and no warnings; every sensor has no inputs, the actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["IMPR-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["IMPR-"]) == [], \
        engine_filter.scoped(warns, ["IMPR-"])

    for code in ("IMPR-01-01-04", "IMPR-03-02-04"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    op = lib.by_code["IMPR-01-03-04"]
    assert op.io_out == [] and op.io_in, op.code

    # Coherence of the cross-domain seams that IMPR depends on / feeds.
    out = {it["raw"] for it in lib.by_code["IMPR-01-01-01"].io_out}
    assert "Документ@Рацпредложение" in out, out
    out = {it["raw"] for it in lib.by_code["IMPR-02-03-04"].io_out}
    assert "Отчёт@СтатусПроектов" in out, out
    inp = {it["raw"] for it in lib.by_code["IMPR-02-01-02"].io_in}
    for tok in ("План@КорректирующихМероприятий", "Отчёт@ЗакрытиеУзкогоМеста",
                "Документ@ПланVSM", "Документ@ОтчётАктуализацииVSM",
                "План@КорректирующихМероприятий@Утверждён",
                "План@МероприятийПоУстранению"):
        assert tok in inp, (tok, inp)
    inp = {it["raw"] for it in lib.by_code["IMPR-01-01-01"].io_in}
    for tok in ("Документ@ПредложениеПоУлучшению", "Отчёт@УстранениеЗамечаний",
                "План@ПредупреждающихМероприятий"):
        assert tok in inp, (tok, inp)
    inp = {it["raw"] for it in lib.by_code["IMPR-03-01-01"].io_in}
    assert "Отчёт@Утверждён" in inp and "Отчёт@Качество" in inp, inp


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_impr_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 39 IMPR ops + domain roll-up.

    Every continuous-improvement operation (3 processes / 10 subprocesses, i.e. the
    36 typed ops plus the 3 flow-pass boundary ops) carries the T0.5 economics
    block with in-domain values; the domain scope stays clean (0 errors /
    0 warnings) and the IMPR roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("IMPR-")]
    assert len(ops) == 39, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["IMPR-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["IMPR-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 39, group
    assert group["fte"] == pytest.approx(0.394853, abs=1e-4), group
    assert group["cost"] == pytest.approx(671250, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    procs = [by[c.code] for c in lib.by_code["IMPR"].children if c.code in by]
    assert by["IMPR"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["IMPR-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_qual_processes_are_typed_and_goaled():
    """T2.6: quality-management replication — sub-step 2 (QUAL-01..09).

    The whole `QUAL` group (9 processes / 29 subprocesses / 147 operations) is
    converted from the legacy container form to typed `##### Операция` nodes
    (172 operations in the group once the flow pass adds 25 boundary ops).
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY / POSSIBLE DUPLICATE in the QUAL scope (dangling §4.2 is
    closed by the flow-graph pass), and the cross-domain pins on the exact op
    codes keep their tokens.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("QUAL-01-01", "QUAL-01-02", "QUAL-01-03",
            "QUAL-02-01",
            "QUAL-03-01", "QUAL-03-02", "QUAL-03-03", "QUAL-03-04",
            "QUAL-03-05", "QUAL-03-06",
            "QUAL-04-01",
            "QUAL-05-01", "QUAL-05-02", "QUAL-05-03", "QUAL-05-04", "QUAL-05-05",
            "QUAL-06-01", "QUAL-06-02", "QUAL-06-03",
            "QUAL-07-01", "QUAL-07-02", "QUAL-07-03", "QUAL-07-04",
            "QUAL-08-01", "QUAL-08-02", "QUAL-08-03",
            "QUAL-09-01", "QUAL-09-02", "QUAL-09-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    # 147 typed operations + the 25 flow-pass boundary ops hosted in the group.
    assert len(ops) == 172, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY", "POSSIBLE DUPLICATE"))]
    assert bad == [], bad

    # Cross-domain pins owned by other domains on these exact op codes.
    def inp(code):
        return {it["raw"] for it in lib.by_code[code].io_in}

    def outp(code):
        return {it["raw"] for it in lib.by_code[code].io_out}

    assert "Норматив@ВходногоКонтроля" in inp("QUAL-03-01-01")
    assert "Заявка@ВходнойКонтроль" in inp("QUAL-03-01-04")
    assert "Норматив@ВходногоКонтроля" in outp("QUAL-03-01-04")
    assert "Сырьё@Проба" in inp("QUAL-03-01-05")
    assert "Протокол@Испытаний" in outp("QUAL-03-01-08")
    assert "Паспорт" in outp("QUAL-03-05-02")
    assert "Отчёт@Качество" in outp("QUAL-03-03-04")
    assert "Протокол@Расхождений" in inp("QUAL-05-01-01")
    assert "Уведомление@Несоответствие" in outp("QUAL-05-01-01")
    assert "Разрешение@НаИспользованиеСырья" in outp("QUAL-05-01-03")
    assert "Документ@АктОБраке" in inp("QUAL-05-02-01")
    assert "Протокол@Брак" in outp("QUAL-05-02-01")
    assert "Партия@Карантин" in inp("QUAL-05-02-06")
    assert "Протокол@ОсмотраГП" in inp("QUAL-05-03-01")
    assert "Уведомление@НСП" in inp("QUAL-05-04-01")


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_qual_flow_graph_is_closed():
    """T2.6 sub-step 3: the QUAL flow graph closes every I/O.

    `QUAL.md` carries a «Потоки (Flow Links)» table (internal QUAL→QUAL flow plus
    cross-domain seams to ENG / MFG / SL_LOG / SL_QUAL / SL_PLAN / PLAN / MNT /
    HRP / IMPR / EMG / SL_ANL and the STRAT forward seam) and **25 explicit
    boundary ops** (10 sensors: external normative/legislation contour, external
    customer and SMK initiators, asset/stock registry, production programme, HRP
    personnel data, supplier source documents, certification/labs reference, NSP
    sources, analysis inputs, QMS documentation base; 15 actors: finance and
    procurement, ЦСМ, HRP training, quality-service operating documents,
    management reporting, production contour, sales and warehouse, УСИС/АИЛ
    dispatch, SL_LOG logistics, supplier claims, NSP actions, customer/recall,
    investigation commission, audit group, QMS archive). Assert the domain gate:
    no DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the QUAL scope, and no
    warnings; every sensor has no inputs, every actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["QUAL-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["QUAL-"]) == [], \
        engine_filter.scoped(warns, ["QUAL-"])

    sensors = ("QUAL-01-01-06", "QUAL-01-01-07", "QUAL-01-02-05",
               "QUAL-01-03-07", "QUAL-02-01-07", "QUAL-03-01-09",
               "QUAL-04-01-07", "QUAL-05-01-05", "QUAL-06-01-08",
               "QUAL-08-01-05")
    actors = ("QUAL-01-02-06", "QUAL-01-03-08", "QUAL-02-01-08",
              "QUAL-02-01-09", "QUAL-02-01-10", "QUAL-03-01-10",
              "QUAL-03-05-04", "QUAL-04-01-08", "QUAL-04-01-09",
              "QUAL-05-01-06", "QUAL-05-02-08", "QUAL-05-04-12",
              "QUAL-06-02-05", "QUAL-07-02-05", "QUAL-08-02-05")
    for code in sensors:
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in actors:
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code

    qual_links = [lk for lk in lib.links if lk["src"].startswith("QUAL-")
                  or lk["dst"].startswith("QUAL-")]
    assert len(qual_links) >= 400, len(qual_links)

    def inp(code):
        return {it["raw"] for it in lib.by_code[code].io_in}

    def outp(code):
        return {it["raw"] for it in lib.by_code[code].io_out}

    assert "Разрешение@НаИспользованиеСырья" in outp("QUAL-05-01-03")
    assert "Сырьё@Проба" in inp("QUAL-03-01-05")
    assert "График@Отпусков" in outp("QUAL-02-01-01")
    assert "График@Аттестации" in outp("QUAL-01-03-02")
    assert "ПланПроизводства" in inp("QUAL-02-01-01")
    assert "ТехнологическаяКарта" in inp("QUAL-03-03-02")


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_qual_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 172 QUAL ops + domain roll-up.

    Every quality-management operation (9 processes / 29 subprocesses, i.e. the
    147 typed ops plus the 25 flow-pass boundary ops) carries the T0.5 economics
    block with in-domain values; the domain scope stays clean (0 errors /
    0 warnings) and the QUAL roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("QUAL-")]
    assert len(ops) == 172, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["QUAL-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["QUAL-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 172, group
    assert group["fte"] == pytest.approx(2.560471, abs=1e-4), group
    assert group["cost"] == pytest.approx(4352750, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    procs = [by[c.code] for c in lib.by_code["QUAL"].children if c.code in by]
    assert by["QUAL"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["QUAL-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_org_processes_are_typed_and_goaled():
    """T2.6: organization-and-labour replication — sub-step 2 (ORG-01..02).

    The whole `ORG` group (2 processes / 6 subprocesses / 25 operations) is
    converted from the legacy container form to typed `##### Операция` nodes.
    Assert the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the ORG scope (dangling §4.2 is closed by the flow-graph
    pass). The count includes the thirteen flow-pass boundary ops (7 sensors + 6
    actors).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("ORG-01-01", "ORG-01-02", "ORG-01-03", "ORG-01-04",
            "ORG-02-01", "ORG-02-02")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 38, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    scoped = engine_filter.scoped(errs + warns, list(subs))
    bad = [m for m in scoped
           if m.startswith(("MISSING GOAL", "FREE-TEXT", "UNKNOWN TYPE", "BAD ",
                            "TYPE-CARDINALITY"))]
    assert bad == [], bad


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_org_flow_graph_is_closed():
    """T2.6 sub-step 3: the organization flow graph closes every I/O.

    `ORG.md` carries a «Потоки (Flow Links)» table (internal ORG→ORG flow plus
    cross-domain seams from ENG / STRAT / MNT; the pins owned by PLAN / HRP /
    SL_LOG / SL_QUAL / MFG / SL_HRP are kept coherent) and **13 explicit boundary
    ops** (7 sensors: OSH/5S/visualization normative base, regime handbook +
    time-study schedule, layout contour, zone-state measurement, best-practice /
    legislation contour, personnel & production calendar, attendance/HR orders;
    6 actors: archive/management records, updated technocards, intra-shop
    organization records, visualization approval, HRP familiarization, payroll
    contour). Assert the domain gate: no DANGLING §4.2 and no CYCLE WITHOUT EXIT
    §4.5 in the ORG scope, and no warnings; every sensor has no inputs, the actor
    no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["ORG-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["ORG-"]) == [], \
        engine_filter.scoped(warns, ["ORG-"])

    for code in ("ORG-01-01-05", "ORG-01-02-04", "ORG-01-03-05", "ORG-01-03-06",
                 "ORG-01-04-06", "ORG-02-01-07", "ORG-02-02-04"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    for code in ("ORG-01-01-06", "ORG-01-02-05", "ORG-01-03-07", "ORG-01-04-07",
                 "ORG-02-01-08", "ORG-02-02-05"):
        op = lib.by_code[code]
        assert op.io_out == [] and op.io_in, code

    # Coherence of the cross-domain pins that ORG emits / consumes.
    out = {it["raw"] for it in lib.by_code["ORG-01-02-01"].io_out}
    assert "Норматив@ВремяЦикла" in out, out
    out = {it["raw"] for it in lib.by_code["ORG-01-02-02"].io_out}
    assert "Норматив@НормыТруда" in out, out
    out = {it["raw"] for it in lib.by_code["ORG-01-02-03"].io_out}
    assert "Норматив@ВремяПереналадки" in out, out
    inp = {it["raw"] for it in lib.by_code["ORG-01-04-03"].io_in}
    for tok in ("Протокол@КонтроляУсловий", "Уведомление@НарушениеРежима",
                "Документ@ЖурналНарушений", "СОП", "СОП@Актуализирован"):
        assert tok in inp, (tok, inp)
    inp = {it["raw"] for it in lib.by_code["ORG-02-01-01"].io_in}
    assert "Документ@ШтатноеРасписание@Проект" in inp, inp
    assert "График@Сменности" in inp, inp
    inp = {it["raw"] for it in lib.by_code["ORG-02-02-02"].io_in}
    assert "Документ@ПриказОВзыскании" in inp, inp
    inp = {it["raw"] for it in lib.by_code["ORG-01-02-01"].io_in}
    assert "Норматив@НормыВремени" in inp, inp


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_org_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 38 ORG ops + domain roll-up.

    Every organization/labour operation (2 processes / 6 subprocesses, i.e. the 25
    typed ops plus the 13 flow-pass boundary ops) carries the T0.5 economics block
    with in-domain values; the domain scope stays clean (0 errors / 0 warnings)
    and the ORG roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("ORG-")]
    assert len(ops) == 38, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["ORG-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["ORG-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 38, group
    assert group["fte"] == pytest.approx(2.727353, abs=1e-4), group
    assert group["cost"] == pytest.approx(4636500, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    for code in ("ORG-01", "ORG-02"):
        kids = [by[c.code] for c in lib.by_code[code].children if c.code in by]
        assert by[code]["fte"] == pytest.approx(
            sum(k["fte"] for k in kids), abs=1e-3), code
    procs = [by[c.code] for c in lib.by_code["ORG"].children if c.code in by]
    assert by["ORG"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["ORG-"]) == rows


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_strat_is_typed_and_goaled():
    """T2.6: strategic-planning replication — sub-step 2 (STRAT-01..03).

    The `STRAT` group (1 process / 3 subprocesses / 10 operations) is converted
    from the legacy container form to typed `##### Операция` nodes; the
    flow-graph pass adds six boundary operations (5 sensors + 1 actor). Assert
    the sub-step-2 gate: no MISSING GOAL / FREE-TEXT / UNKNOWN TYPE / BAD /
    TYPE-CARDINALITY in the STRAT scope, and the whole domain scope is clean.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    subs = ("STRAT-01-01", "STRAT-01-02", "STRAT-01-03")
    ops = [c for s in subs for c in lib.by_code[s].children
           if c.level == "OPERATION"]
    assert len(ops) == 16, [o.code for o in ops]
    for op in ops:
        assert op.goal(), f"missing goal on {op.code}"
        assert op.io_in or op.io_out, op.code
        assert engine.aget(op.attrs, "Тип") in engine.VALID_OP_TYPES, op.code
        for it in op.io_in + op.io_out:
            assert it["kind"] == "ref", f"free-text I/O on {op.code}: {it['raw']}"

    assert engine_filter.scoped(errs + warns, ["STRAT-"]) == []


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_strat_flow_graph_is_closed():
    """T2.6 sub-step 3: the strategic-planning flow graph closes every I/O.

    `STRAT.md` carries a «Потоки (Flow Links)» table (internal STRAT→STRAT flow
    plus cross-domain seams to/from ORG / ENG / MNT / ANLZ / IMPR / HRP; the pins
    owned by ENG / SL_PLAN / ANLZ are kept coherent) and **6 explicit boundary
    ops** (5 sensors: external strategic contour, reference-normative contour,
    planning-economic contour, budget-committee protocol, process registry; 1
    actor: management / strategic committee). Assert the domain gate: no
    DANGLING §4.2 and no CYCLE WITHOUT EXIT §4.5 in the STRAT scope, and no
    warnings; every sensor has no inputs, the actor no outputs.
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    scoped = engine_filter.scoped(errs, ["STRAT-"])
    dangling = [m for m in scoped if m.startswith("DANGLING")]
    cycles = [m for m in errs if m.startswith("CYCLE WITHOUT EXIT")]
    assert dangling == [], dangling
    assert cycles == [], cycles
    assert engine_filter.scoped(warns, ["STRAT-"]) == [], \
        engine_filter.scoped(warns, ["STRAT-"])

    for code in ("STRAT-01-01-02", "STRAT-01-01-03", "STRAT-01-02-04",
                 "STRAT-01-02-05", "STRAT-01-03-07"):
        op = lib.by_code[code]
        assert op.io_in == [] and op.io_out, code
    op = lib.by_code["STRAT-01-03-08"]
    assert op.io_out == [] and op.io_in, op.code

    # Coherence of the cross-domain pins that STRAT emits / consumes.
    out = {it["raw"] for it in lib.by_code["STRAT-01-01-01"].io_out}
    assert "ПланПроизводства" in out, out
    inp = {it["raw"] for it in lib.by_code["STRAT-01-01-01"].io_in}
    for tok in ("СвободнаяЁмкостьСклада", "ЛогистическиеОграничения",
                "Норматив@Расхода", "Норматив@НормыТруда"):
        assert tok in inp, (tok, inp)
    out = {it["raw"] for it in lib.by_code["STRAT-01-02-03"].io_out}
    assert "Бюджет@Утверждён" in out, out
    inp = {it["raw"] for it in lib.by_code["STRAT-01-02-03"].io_in}
    assert "Бюджет@Откорректирован" in inp, inp
    inp = {it["raw"] for it in lib.by_code["HRP-01-04-03"].io_in}
    assert "Документ@ИндивидуальныеKPI" in inp, inp


@pytest.mark.skipif(not os.path.isdir(os.path.join(VAULT, "library")),
                    reason="vault not present")
def test_vault_strat_economics_complete_and_rolls_up():
    """T2.6 sub-steps 4-5: full economics on all 16 STRAT ops + domain roll-up.

    Every strategic-planning operation (1 process / 3 subprocesses, i.e. the 10
    typed ops plus the 6 flow-pass boundary ops) carries the T0.5 economics block
    with in-domain values; the domain scope stays clean (0 errors / 0 warnings)
    and the STRAT roll-up is finite, additive and cost-identical
    (`Cost = Hours × REF_RATE = FTE × AnnualFund × REF_RATE`).
    """
    import engine_filter
    lib = engine.parse_paths(os.path.join(VAULT, "library"))
    vocab = engine.load_vocabulary(
        os.path.join(VAULT, "specs", "T0.3-entity-state-vocabulary.md"))
    errs, warns = engine.validate(lib, vocab)

    ops = [n for n in engine._iter_nodes(lib)
           if n.level == "OPERATION" and n.code.startswith("STRAT-")]
    assert len(ops) == 16, len(ops)
    for n in ops:
        for key in ("Критичность", "Периодичность", "Трудоёмкость",
                    "Стоимость", "decomposition"):
            assert engine.aget(n.attrs, key), f"{n.code}: missing {key}"
        assert n.attrs["Критичность"] in engine.VALID_CRITICALITY, n.code
        assert n.attrs["decomposition"] in engine.VALID_DECOMPOSITION, n.code
        assert engine.PERIODICITY_RE.match(n.attrs["Периодичность"]), n.code
        assert engine.LABOUR_RE.match(n.attrs["Трудоёмкость"]), n.code
        assert engine.COST_RE.match(n.attrs["Стоимость"]), n.code

    assert engine_filter.scoped(errs + warns, ["STRAT-"]) == []

    rows = rollup.rollup_matrix(lib, scope=["STRAT-"])
    by = {r["code"]: r for r in rows}
    group = rollup.totals(rows, "GROUP")
    assert group["ops"] == 16, group
    assert group["fte"] == pytest.approx(0.0556, abs=1e-3), group
    assert group["cost"] == pytest.approx(94500, abs=1.0), group

    # identity + additivity at every level.
    for r in rows:
        assert r["cost"] == pytest.approx(r["hours"] * rollup.REF_RATE,
                                          abs=1.0), r
        assert r["cost"] == pytest.approx(
            r["fte"] * rollup.ANNUAL_FUND * rollup.REF_RATE, abs=2.0), r
    procs = [by[c.code] for c in lib.by_code["STRAT"].children if c.code in by]
    assert by["STRAT"]["fte"] == pytest.approx(
        sum(p["fte"] for p in procs), abs=1e-3)

    # determinism.
    assert rollup.rollup_matrix(lib, scope=["STRAT-"]) == rows
