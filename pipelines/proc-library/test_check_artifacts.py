"""Tests for check_artifacts.py (artifact-chain checker, plan 1791810263662).

Run:  python -m pytest -q -p no:cacheprovider   (from pipelines/proc-library)
"""
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_artifacts as ca  # noqa: E402

REG = ca.load_registry()
CODES = REG["codes"]

LIB_FIXTURE = """# Библиотека фикстуры
**Цель библиотеки:** тестовый контур.
## Группа TST: Тестовая группа
**Цель группы:** показать конвенцию.
### Процесс TST-01: Процесс один
**Цель:** провести поток.
**APQC:** 4.0
**Владелец:** Руководитель производства
#### Подпроцесс TST-01-01: Подпроцесс
**Цель:** зафиксировать.
**Владелец:** Руководитель производства
##### Операция TST-01-01-01: Операция
- **Тип:** `Simple`
- **Цель:** зафиксировать
- **Исполнитель:** Начальник смены
- **Входы:** —
- **Выходы:** `Протокол`
### Процесс TST-02: Процесс два
**Цель:** провести поток.
**APQC:** 4.0
**Владелец:** Главный технолог
##### Операция TST-02-01-01: Операция
- **Тип:** `Simple`
- **Цель:** оформить
- **Исполнитель:** Главный технолог
- **Входы:** —
- **Выходы:** `Протокол`
"""


def ktk(role_code, role_name, rows, extra=""):
    lines = ["---", "artifact: ktk", f"roles: [{role_code}]", "---", "",
             f"## {role_name} ({role_code})", "",
             "| № | Код процесса | Роль | keystone | Критический выход | "
             "KPI/критерий | Частота контроля | Источник данных | Критичность | "
             "Обоснование keystone |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    if extra:
        lines += ["", extra]
    return "\n".join(lines) + "\n"


def ktk_row(n, code, role, key, crit, kpi="ориентир (100)", just="обоснование"):
    return [str(n), code, role, key, "выход", kpi, "ежемесячно", "источник",
            crit, just]


def matrix(sections, roles=None):
    roles = roles if roles is not None else CODES
    lines = ["---", "artifact: priority-matrix",
             f"roles: [{', '.join(roles)}]", "---", ""]
    for role_code, role_name, rows in sections:
        lines += [f"## {role_name} ({role_code})", "",
                  "| Квадрант | Задача | Тип | Делегирование | "
                  "Профилактика / автоматизация | Связанный процесс (код) |",
                  "| --- | --- | --- | --- | --- | --- |"]
        lines += ["| " + " | ".join(r) + " |" for r in rows]
        lines += [""]
    return "\n".join(lines) + "\n"


def grid(sections, roles=None):
    roles = roles if roles is not None else CODES
    lines = ["---", "artifact: event-grid",
             f"roles: [{', '.join(roles)}]", "---", ""]
    for heading, rows in sections:
        lines += [f"### {heading}", "",
                  "| Триггер/Период | Событие | Длительность | Владелец | "
                  "Участники | Повестка | Вход | Выход | Процессы | Горизонт |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        lines += ["| " + " | ".join(r) + " |" for r in rows]
        lines += [""]
    return "\n".join(lines) + "\n"


def grid_row(hl, event, owner, horizon, codes="TST-01"):
    return [hl, event, "30 мин", owner, "участники", "повестка", "вход", "выход",
            codes, horizon]


def build_vault(files):
    """files: dict relpath -> text, under library/. Returns vault path."""
    d = tempfile.mkdtemp()
    for rel, text in files.items():
        fp = os.path.join(d, "library", *rel.split("/"))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(text)
    return d


def run(vault, cross=False, semantic=False):
    return ca.run(vault, cross=cross, semantic=semantic)


# --- structure -------------------------------------------------------------
def test_structure_ok_ktk():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "TST-01", "Владелец", "да", "high")]),
    })
    res = run(v)
    assert res["errors"] == [], res["errors"]


def test_bad_header_is_hard():
    txt = ktk("РП", "Руководитель производства",
              [ktk_row(1, "TST-01", "Владелец", "да", "high")])
    txt = txt.replace("KPI/критерий", "KPI")  # break the exact header
    v = build_vault({"TST.md": LIB_FIXTURE, "artifacts/КТК/ТСТ_КТК.md": txt})
    res = run(v)
    assert any("no КТК table" in e for e in res["errors"]), res["errors"]


def test_unknown_code_h2():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "TST-99", "Владелец", "да", "high")]),
    })
    res = run(v)
    assert any("H2" in e and "TST-99" in e for e in res["errors"]), res["errors"]


def test_missing_code_h7():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "—", "Владелец", "да", "high")]),
    })
    res = run(v)
    assert any("H7" in e for e in res["errors"]), res["errors"]


def test_h5_keystone_and_criticality():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "TST-01", "Владелец", "yes", "critical")]),
    })
    res = run(v)
    h5 = [e for e in res["errors"] if "H5" in e]
    assert len(h5) == 2, res["errors"]


