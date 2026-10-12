"""Author the STRAT flow graph (T2.6 sub-step 3, strategic planning & budgeting).

Two idempotent operations on `STRAT.md`:

1. Insert the boundary operations (enterprise-perimeter sensors and the
   management actor) into their host subprocess sections: the external
   strategic contour (UPL / управляющая компания — strategy, goals, sales
   forecast, long-term contracts), the reference-normative contour (capacity
   performance, working-time fund), the planning-economic contour (forecast
   prices, energy tariffs, investment programme), the budget-committee protocol
   (approval decision), the process registry (справочный контур) and the
   management / strategic-committee actor that archives the goals and X-matrix.
2. Append the per-file «Потоки (Flow Links)» table closing every STRAT dangling
   I/O (internal STRAT->STRAT flow + cross-domain seams to/from ORG / ENG / MNT /
   ANLZ / IMPR / HRP; the pins owned by ENG / SL_PLAN / ANLZ are kept coherent).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\STRAT.md")

# code -> (subprocess host, op dict). A boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("STRAT-01-01", {
        "code": "STRAT-01-01-02",
        "name": "Внешний стратегический контур (УПЛ / управляющая компания) — стратегия и прогнозы продаж",
        "type": "Simple",
        "goal": "Стратегия развития, стратегические цели, прогнозы продаж и данные о долгосрочных контрактах доступны для формирования производственной программы (внешний контур).",
        "horizon": "year",
        "executor": "УПЛ / управляющая компания (внешний контур)",
        "inputs": [],
        "outputs": ["Документ@СтратегияРазвитияКомпании", "Документ@СтратегическиеЦели",
                    "Документ@ПрогнозПродаж", "Документ@ДолгосрочныеКонтракты"],
        "kpi": "Полнота и своевременность стратегических вводных (до старта цикла планирования)",
        "decomposition": "ATOMIC",
    }),
    ("STRAT-01-01", {
        "code": "STRAT-01-01-03",
        "name": "Справочно-нормативный контур — производительность и фонд рабочего времени",
        "type": "Simple",
        "goal": "Нормативная производительность оборудования и нормативный фонд рабочего времени доступны для балансировки программы (справочный контур).",
        "horizon": "year",
        "executor": "НСИ / справочно-нормативный контур",
        "inputs": [],
        "outputs": ["Норматив@Производительность", "Норматив@ФондРабочегоВремени"],
        "kpi": "Актуальность нормативов производительности и фонда времени",
        "decomposition": "ATOMIC",
    }),
    ("STRAT-01-02", {
        "code": "STRAT-01-02-04",
        "name": "Планово-экономический контур — прогнозные цены, тарифы и инвестиции",
        "type": "Simple",
        "goal": "Прогнозные цены на сырьё и материалы, плановые тарифы на энергоресурсы и данные о планируемых инвестициях доступны для калькуляции (внешний контур).",
        "horizon": "year",
        "executor": "УПЛ / снабжение / планово-экономический контур",
        "inputs": [],
        "outputs": ["Документ@ПрогнозЦенНаСырьё", "Норматив@ТарифыНаЭнергоресурсы",
                    "Документ@ИнвестиционнаяПрограмма"],
        "kpi": "Полнота прогнозных цен и тарифов (до начала бюджетного расчёта)",
        "decomposition": "ATOMIC",
    }),
    ("STRAT-01-02", {
        "code": "STRAT-01-02-05",
        "name": "Бюджетный комитет / ПЭУ — протокол утверждения бюджета",
        "type": "Simple",
        "goal": "Решение бюджетного комитета об утверждении бюджета производственных затрат доступно для завершения бюджетного цикла (внешний контур).",
        "horizon": "year",
        "executor": "Бюджетный комитет / ПЭУ (внешний контур)",
        "inputs": [],
        "outputs": ["Протокол@БюджетногоКомитета"],
        "kpi": "Наличие протокола бюджетного комитета (до 1 декабря)",
        "decomposition": "ATOMIC",
    }),
    ("STRAT-01-03", {
        "code": "STRAT-01-03-07",
        "name": "Перечень основных процессов предприятия (справочный контур)",
        "type": "Simple",
        "goal": "Перечень основных процессов предприятия доступен для построения Х-матрицы (справочный контур).",
        "horizon": "year",
        "executor": "Справочный контур / система менеджмента",
        "inputs": [],
        "outputs": ["Документ@ПереченьОсновныхПроцессов"],
        "kpi": "Актуальность перечня основных процессов",
        "decomposition": "ATOMIC",
    }),
    ("STRAT-01-03", {
        "code": "STRAT-01-03-08",
        "name": "Руководство производства / стратегический комитет — архив целей и Х-матриц (управленческий контур)",
        "type": "Simple",
        "goal": "Актуализированные цели, Х-матрицы и отчёт о ходе выполнения приняты управленческим контуром (внутренний контур).",
        "horizon": "quarter",
        "executor": "Руководство производства / стратегический комитет (внутренний контур)",
        "inputs": ["Документ@ХМатрица@Актуализирована", "Отчёт@ХодВыполненияЦелей"],
        "outputs": [],
        "kpi": "Полнота управленческого контура по целям и Х-матрицам",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- STRAT-01-01 production programme (internal) ---------------------------
    ("STRAT-01-01-01", "STRAT-01-02-01", "ПотребностьВРесурсах@Годовая", "годовая потребность в ресурсах для калькуляции (внутренний поток)"),
    ("STRAT-01-01-01", "STRAT-01-02-02", "ПланПроизводства", "производственная программа для бюджета (внутренний поток)"),

    # --- STRAT-01-01 boundary feeds --------------------------------------------
    ("STRAT-01-01-02", "STRAT-01-01-01", "Документ@СтратегияРазвитияКомпании", "стратегия развития компании (внешний контур)"),
    ("STRAT-01-01-02", "STRAT-01-01-01", "Документ@СтратегическиеЦели", "стратегические цели компании (внешний контур)"),
    ("STRAT-01-01-02", "STRAT-01-01-01", "Документ@ПрогнозПродаж", "прогнозы продаж (внешний контур)"),
    ("STRAT-01-01-02", "STRAT-01-01-01", "Документ@ДолгосрочныеКонтракты", "данные о долгосрочных контрактах (внешний контур)"),
    ("STRAT-01-01-03", "STRAT-01-01-01", "Норматив@Производительность", "нормативная производительность (справочный контур)"),
    ("STRAT-01-01-03", "STRAT-01-01-01", "Норматив@ФондРабочегоВремени", "нормативный фонд рабочего времени (справочный контур)"),

    # --- STRAT-01-02 budget chain (internal) -----------------------------------
    ("STRAT-01-02-01", "STRAT-01-02-02", "Документ@СводнаяВедомостьЗатрат", "сводная ведомость затрат (внутренний поток)"),
    ("STRAT-01-02-02", "STRAT-01-02-03", "Бюджет@Проект", "проект бюджета на утверждение (внутренний поток)"),

    # --- STRAT-01-02 boundary feeds --------------------------------------------
    ("STRAT-01-02-04", "STRAT-01-02-01", "Документ@ПрогнозЦенНаСырьё", "прогнозные цены на сырьё и материалы (внешний контур)"),
    ("STRAT-01-02-04", "STRAT-01-02-01", "Норматив@ТарифыНаЭнергоресурсы", "плановые тарифы на энергоресурсы (внешний контур)"),
    ("STRAT-01-02-04", "STRAT-01-02-01", "Документ@ИнвестиционнаяПрограмма", "данные о планируемых инвестициях (внешний контур)"),
    ("STRAT-01-02-05", "STRAT-01-02-03", "Протокол@БюджетногоКомитета", "протокол бюджетного комитета (внешний контур)"),

    # --- STRAT-01-03 hoshin kanri (internal) -----------------------------------
    ("STRAT-01-03-01", "STRAT-01-03-02", "Документ@ПрорывныеЦели", "прорывные цели на год (внутренний поток)"),
    ("STRAT-01-03-02", "STRAT-01-03-03", "Документ@ХМатрица", "Х-матрица верхнего уровня (внутренний поток)"),
    ("STRAT-01-03-03", "STRAT-01-03-04", "Документ@ХМатрицаЦехов", "Х-матрицы цехов (внутренний поток)"),
    ("STRAT-01-03-03", "STRAT-01-03-04", "Документ@ХМатрицаУчастков", "Х-матрицы участков (внутренний поток)"),
    ("STRAT-01-03-05", "STRAT-01-03-06", "Отчёт@ХодВыполненияЦелей", "отчёт о ходе выполнения целей (внутренний поток)"),

    # --- STRAT-01-03 boundary feeds --------------------------------------------
    ("STRAT-01-01-02", "STRAT-01-03-01", "Документ@СтратегическиеЦели", "стратегические цели компании (внешний контур)"),
    ("STRAT-01-01-02", "STRAT-01-03-06", "Документ@СтратегияРазвитияКомпании", "новая стратегия для ревизии (внешний контур)"),
    ("STRAT-01-03-07", "STRAT-01-03-02", "Документ@ПереченьОсновныхПроцессов", "перечень основных процессов (справочный контур)"),
    ("STRAT-01-03-05", "STRAT-01-03-08", "Отчёт@ХодВыполненияЦелей", "отчёт о ходе целей в управленческий контур (внутренний контур)"),
    ("STRAT-01-03-06", "STRAT-01-03-08", "Документ@ХМатрица@Актуализирована", "актуализированная Х-матрица (внутренний контур)"),

    # --- cross-domain inbound --------------------------------------------------
    ("ORG-01-02-02", "STRAT-01-01-01", "Норматив@НормыТруда", "нормы труда (ORG)"),
    ("ORG-01-02-02", "STRAT-01-02-01", "Норматив@НормыТруда", "нормы труда для калькуляции (ORG)"),
    ("ENG-01-01-07", "STRAT-01-01-01", "Паспорт@Оборудования", "паспорта оборудования (ENG)"),
    ("MNT-01-04-05", "STRAT-01-01-01", "Документ@КарточкаОбъектаТОиР", "карточки ТОиР (MNT)"),
    ("MNT-03-02-01", "STRAT-01-01-01", "График@ППР", "план-график ППР (MNT)"),
    ("ANLZ-01-01-01", "STRAT-01-03-01", "Отчёт@АнализОтклонений", "анализ текущего состояния (ANLZ)"),
    ("ANLZ-01-01-01", "STRAT-01-03-05", "Показатель@OEE", "фактические KPI (ANLZ)"),
    ("IMPR-02-03-04", "STRAT-01-03-05", "Отчёт@СтатусПроектов", "статус проектов улучшений (IMPR)"),

    # --- cross-domain outbound -------------------------------------------------
    ("STRAT-01-03-04", "HRP-01-04-03", "Документ@ИндивидуальныеKPI", "индивидуальные KPI в систему мотивации (HRP)"),
]

HEADER = "## Потоки (Flow Links)"
TABLE_HEAD = ("| Источник (Операция.Выход) | → | Приёмник (Операция.Вход) "
              "| Условие |")
TABLE_SEP = "|---------------------------|:---:|---------------------------|---------|"

HEAD_RE = re.compile(r"^#{1,4}\s")
SUB_RE = re.compile(r"^####\s+Подпроцесс\s+(\S+?):")
OPNODE_RE = re.compile(r"^#####\s+Операция\s+(\S+?):")


def io_cell(items):
    if not items:
        return "\u2014"
    return ", ".join("`%s`" % i for i in items)


def block(op):
    lines = [f"##### Операция {op['code']}: {op['name']}"]
    lines.append(f"- **Тип:** {op['type']}")
    lines.append(f"- **Цель:** {op['goal']}")
    lines.append(f"- **Горизонт:** {op['horizon']}")
    lines.append(f"- **Исполнитель:** {op['executor']}")
    lines.append(f"- **Входы:** {io_cell(op['inputs'])}")
    lines.append(f"- **Выходы:** {io_cell(op['outputs'])}")
    lines.append(f"- **КПЭ:** {op['kpi']}")
    lines.append(f"- **decomposition:** {op['decomposition']}")
    return lines


def insert_boundaries(lines):
    present = {OPNODE_RE.match(x).group(1) for x in lines if OPNODE_RE.match(x)}
    for host, op in BOUNDARIES:
        if op["code"] in present:
            continue
        start = None
        for i, ln in enumerate(lines):
            m = SUB_RE.match(ln)
            if m and m.group(1) == host:
                start = i
                break
        if start is None:
            raise SystemExit(f"host subprocess {host} not found")
        j = start + 1
        while j < len(lines) and not HEAD_RE.match(lines[j]):
            j += 1
        ins = [""] + block(op)
        lines[j:j] = ins
        present.add(op["code"])
    return lines


def build_section():
    out = [HEADER, "", TABLE_HEAD, TABLE_SEP]
    for src, dst, tok, cond in sorted(EDGES, key=lambda e: (e[0], e[1], e[2])):
        out.append(f"| {src}.{tok} | → | {dst}.{tok} | {cond} |")
    return "\r\n".join(out) + "\r\n"


def main():
    with io.open(FILE, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    eol = "\r\n" if "\r\n" in text else "\n"
    idx = text.find(eol + HEADER)
    if idx == -1:
        idx = text.find("\n" + HEADER)
    if idx != -1:
        text = text[:idx].rstrip("\r\n") + "\r\n"
    lines = text.split(eol)
    lines = insert_boundaries(lines)
    text = eol.join(lines)
    if not text.endswith(eol + eol):
        text = text.rstrip("\r\n") + eol + eol
    text += build_section().replace("\r\n", eol)
    with io.open(FILE, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"boundaries={len(BOUNDARIES)} edges={len(EDGES)} eol={repr(eol)}")


if __name__ == "__main__":
    sys.exit(main())
