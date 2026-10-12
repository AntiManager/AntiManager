#!/usr/bin/env python3
"""Derive the unified priority matrix from the source ФРПС register (plan 1791810263662, Phase C).

Source (client register, read-only):
  Proc_library/library/reglaments/ФРПС/Приоритеты_руководителей.md  (13 role sections)
Target (unified artifact, one file):
  <vault>/library/artifacts/Приоритеты_руководителей.md   (10 canonical roles)

Rules (specs/T4.2):
  - 13 source sections -> 10 register roles. Action roles (Оператор, Ремонтный
    персонал) are dropped. ПЭО folds into ГД+РП, ИПП into РП, РПС into ГТ:
    folding drops the source section and re-anchors its rows to the target role.
  - ГИ and РС have no source section -> authored from the library (INF/ENV/EMG/HRP
    for ГИ; SL_LOG/PLAN-03/HRP/ORG for РС).
  - every row must reference >=1 valid library process code (H7); a source row
    whose code cell resolves to no library node is dropped.
  - client/holding tokens stripped (H6): stop-words, money-figure, hard dates.

Usage:
  python author_priority_matrix.py --analyze
  python author_priority_matrix.py --emit <vault> [--out <file>]
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

SRC_DEFAULT = os.path.join(
    os.path.dirname(HERE), "..", "..", "Proc_library", "library",
    "reglaments", "ФРПС", "Приоритеты_руководителей.md")

ROLE_HEAD_RE = re.compile(r"^##\s+\d+\.\s+(.*?)\s*$")
PLAIN_HEAD_RE = re.compile(r"^##\s+(.*?)\s*$")
QUADRANTS = ["Срочно и важно", "Важно, но не срочно",
             "Срочно, но не важно", "Не срочно и не важно"]
EMPTY = {"—", "–", "-", ""}

ORDER = ["ГД", "РП", "ГИ", "ГТ", "РК", "РС", "ГМ", "HR", "НЦ", "НС"]
NAMES = {
    "ГД": "Генеральный директор", "РП": "Руководитель производства",
    "ГИ": "Главный инженер", "ГТ": "Главный технолог",
    "РК": "Руководитель качества", "РС": "Руководитель склада",
    "ГМ": "Главный механик", "HR": "HR-менеджер",
    "НЦ": "Начальник цеха", "НС": "Начальник смены / Мастер",
}
FOLDS = {
    "ГД": "вбирает задачи ПЭО (экономическое планирование)",
    "РП": "вбирает ИПП (подготовка производства)",
    "ГТ": "вбирает РПС (развитие производственных систем)",
    "ГИ": "вбирает Эколога и специалиста по охране труда",
    "РК": "вбирает Инженера по качеству (владелец-уровень)",
    "РС": "вбирает начальника транспортной службы",
}

# Source section number -> register code(s); [] = drop (action role).
# §6 (ПЭО) folds into ГД: its head reports to the director; ИПП (§13) into РП;
# РПС (§12) into ГТ. Оператор (§10) and Ремонтный персонал (§11) are dropped.
SECTION_ROLES = {
    "1": ["РП"], "2": ["НЦ"], "3": ["ГТ"], "4": ["ГМ"], "5": ["РК"],
    "6": ["ГД"], "7": ["HR"], "8": ["НС"], "9": ["ГД"],
    "10": [], "11": [], "12": ["ГТ"], "13": ["РП"],
}
# The section whose "Целевое распределение времени" line belongs to the role.
PRIMARY = {"РП": "1", "НЦ": "2", "ГТ": "3", "ГМ": "4", "РК": "5",
           "HR": "7", "НС": "8", "ГД": "9"}

# --- de-identification (umbrella §5 token rules; enforced by H6) ------------
SDS = "служба развития производственной системы"
CLEAN = [
    # parentheticals that are hard targets -> drop whole group
    (re.compile(r"\((?:[^()]*\d+[.,]?\d*\s*%[^()]*)\)"), ""),
    (re.compile(r">\s*\d+([.,]\d+)?\s*%"), ""),
    (re.compile(r"≤\s*±?\s*\d+([.,]\d+)?\s*%"), ""),
    (re.compile(r"≥\s*\d+([.,]\d+)?\s*%"), ""),
    (re.compile(r"до\s*\d[\d\s\u00a0]*тыс\.?\s*руб\.?"), "в пределах установленного лимита"),
    (re.compile(r"\d[\d\s\u00a0]*тыс\.?\s*руб\.?"), "установленного лимита"),
    (re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b"), ""),
    # головная организация (УК) — case-aware
    (re.compile(r"с УК\b"), "с головной организацией"),
    (re.compile(r"в УК\b"), "в головную организацию"),
    (re.compile(r"перед УК\b"), "перед головной организацией"),
    (re.compile(r"от УК\b"), "от головной организации"),
    (re.compile(r"\bи УК\b"), "и головной организацией"),
    (re.compile(r"\bУК\b"), "головной организации"),
    # внешний заказчик (ТД / Торговый дом)
    (re.compile(r"с ТД\b"), "с внешним заказчиком"),
    (re.compile(r"Торговым домом"), "внешним заказчиком"),
    (re.compile(r"Торгового дома"), "внешнего заказчика"),
    (re.compile(r"Торговый дом"), "внешний заказчик"),
    (re.compile(r"\bТД\b"), "внешнего заказчика"),
    (re.compile(r"давальческ\w*"), "по переработке"),
    (re.compile(r"ПС ПП"), "производственной системы"),
    (re.compile(r"ФРПС"), SDS),
    (re.compile(r"Росприроднадзор"), "надзорный орган"),
    (re.compile(r"2-ТП"), "статистическая отчётность"),
    (re.compile(r"Power\s*BI"), "BI-инструмент"),
    (re.compile(r"Proc_lib\w*"), "библиотека процессов"),
    (re.compile(r"Приоритеты_руководителей"), "матрица приоритетов"),
    (re.compile(r"1С[:\s]*ERP|1С ERP"), "учётная система"),
    # экономическая служба (ПЭО) — case-aware
    (re.compile(r"Делегировать ПЭО\b"), "Делегировать экономической службе"),
    (re.compile(r"Передать ПЭО\b"), "Передать экономической службе"),
    (re.compile(r"с ПЭО\b"), "с экономической службой"),
    (re.compile(r"для ПЭО\b"), "для экономической службы"),
    (re.compile(r"\bПЭО\b"), "экономическая служба"),
    # ИПП
    (re.compile(r"с ИПП\b"), "с инженером по подготовке производства"),
    (re.compile(r"\bИПП\b"), "инженер по подготовке производства"),
    # РПС
    (re.compile(r"инициированных РПС"), "инициированных службой развития производственной системы"),
    (re.compile(r"предложенного РПС"), "предложенной службой развития производственной системы"),
    (re.compile(r"РПС\s*[–-]\s*координатор"), "координатор — " + SDS),
    (re.compile(r"\bРПС\b"), SDS),
]
CODE_RE = re.compile(r"\b[A-Z][A-Z0-9_-]*-\d{2}(?:-\d{2})*\b")


def clean(s: str) -> str:
    for pat, repl in CLEAN:
        s = pat.sub(repl, s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def parse_source(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    sections, cur, in_table, quadrant = [], None, False, None
    for ln in lines:
        m = ROLE_HEAD_RE.match(ln)
        if m:
            cur = {"title": m.group(1),
                   "num": ln.split(".")[0].lstrip("# ").strip(),
                   "rows": [], "time": ""}
            sections.append(cur)
            in_table, quadrant = False, None
            continue
        if ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if (len(cells) == 6 and cells[0] == "Квадрант" and cells[1] == "Задача"
                    and cells[5].startswith("Связанный процесс")):
                in_table = True
                continue
            if set("".join(cells)) <= set("-: ") or not in_table or cur is None:
                continue
            if len(cells) < 6:
                continue
            q = re.sub(r"\*\*", "", cells[0]).strip()
            if q:
                quadrant = q
            cur["rows"].append({
                "quadrant": quadrant, "task": cells[1], "type": cells[2],
                "delegation": cells[3], "prevention": cells[4], "codes": cells[5]})
        else:
            if ln.strip():
                in_table = False
            if cur is not None and "Целевое распределение времени" in ln:
                cur["time"] = clean(ln)
    return sections


def split_codes(raw, lib):
    out = []
    for c in re.split(r"[,\s]+", raw):
        c = c.strip()
        if CODE_RE.fullmatch(c) and c in lib.by_code:
            out.append(c)
    return out


def build_rows(sections, lib):
    role_rows = {code: [] for code in ORDER}
    role_time = {}
    for s in sections:
        targets = SECTION_ROLES.get(s["num"], [])
        if not targets:
            continue
        for code in targets:
            if PRIMARY.get(code) == s["num"] and s["time"]:
                role_time[code] = s["time"]
        for r in s["rows"]:
            codes = split_codes(r["codes"], lib)
            if not codes:
                continue
            task = clean(r["task"])
            if not task:
                continue
            row = {
                "quadrant": r["quadrant"] or QUADRANTS[0], "task": task,
                "type": clean(r["type"]), "delegation": clean(r["delegation"]),
                "prevention": clean(r["prevention"]), "codes": ", ".join(codes)}
            for code in targets:
                role_rows[code].append(dict(row))
    return role_rows, role_time


def dedup_and_sort(rows):
    qi = {q: i for i, q in enumerate(QUADRANTS)}
    seen, out = set(), []
    for r in sorted(rows, key=lambda x: qi.get(x["quadrant"], 99)):
        key = (r["quadrant"], re.sub(r"\W+", " ", r["task"].lower()))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


# --- authored sections (roles absent from the source register) -------------
def authored_rows():
    def R(q, t, ty, d, p, c):
        return {"quadrant": q, "task": t, "type": ty, "delegation": d,
                "prevention": p, "codes": c}
    gi = [
        R("Срочно и важно", "Аварийная остановка инженерных систем (энерго-, тепло-, водоснабжение), угрожающая производству", "Разовый кризис", "Лично, с главным энергетиком и главным механиком", "Резервирование критичных вводов и плановое ТО — в квадрант 2", "INF-02"),
        R("Срочно и важно", "Экологический инцидент (разлив, превышение выбросов или сбросов)", "Разовый кризис", "Лично, уведомление надзорных органов", "Производственный экологический контроль — в квадрант 2", "ENV-03-01"),
        R("Срочно и важно", "Травма или опасный инцидент на объектах инфраструктуры", "Разовый кризис", "Лично, организация расследования", "Систематическое обучение по охране труда — в квадрант 2", "HRP-02-03"),
        R("Срочно и важно", "Пожар или авария с угрозой жизни и имуществу", "Разовый кризис", "Лично, взаимодействие с аварийными службами", "Планы реагирования и тренировки — в квадрант 2", "EMG-01"),
        R("Срочно и важно", "Отказ грузоподъёмных механизмов", "Разовый кризис", "Лично, с механиком по грузоподъёмным механизмам", "Периодическое техническое освидетельствование — в квадрант 2", "INF-04"),
        R("Важно, но не срочно", "Производственный экологический контроль", "–", "Лично, с экологом", "–", "ENV-02"),
        R("Важно, но не срочно", "Обращение с отходами производства и потребления", "–", "Лично, с экологом и начальниками цехов", "–", "ENV-01"),
        R("Важно, но не срочно", "Планирование технического обслуживания и ремонта инженерных систем", "–", "Делегировать инженеру технической службы с контролем", "–", "INF-14"),
        R("Важно, но не срочно", "Управление энергоресурсами и энергоэффективность", "–", "Лично, с главным энергетиком", "–", "INF-02"),
        R("Важно, но не срочно", "Промышленная безопасность и охрана труда", "–", "Лично, со специалистом по охране труда", "–", "INF-09"),
        R("Важно, но не срочно", "Развитие инфраструктуры и управление активами", "–", "Лично, с экономической службой", "–", "INF-13"),
        R("Важно, но не срочно", "Бюджетирование и экономика ремонта инфраструктуры", "–", "Лично, с экономической службой", "–", "INF-10"),
        R("Важно, но не срочно", "Развитие компетенций персонала инженерных служб", "–", "Лично, с HR-менеджером", "–", "INF-11"),
        R("Срочно, но не важно", "Текущие заявки на ремонт зданий и сооружений", "–", "Делегировать инженеру технической службы с контролем", "Перевести заявки в электронный вид", "INF-01"),
        R("Срочно, но не важно", "Согласование доступа подрядчиков на территорию", "–", "Делегировать специалисту по режиму с контролем", "Электронные пропуска", "INF-01"),
        R("Не срочно и не важно", "Ведение бумажных архивов проектной документации", "–", "Перевести в электронный архив", "–", "INF-08"),
        R("Не срочно и не важно", "Дублирующие отчёты по инженерным системам", "–", "Автоматизировать выгрузку из систем учёта", "–", "INF-13"),
    ]
    rs = [
        R("Срочно и важно", "Остановка отгрузки готовой продукции из-за сбоя склада или транспорта", "Разовый кризис", "Лично, координация с производством", "Резервные маршруты и перекрёстное обучение — в квадрант 2", "SL_LOG-02"),
        R("Срочно и важно", "Срыв поставки сырья или материалов на производство из-за дефицита запаса", "Разовый кризис", "Лично, эскалация к снабжению", "Нормирование страховых запасов — в квадрант 2", "SL_LOG-01"),
        R("Срочно и важно", "Порча или утрата груза (сырья, материалов, готовой продукции)", "Системный сбой", "Лично, разбор причин с материально ответственным", "Условия хранения и контроль — в квадрант 2", "SL_LOG-01"),
        R("Срочно и важно", "Травма или инцидент на погрузочно-разгрузочных работах", "Разовый кризис", "Лично, организация расследования", "Обучение безопасным приёмам — в квадрант 2", "HRP-02-03"),
        R("Срочно и важно", "Простой транспорта из-за отказа техники", "Системный сбой", "Лично, с механиком транспортной службы", "Плановое обслуживание автопарка — в квадрант 2", "SL_LOG-03"),
        R("Важно, но не срочно", "Нормирование складских запасов", "–", "Лично, с инженером по планированию", "–", "PLAN-03-01"),
        R("Важно, но не срочно", "Анализ эффективности управления запасами (ABC/XYZ)", "–", "Лично, с инженером по планированию", "–", "PLAN-03-02"),
        R("Важно, но не срочно", "Управление готовой продукцией и отгрузкой", "–", "Лично, с начальником склада готовой продукции", "–", "SL_LOG-02"),
        R("Важно, но не срочно", "Развитие транспортной логистики", "–", "Лично, с начальником транспортной службы", "–", "SL_LOG-03"),
        R("Важно, но не срочно", "Управление возвратной логистикой", "–", "Лично, с координатором возвратов", "–", "SL_LOG-04"),
        R("Важно, но не срочно", "Инвентаризация и контроль сохранности запасов", "–", "Лично, с материально ответственными", "–", "SL_LOG-01"),
        R("Важно, но не срочно", "Обучение и развитие складского персонала", "–", "Лично, с HR-менеджером", "–", "HRP-01-02"),
        R("Срочно, но не важно", "Оформление первичных складских документов", "–", "Делегировать кладовщику с контролем", "Электронный документооборот", "SL_LOG-01"),
        R("Срочно, но не важно", "Текущие заявки на внутризаводской транспорт", "–", "Делегировать диспетчеру с контролем", "Электронные маршрутные листы", "SL_LOG-03"),
        R("Не срочно и не важно", "Дублирующие отчёты о движении товарно-материальных ценностей", "–", "Автоматизировать выгрузку из учётной системы", "–", "SL_LOG-01"),
        R("Не срочно и не важно", "Ведение бумажных журналов приёма-передачи", "–", "Перевести в электронный вид", "–", "ORG-02-02"),
    ]
    return {"ГИ": gi, "РС": rs}


PRINCIPLES = [
    "1. **Приоритетность при конфликтах:** безопасность > качество > выполнение плана > бюджет. Любой руководитель вправе остановить процесс при угрозе безопасности или массовом браке.",
    "2. **Тип задачи в квадранте «Срочно и важно»:** *разовый кризис* требует немедленного личного вмешательства; *системный сбой* (повторяется чаще раза в месяц) автоматически порождает задачу в квадранте «Важно, но не срочно» — устранить корневую причину.",
    "3. **Делегирование:** указывается конкретный исполнитель с ресурсом времени и полномочиями; при перегрузке задача не делегируется, а вопросы перераспределения или автоматизации решаются отдельно. Ответственность за результат сохраняется за руководителем.",
    "4. **Автоматизация и исключение:** для квадранта «Не срочно и не важно» указывается план замены (электронный вид, дашборды, отказ от нечитаемых отчётов).",
    "5. **Целевое распределение времени** даётся как ориентир с поэтапным графиком достижения.",
    "6. **Ежеквартальная ревизия** матрицы с учётом изменений стратегии, оборудования и персонала.",
    "7. **Привязка к процессам:** каждая задача ссылается на код процесса из библиотеки процессов — единое понимание и быстрый доступ к регламентам.",
]


def render(role_rows, role_time, lib):
    L = []
    L.append("---")
    L.append("artifact: priority-matrix")
    L.append("roles: [%s]" % ", ".join(ORDER))
    L.append("status: draft")
    L.append("updated: 2026-10-12")
    L.append("tags: [library, artifacts, priorities]")
    L.append("---")
    L.append("")
    L.append("# Матрица приоритетов руководителей (Эйзенхауэр)")
    L.append("")
    L.append("> Артефакт единой цепочки управления (КТК → приоритеты руководителей → "
             "сетка регулярных событий). Реестр ролей — `Роли.md`; спецификация — "
             "`specs/T4.2` (EN).")
    L.append("")
    L.append("## Общие принципы")
    L.append("")
    L.extend(PRINCIPLES)
    L.append("")
    header = ("| Квадрант | Задача | Тип | Делегирование | "
              "Профилактика / автоматизация | Связанный процесс (код) |")
    sep = "| --- | --- | --- | --- | --- | --- |"
    for code in ORDER:
        rows = role_rows[code]
        L.append("## %s (%s)" % (NAMES[code], code))
        L.append("")
        note = "> Роль: %s (%s)." % (NAMES[code], code)
        if code in FOLDS:
            note += " %s." % FOLDS[code]
        L.append(note)
        L.append("")
        L.append(header)
        L.append(sep)
        for r in rows:
            L.append("| %s | %s | %s | %s | %s | %s |" % (
                r["quadrant"], r["task"], r["type"] or "–", r["delegation"] or "–",
                r["prevention"] or "–", r["codes"]))
        L.append("")
        if role_time.get(code):
            L.append(role_time[code])
            L.append("")
    return "\n".join(L).rstrip() + "\n"


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
            codes = sum(1 for r in s["rows"] if r["codes"] not in EMPTY)
            print(f"§{s['num']:>2} rows={len(s['rows']):>2} coded={codes:>2} "
                  f"-> {SECTION_ROLES.get(s['num'])}")
        return 0

    if not args.emit:
        ap.error("choose --analyze or --emit <vault>")
    vault = args.emit
    from check_artifacts import parse_library
    lib = parse_library(vault)
    role_rows, role_time = build_rows(sections, lib)
    for code, rows in authored_rows().items():
        role_rows[code] = dedup_and_sort(role_rows[code] + rows)
    for code in ORDER:
        role_rows[code] = dedup_and_sort(role_rows[code])
    text = render(role_rows, role_time, lib)

    out = args.out or os.path.join(vault, "library", "artifacts",
                                   "Приоритеты_руководителей.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {out}")
    for code in ORDER:
        print(f"  {code}: {len(role_rows[code])} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