def test_h6_stopword():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "TST-01", "Владелец", "да", "high")],
            extra="Основание: ФРПС, регламент холдинга."),
    })
    res = run(v)
    assert any("H6" in e for e in res["errors"]), res["errors"]


def test_unknown_role_h1a():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "ХХ", "Неизвестная роль",
            [ktk_row(1, "TST-01", "Владелец", "да", "high")]),
    })
    res = run(v)
    assert any("H1a" in e and "ХХ" in e for e in res["errors"]), res["errors"]


def test_missing_roles_frontmatter_h1b():
    txt = ktk("РП", "Руководитель производства",
              [ktk_row(1, "TST-01", "Владелец", "да", "high")])
    txt = txt.replace("roles: [РП]\n", "")  # break the T4.9 §2 contract
    v = build_vault({"TST.md": LIB_FIXTURE, "artifacts/КТК/ТСТ_КТК.md": txt})
    res = run(v)
    assert any("H1b" in e for e in res["errors"]), res["errors"]


# --- grid horizons ---------------------------------------------------------
def test_grid_h3_h4():
    secs = [("Ежедневные события",
             [grid_row("08:00", "планёрка", "Руководитель производства", "day")])]
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/Сетка_регулярных_событий.md": grid(secs)})
    res = run(v)
    assert res["errors"] == [], res["errors"]

    secs_bad = [("Ежедневные события",
                 [grid_row("08:00", "планёрка", "Руководитель производства",
                           "month")])]
    v2 = build_vault({"TST.md": LIB_FIXTURE,
                      "artifacts/Сетка_регулярных_событий.md": grid(secs_bad)})
    res2 = run(v2)
    assert any("H4" in e for e in res2["errors"]), res2["errors"]

    secs_empty = [("Ежедневные события",
                   [grid_row("08:00", "планёрка", "Руководитель производства", "")])]
    v3 = build_vault({"TST.md": LIB_FIXTURE,
                      "artifacts/Сетка_регулярных_событий.md": grid(secs_empty)})
    res3 = run(v3)
    assert any("H3" in e for e in res3["errors"]), res3["errors"]


# --- cross -----------------------------------------------------------------
def _full_vault():
    files = {"TST.md": LIB_FIXTURE}
    for code in CODES:
        name = next(r["name"] for r in REG["roles"] if r["code"] == code)
        files[f"artifacts/КТК/{code}_КТК.md"] = ktk(
            code, name, [ktk_row(1, "TST-01", "Владелец", "да", "high")])
    sections = []
    for code in CODES:
        name = next(r["name"] for r in REG["roles"] if r["code"] == code)
        sections.append((code, name,
                         [["Срочно и важно", "задача", "регулярная", "—",
                           "—", "TST-01"]]))
    files["artifacts/Приоритеты_руководителей.md"] = matrix(sections)
    files["artifacts/Сетка_регулярных_событий.md"] = grid(
        [("Ежедневные события",
          [grid_row("08:00", "планёрка", "Руководитель производства", "day")])])
    return build_vault(files)


def test_cross_h1_ok():
    res = run(_full_vault(), cross=True)
    assert not any("H1" in e for e in res["errors"]), res["errors"]


def test_cross_h1_missing_kind():
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/Сетка_регулярных_событий.md": grid(
                         [("Ежедневно", [grid_row("08:00", "планёрка",
                                                  "Руководитель производства",
                                                  "day")])])})
    res = run(v, cross=True)
    assert any("missing" in e for e in res["errors"]), res["errors"]


def test_cross_h1_partial_roles():
    v = _full_vault()
    # drop one КТК file -> union no longer equals register
    p = os.path.join(v, "library", "artifacts", "КТК", f"{CODES[0]}_КТК.md")
    os.remove(p)
    res = run(v, cross=True)
    assert any("H1" in e and "missing" in e for e in res["errors"]), res["errors"]


def test_w2_owner_mismatch():
    secs = [("Ежедневные события",
             [grid_row("08:00", "планёрка", "Руководитель производства", "day",
                       codes="TST-02")])]
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/Сетка_регулярных_событий.md": grid(secs)})
    res = run(v, cross=True)
    assert any("W2" in w for w in res["warnings"]), res["warnings"]


def test_w6_duplicate():
    files = {"TST.md": LIB_FIXTURE,
             "artifacts/КТК/РП_КТК.md": ktk(
                 "РП", "Руководитель производства",
                 [ktk_row(1, "TST-01", "Владелец", "да", "high"),
                  ktk_row(2, "TST-01", "Владелец", "да", "high")])}
    v = build_vault(files)
    res = run(v, cross=True)
    assert any("W6" in w for w in res["warnings"]), res["warnings"]


# --- semantic --------------------------------------------------------------
def test_w3_matrix_delegation():
    sections = [("РП", "Руководитель производства",
                 [["Срочно, но не важно", "задача", "регулярная", "",
                   "—", "TST-01"]])]
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/Приоритеты_руководителей.md": matrix(sections,
                                                                     roles=["РП"])})
    res = run(v, semantic=True)
    assert any("W3" in w for w in res["warnings"]), res["warnings"]


