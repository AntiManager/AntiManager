"""Author the SL_QUAL flow graph (T2.6 sub-step 3, logistics quality).

Two idempotent operations on `SL_QUAL.md`:

1. Insert the boundary operations (external-perimeter sensors/actors) into their
   host subprocess sections — the residual I/O the in-library domains do not
   provide/consume: internal standards (методики отбора проб, норматив погрузки),
   external claims (претензия клиента/ТК) and the counterparty contract/response.
2. Append the per-file «Потоки (Flow Links)» table closing every SL_QUAL dangling
   I/O (internal SL_QUAL->SL_QUAL flow + cross-domain seams to QUAL / SL_LOG /
   MFG / SL_ANL / ORG / SL_MNT).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\SL_QUAL.md")

# code -> (subprocess host, op dict). The boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("SL_QUAL-01-01", {
        "code": "SL_QUAL-01-01-04",
        "name": "Актуализация методик отбора проб (внутренний стандарт)",
        "type": "Simple",
        "goal": "Методики отбора проб ТМЦ актуализированы (внешний к SL_QUAL стандарт).",
        "horizon": "quarter",
        "executor": "Служба качества / стандартизации (внутренний стандарт)",
        "inputs": [],
        "outputs": ["Норматив@МетодикОтбораПроб"],
        "kpi": "Актуальность методик (не реже 1 раза в квартал)",
        "decomposition": "ATOMIC",
    }),
    ("SL_QUAL-03-01", {
        "code": "SL_QUAL-03-01-05",
        "name": "Актуализация норматива погрузки ГП (внутренний стандарт)",
        "type": "Simple",
        "goal": "Норматив погрузки ГП актуализирован (внешний к SL_QUAL стандарт).",
        "horizon": "quarter",
        "executor": "Служба логистики / стандартизации (внутренний стандарт)",
        "inputs": [],
        "outputs": ["Норматив@Погрузки"],
        "kpi": "Актуальность норматива (не реже 1 раза в квартал)",
        "decomposition": "ATOMIC",
    }),
    ("SL_QUAL-04-01", {
        "code": "SL_QUAL-04-01-03",
        "name": "Внешняя претензия клиента или ТК",
        "type": "Simple",
        "goal": "Претензия внешнего контрагента (клиента / ТК) получена.",
        "horizon": "event",
        "executor": "Клиент / транспортная компания (внешний контур)",
        "inputs": [],
        "outputs": ["Уведомление@Претензия"],
        "kpi": "Регистрация претензии в день получения",
        "decomposition": "ATOMIC",
    }),
    ("SL_QUAL-04-02", {
        "code": "SL_QUAL-04-02-04",
        "name": "Договоры и ответы контрагента",
        "type": "Simple",
        "goal": "Договор с контрагентом и ответ на претензию получены.",
        "horizon": "event",
        "executor": "Контрагент: поставщик / ТК (внешний контур)",
        "inputs": [],
        "outputs": ["Документ@Договор", "Уведомление@ОтветНаПретензию"],
        "kpi": "Полнота и своевременность получения документов",
        "decomposition": "ATOMIC",
    }),
    ("SL_QUAL-04-02", {
        "code": "SL_QUAL-04-02-05",
        "name": "Направление претензии контрагенту",
        "type": "Joiner",
        "goal": "Претензия направлена контрагенту (поставщику / ТК).",
        "horizon": "event",
        "executor": "Контрагент: поставщик / ТК (исходящая претензия)",
        "inputs": ["Документ@Претензия"],
        "outputs": [],
        "kpi": "Направление претензии в установленный срок",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- SL_QUAL-01-01 intake control -------------------------------------------
    ("SL_QUAL-01-01-04", "SL_QUAL-01-01-02", "Норматив@МетодикОтбораПроб", "внутренний стандарт"),
    ("SL_LOG-01-01-02", "SL_QUAL-01-01-01", "Документ@ПриходныйОрдер", "приходный ордер (SL_LOG)"),
    ("QUAL-03-01-04", "SL_QUAL-01-01-01", "Норматив@ВходногоКонтроля", "перечень входного контроля (QUAL)"),
    ("SL_QUAL-01-01-01", "SL_QUAL-01-01-02", "Документ@РешениеОбОтбореПроб", "внутренний поток"),
    ("QUAL-03-01-08", "SL_QUAL-01-01-03", "Протокол@Испытаний", "результаты испытаний (QUAL)"),
    ("SL_QUAL-01-01-02", "QUAL-03-01-04", "Заявка@ВходнойКонтроль", "заявка на отбор проб (QUAL)"),
    ("SL_QUAL-01-01-02", "SL_LOG-01-01-04", "Уведомление@Кладовщику", "уведомление кладовщика (SL_LOG)"),
    ("SL_QUAL-01-01-03", "SL_LOG-01-01-09", "Разрешение@Годен", "решение о годности (SL_LOG)"),
    ("SL_QUAL-01-01-03", "QUAL-05-02-06", "Партия@Карантин", "карантин НСП (QUAL)"),

    # --- SL_QUAL-02-01 storage monitoring ---------------------------------------
    ("SL_LOG-01-02-09", "SL_QUAL-02-01-01", "Измерение@ТемператураВлажность", "показания датчиков (SL_LOG)"),
    ("SL_LOG-01-02-09", "SL_QUAL-02-01-01", "Норматив@УсловийХранения", "норматив условий (SL_LOG)"),
    ("SL_LOG-01-02-01", "SL_QUAL-02-01-02", "Запас@Склад", "запас на складе (SL_LOG)"),
    ("SL_QUAL-02-01-01", "SL_QUAL-02-02-01", "Протокол@КонтроляУсловий", "внутренний поток"),
    ("SL_QUAL-02-01-01", "SL_QUAL-02-02-02", "Протокол@КонтроляУсловий", "внутренний поток"),
    ("SL_QUAL-02-01-01", "ORG-01-04-03", "Протокол@КонтроляУсловий", "аудит условий (ORG)"),
    ("SL_QUAL-02-01-01", "ORG-01-04-03", "Документ@ЖурналКонтроля", "аудит условий (ORG)"),
    ("SL_QUAL-02-01-02", "SL_EMG-01-01-01", "Протокол@Осмотра", "акт осмотра (SL_EMG)"),

    # --- SL_QUAL-02-02 storage-deviation handling -------------------------------
    ("SL_LOG-01-02-09", "SL_QUAL-02-02-01", "Измерение@ТемператураВлажность", "показания датчиков (SL_LOG)"),
    ("SL_LOG-01-02-01", "SL_QUAL-02-02-02", "Запас@Склад", "запас на складе (SL_LOG)"),
    ("SL_QUAL-02-02-01", "ORG-01-04-03", "Документ@ЖурналНарушений", "аудит условий (ORG)"),
    ("SL_QUAL-02-02-01", "ORG-01-04-03", "Документ@МерыПоУстранению", "аудит условий (ORG)"),
    ("SL_QUAL-02-02-02", "ORG-01-04-03", "Протокол@СостоянияТМЦ", "аудит условий (ORG)"),
    ("SL_QUAL-02-02-02", "SL_QUAL-04-01-01", "Протокол@Несоответствия", "внутренний поток"),

    # --- SL_QUAL-03-01 shipping / loading control -------------------------------
    ("SL_MNT-03-01-01", "SL_QUAL-03-01-01", "ТранспортноеСредство", "парк ТС (SL_MNT)"),
    ("SL_QUAL-03-01-05", "SL_QUAL-03-01-01", "Норматив@Погрузки", "внутренний стандарт"),
    ("SL_QUAL-03-01-05", "SL_QUAL-03-01-02", "Норматив@Погрузки", "внутренний стандарт"),
    ("MFG-01-03-01", "SL_QUAL-03-01-02", "ГотоваяПродукция@Упакована", "упакованная ГП (MFG)"),
    ("SL_LOG-03-02-02", "SL_QUAL-03-01-03", "ТранспортноеСредство@Загружено", "загруженное ТС (SL_LOG)"),
    ("SL_QUAL-03-01-02", "SL_QUAL-03-01-03", "Документ@СхемаПогрузки", "внутренний поток"),
    ("SL_QUAL-03-01-01", "SL_QUAL-03-01-04", "Протокол@ОсмотраТС", "внутренний поток"),
    ("SL_QUAL-03-01-03", "SL_QUAL-03-01-04", "Протокол@КрепленияГруза", "внутренний поток"),
    ("SL_QUAL-03-01-01", "SL_LOG-02-03-01", "Разрешение@НаПогрузку", "разрешение на погрузку (SL_LOG)"),
    ("SL_QUAL-03-01-03", "ORG-01-04-03", "Документ@Фотофиксация", "аудит погрузки (ORG)"),
    ("SL_QUAL-03-01-04", "SL_LOG-02-03-02", "Уведомление@Отказе", "отказ в погрузке (SL_LOG)"),
    ("SL_QUAL-03-01-04", "SL_MNT-03-01-01", "Заявка@ЗаменаТС", "замена ТС (SL_MNT)"),
    ("SL_QUAL-03-01-04", "SL_LOG-02-03-02", "Заявка@Отклонение", "запрос отклонения (SL_LOG)"),

    # --- SL_QUAL-04-01 nonconformance registration ------------------------------
    ("SL_LOG-01-01-06", "SL_QUAL-04-01-01", "Уведомление@Претензия", "претензия поставщику (SL_LOG)"),
    ("SL_QUAL-04-01-03", "SL_QUAL-04-01-01", "Уведомление@Претензия", "претензия клиента/ТК (внешний контур)"),
    ("SL_QUAL-04-01-01", "SL_ANL-01-01-02", "Документ@РеестрНСП", "KPI хранения (SL_ANL)"),
    ("SL_QUAL-04-01-01", "SL_QUAL-04-01-02", "Протокол@НСП", "внутренний поток"),
    ("SL_QUAL-04-01-02", "SL_QUAL-04-02-01", "Протокол@НСП@Классифицировано", "внутренний поток"),
    ("SL_QUAL-04-01-02", "SL_LOG-04-01-02", "Норматив@КлассификацииВозвратов", "классификация НСП (SL_LOG)"),

    # --- SL_QUAL-04-02 investigation / claims -----------------------------------
    ("SL_QUAL-04-02-04", "SL_QUAL-04-02-02", "Документ@Договор", "договор с контрагентом (внешний контур)"),
    ("SL_QUAL-04-02-04", "SL_QUAL-04-02-03", "Уведомление@ОтветНаПретензию", "ответ на претензию (внешний контур)"),
    ("SL_LOG-01-01-12", "SL_QUAL-04-02-01", "Накладная", "документы приёмки (SL_LOG)"),
    ("SL_QUAL-04-02-01", "SL_QUAL-04-02-02", "Протокол@Расследования", "внутренний поток"),
    ("SL_QUAL-04-02-01", "SL_QUAL-06-01-01", "Протокол@Расследования", "внутренний поток"),
    ("SL_QUAL-04-02-01", "ORG-01-04-03", "Протокол@ЗаключениеОПричинах", "аудит расследований (ORG)"),
    ("SL_QUAL-04-02-02", "SL_QUAL-04-02-03", "Документ@РеестрПретензий", "внутренний поток"),
    ("SL_QUAL-04-02-02", "SL_QUAL-04-02-05", "Документ@Претензия", "исходящая претензия (внешний контур)"),
    ("SL_QUAL-04-02-03", "SL_ANL-01-01-02", "Протокол@НСП@Закрыто", "KPI хранения (SL_ANL)"),
    ("SL_QUAL-04-02-03", "SL_ANL-01-01-02", "Отчёт@ПретензионнаяРабота", "KPI хранения (SL_ANL)"),

    # --- SL_QUAL-06-01 root-cause / CAPA design ---------------------------------
    ("SL_ANL-03-01-01", "SL_QUAL-06-01-01", "Отчёт@ТрендыНСП", "тренды НСП (SL_ANL)"),
    ("SL_QUAL-06-01-01", "SL_QUAL-06-01-02", "Протокол@RCA", "внутренний поток"),
    ("SL_QUAL-06-01-01", "SL_QUAL-06-01-03", "Протокол@RCA", "внутренний поток"),
    ("SL_QUAL-06-01-02", "SL_QUAL-06-02-01", "План@КорректирующихДействий", "внутренний поток"),
    ("SL_QUAL-06-01-03", "SL_QUAL-06-02-01", "План@ПредупреждающихДействий", "внутренний поток"),

    # --- SL_QUAL-06-02 CAPA implementation / verification -----------------------
    ("SL_ANL-03-01-01", "SL_QUAL-06-02-02", "Отчёт@ТрендыНСП", "тренды НСП (SL_ANL)"),
    ("SL_QUAL-06-02-01", "SL_QUAL-06-02-02", "Документ@ЖурналCAPA", "внутренний поток"),
    ("SL_QUAL-06-02-01", "ORG-01-04-03", "СОП", "актуализация СОП (ORG)"),
    ("SL_QUAL-06-02-02", "SL_ANL-03-01-01", "Отчёт@РезультативностьCAPA", "результативность CAPA (SL_ANL)"),
    ("SL_QUAL-06-02-02", "ORG-01-04-03", "СОП@Актуализирован", "актуализация СОП (ORG)"),
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
        # find the host subprocess heading
        start = None
        for i, ln in enumerate(lines):
            m = SUB_RE.match(ln)
            if m and m.group(1) == host:
                start = i
                break
        if start is None:
            raise SystemExit(f"host subprocess {host} not found")
        # insert before the next heading of depth <= 4
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
    # drop an existing flow section
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
