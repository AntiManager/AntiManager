"""Author the SL_ANL flow graph (T2.6 sub-step 3, logistics analytics/KPI).

Two idempotent operations on `SL_ANL.md`:

1. Insert the boundary operations (external-perimeter sensors/actors) into their
   host subprocess sections: the ERP/accounting data feed (sensor), the transport
   portal / carrier contracts feed (sensor) and the operational management
   consumer of the summary report (actor).
2. Append the per-file «Потоки (Flow Links)» table closing every SL_ANL dangling
   I/O (internal SL_ANL->SL_ANL flow + cross-domain seams to SL_LOG / SL_QUAL /
   SL_MNT / SL_PLAN / STRAT).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\SL_ANL.md")

# code -> (subprocess host, op dict). A boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("SL_ANL-01-01", {
        "code": "SL_ANL-01-01-04",
        "name": "ERP/учётная система — операционные данные и акты расхождений (внешний контур ИТ)",
        "type": "Simple",
        "goal": "Операционные данные приёмки, хранения и отгрузки и акты расхождений доступны для расчёта KPI (внешний контур).",
        "horizon": "day",
        "executor": "ERP/учётная система (внешний контур)",
        "inputs": [],
        "outputs": ["ДанныеОперативногоУчёта@Приёмка", "ДанныеОперативногоУчёта@Склад",
                    "ДанныеОперативногоУчёта@Отгрузка", "Протокол@Расхождений",
                    "Уведомление@Претензия"],
        "kpi": "Доступность данных KPI (100%)",
        "decomposition": "ATOMIC",
    }),
    ("SL_ANL-02-01", {
        "code": "SL_ANL-02-01-03",
        "name": "Транспортный портал и договоры ТК (внешний контур)",
        "type": "Simple",
        "goal": "Данные Транспортного портала и договоры ТК доступны для анализа стоимости доставки (внешний контур).",
        "horizon": "day",
        "executor": "Транспортный портал / ТК (внешний контур)",
        "inputs": [],
        "outputs": ["ДанныеОперативногоУчёта@Доставка", "Документ@ДоговорТК"],
        "kpi": "Полнота данных по доставке (100%)",
        "decomposition": "ATOMIC",
    }),
    ("SL_ANL-03-01", {
        "code": "SL_ANL-03-01-04",
        "name": "Операционная дирекция / руководство — потребитель сводного отчёта (внешний контур)",
        "type": "Simple",
        "goal": "Сводный отчёт, презентация результатов и план корректирующих мероприятий приняты руководством (внешний контур).",
        "horizon": "quarter",
        "executor": "Операционная дирекция (внешний контур)",
        "inputs": ["Отчёт@СводныйПоЛогистике", "Протокол@Презентации", "План@КорректирующихМероприятий"],
        "outputs": [],
        "kpi": "Принятие отчёта и плана мероприятий",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- SL_ANL-01 warehouse KPI collection (internal) -------------------------
    ("SL_ANL-01-01-01", "SL_ANL-03-01-01", "Показатель@KPIПриёмки", "сводка KPI (внутренний поток)"),
    ("SL_ANL-01-01-02", "SL_ANL-03-01-01", "Показатель@KPIХранения", "сводка KPI (внутренний поток)"),
    ("SL_ANL-01-01-02", "SL_ANL-04-01-01", "Показатель@KPIХранения", "исторические KPI (внутренний поток)"),
    ("SL_ANL-01-01-03", "SL_ANL-03-01-01", "Показатель@KPIОтгрузки", "сводка KPI (внутренний поток)"),

    # --- SL_ANL-01 data feed (external contour) --------------------------------
    ("SL_ANL-01-01-04", "SL_ANL-01-01-01", "ДанныеОперативногоУчёта@Приёмка", "ERP-данные (внешний контур ИТ)"),
    ("SL_ANL-01-01-04", "SL_ANL-01-01-01", "Протокол@Расхождений", "акты расхождений (внешний контур ИТ)"),
    ("SL_ANL-01-01-04", "SL_ANL-01-01-02", "ДанныеОперативногоУчёта@Склад", "ERP-данные (внешний контур ИТ)"),
    ("SL_ANL-01-01-04", "SL_ANL-01-01-03", "ДанныеОперативногоУчёта@Отгрузка", "ERP-данные (внешний контур ИТ)"),
    ("SL_ANL-01-01-04", "SL_ANL-01-01-03", "Уведомление@Претензия", "рекламации клиентов (внешний контур)"),

    # --- SL_ANL-02 transport KPI (internal + feeds + cross-domain) --------------
    ("SL_ANL-02-01-01", "SL_ANL-03-01-01", "Отчёт@СтоимостьДоставки", "сводка KPI (внутренний поток)"),
    ("SL_ANL-02-01-02", "SL_ANL-03-01-01", "Показатель@ЗагрузкиТС", "сводка KPI (внутренний поток)"),
    ("SL_ANL-02-01-02", "SL_ANL-04-01-02", "Показатель@ЗагрузкиТС", "транспортные KPI (внутренний поток)"),
    ("SL_ANL-02-01-03", "SL_ANL-02-01-01", "ДанныеОперативногоУчёта@Доставка", "Транспортный портал (внешний контур)"),
    ("SL_ANL-02-01-03", "SL_ANL-02-01-01", "Документ@ДоговорТК", "договоры ТК (внешний контур)"),
    ("SL_LOG-03-01-05", "SL_ANL-02-01-02", "Измерение@GPS", "телематика (SL_LOG)"),
    ("SL_PLAN-02-01-01", "SL_ANL-02-01-02", "ЗаданиеНаПеревозку", "задание на перевозку (SL_PLAN)"),
    ("SL_ANL-02-01-02", "SL_PLAN-02-01-03", "Отчёт@ОптимизацииТС", "рекомендации по ТК (SL_PLAN)"),

    # --- SL_ANL-03 consolidated reporting (internal + external actor) -----------
    ("SL_ANL-03-01-01", "SL_ANL-03-01-02", "Сводка@KPI", "внутренний поток"),
    ("SL_ANL-03-01-02", "SL_ANL-03-01-03", "Отчёт@СводныйПоЛогистике", "внутренний поток"),
    ("SL_ANL-03-01-02", "SL_ANL-03-01-04", "Отчёт@СводныйПоЛогистике", "представление руководству (внешний контур)"),
    ("SL_ANL-03-01-03", "SL_ANL-03-01-04", "Протокол@Презентации", "представление руководству (внешний контур)"),
    ("SL_ANL-03-01-03", "SL_ANL-03-01-04", "План@КорректирующихМероприятий", "представление руководству (внешний контур)"),

    # --- SL_ANL-04 predictive analytics (internal + cross-domain) ---------------
    ("STRAT-01-01-01", "SL_ANL-04-01-01", "ПланПроизводства", "план производства (STRAT)"),
    ("SL_LOG-01-02-01", "SL_ANL-04-01-01", "Измерение@ЗагрузкаСклада", "загрузка склада (SL_LOG)"),
    ("SL_LOG-03-01-04", "SL_ANL-04-01-02", "Отчёт@ДвиженияТС", "данные движения ТС (SL_LOG)"),
    ("SL_LOG-03-01-05", "SL_ANL-04-01-02", "Документ@СостояниеТС", "телематика (SL_LOG)"),
    ("SL_ANL-04-01-01", "SL_PLAN-01-02-02", "Отчёт@ПрогнозЗагрузкиСклада", "рекомендации по ёмкости (SL_PLAN)"),
    ("SL_ANL-04-01-01", "SL_PLAN-03-01-01", "Измерение@ПиковыхНагрузок", "ограничения S&OP (SL_PLAN)"),
    ("SL_ANL-04-01-02", "SL_PLAN-03-01-02", "Измерение@ПрогнозПотребностиТС", "ограничения S&OP (SL_PLAN)"),
    ("SL_LOG-03-01-05", "SL_ANL-04-02-01", "Измерение@ПробегТопливо", "телематика (SL_LOG)"),
    ("SL_LOG-03-01-05", "SL_ANL-04-02-01", "Документ@СостояниеТС", "телематика (SL_LOG)"),
    ("SL_MNT-01-01-03", "SL_ANL-04-02-01", "Отчёт@ЗатратыНаТО", "журнал ТО (SL_MNT)"),
    ("SL_ANL-04-02-01", "SL_ANL-04-02-02", "Отчёт@ТехническоеСостояниеПарка", "внутренний поток"),
    ("SL_ANL-04-02-01", "SL_ANL-04-02-02", "РеестрРисков", "внутренний поток"),
    ("SL_ANL-04-02-02", "SL_MNT-01-01-01", "График@ТООткорректирован", "корректировка графика ТО (SL_MNT)"),
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


def insert_boundaries(lines, eol):
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
    lines = insert_boundaries(lines, eol)
    text = eol.join(lines)
    if not text.endswith(eol + eol):
        text = text.rstrip("\r\n") + eol + eol
    text += build_section().replace("\r\n", eol)
    with io.open(FILE, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"boundaries={len(BOUNDARIES)} edges={len(EDGES)} eol={repr(eol)}")


if __name__ == "__main__":
    sys.exit(main())