def test_w4_w5_semantic():
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/РП_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "TST-01", "Владелец", "да", "high",
                     kpi="≥95%", just="")]),
    })
    res = run(v, semantic=True)
    assert any("W4" in w for w in res["warnings"]), res["warnings"]
    assert any("W5" in w for w in res["warnings"]), res["warnings"]


def test_registry_is_ten_and_agrees():
    assert len(CODES) == 10
    assert len(set(CODES)) == 10


def test_registry_codes_match_spec():
    spec = os.path.join(os.path.dirname(ca.__file__), "specs",
                        "T4.0-role-archetypes.md")
    text = open(spec, encoding="utf-8").read()
    spec_codes = re.findall(r"^\|\s*([А-ЯЁA-Z]{2})\s*\|", text, re.M)
    assert set(spec_codes) == set(CODES), (spec_codes, CODES)


# --- H2/H7 for matrix and grid --------------------------------------------
def test_matrix_h2_h7():
    sections = [("РП", "Руководитель производства",
                 [["Срочно и важно", "задача", "регулярная", "—", "—", "TST-99"],
                  ["Срочно и важно", "задача 2", "регулярная", "—", "—", "—"]])]
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/Приоритеты_руководителей.md":
                         matrix(sections, roles=["РП"])})
    res = run(v)
    assert any("H2" in e and "TST-99" in e for e in res["errors"]), res["errors"]
    assert any("H7" in e for e in res["errors"]), res["errors"]


def test_grid_h2():
    secs = [("Ежедневные события",
             [grid_row("08:00", "планёрка", "Руководитель производства", "day",
                       codes="TST-99")])]
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/Сетка_регулярных_событий.md": grid(secs)})
    res = run(v)
    assert any("H2" in e and "TST-99" in e for e in res["errors"]), res["errors"]


# --- H6 identity edges -----------------------------------------------------
def test_h6_identity_person():
    v = build_vault({"TST.md": LIB_FIXTURE,
                     "artifacts/КТК/ТСТ_КТК.md": ktk(
                         "РП", "Руководитель производства",
                         [ktk_row(1, "TST-01", "Владелец", "да", "high")],
                         extra="Куратор: И. И. Иванов.")})
    res = run(v)
    assert any("H6" in e and "person-name" in e for e in res["errors"]), res["errors"]


def test_h6_oriented_money_allowed():
    good = ktk("РП", "Руководитель производства",
               [ktk_row(1, "TST-01", "Владелец", "да", "high")],
               extra="Эффект: ориентир 100 тыс. руб.")
    v = build_vault({"TST.md": LIB_FIXTURE, "artifacts/КТК/ТСТ_КТК.md": good})
    assert not any("H6" in e for e in run(v)["errors"])

    bad = ktk("РП", "Руководитель производства",
              [ktk_row(1, "TST-01", "Владелец", "да", "high")],
              extra="Эффект: 100 тыс. руб.")
    v2 = build_vault({"TST.md": LIB_FIXTURE, "artifacts/КТК/ТСТ_КТК.md": bad})
    assert any("H6" in e for e in run(v2)["errors"])


# --- role resolution maps --------------------------------------------------
def test_role_resolution_maps():
    reg = ca.load_registry()
    assert ca.roles_for_string(reg, "ОТК") == ["РК"]              # event_owner_map
    assert set(ca.roles_for_string(reg, "ПЭО")) == {"РП", "ГД"}   # fold_map multi
    assert ca.roles_for_string(reg, "Оператор") == []             # worker
    assert ca.role_for_string(reg, "Начальник транспортной службы") == "РС"


# --- traceability report (E4) ---------------------------------------------
def test_traceability_no_gaps():
    import traceability as tr
    rep = tr.build(_full_vault())
    assert rep["counts"]["no_code"] == 0, rep["gaps"]
    assert rep["counts"]["unresolved"] == 0, rep["gaps"]
    assert rep["counts"]["ktk_links"] == len(CODES)
    assert rep["ktk"][0]["goal"] is not None


def test_traceability_reports_gap():
    import traceability as tr
    v = build_vault({
        "TST.md": LIB_FIXTURE,
        "artifacts/КТК/ТСТ_КТК.md": ktk(
            "РП", "Руководитель производства",
            [ktk_row(1, "—", "Владелец", "да", "high")]),
    })
    rep = tr.build(v)
    assert rep["counts"]["no_code"] == 1, rep["gaps"]


def test_traceability_empty_vault_not_ok():
    """A vault with no artifacts must not report a green OK (exit 2)."""
    import traceability as tr
    v = build_vault({"TST.md": LIB_FIXTURE})
    assert tr.build(v)["artifact_files"] == 0
    assert tr.main([v]) == 2


# --- vault guards ----------------------------------------------------------
def test_empty_artifacts_is_error():
    v = build_vault({"TST.md": LIB_FIXTURE})
    res = run(v)
    assert any("no artifact files" in e for e in res["errors"]), res["errors"]
