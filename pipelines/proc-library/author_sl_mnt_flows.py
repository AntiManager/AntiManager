"""Author the SL_MNT flow graph (T2.6 sub-step 3, logistics fleet maintenance).

Two idempotent operations on `SL_MNT.md`:

1. Insert the boundary operation (external-perimeter sensor) into its host
   subprocess section — the residual I/O the in-library domains do not provide:
   the regulatory requirements of Ростехнадзор (oversight of lifting equipment).
2. Append the per-file «Потоки (Flow Links)» table closing every SL_MNT dangling
   I/O (internal SL_MNT->SL_MNT flow + cross-domain seams to SL_LOG / MNT / INF /
   SL_ANL).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\SL_MNT.md")

# code -> (subprocess host, op dict). The boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("SL_MNT-02-02", {
        "code": "SL_MNT-02-02-03",
        "name": "Требования Ростехнадзора к освидетельствованию ГПМ (внешний контур)",
        "type": "Simple",
        "goal": "Нормативные требования и сроки освидетельствования ГПМ получены (внешний регулятор).",
        "horizon": "year",
        "executor": "Ростехнадзор (внешний регулятор)",
        "inputs": [],
        "outputs": ["Норматив@ТребованияРостехнадзора"],
        "kpi": "Актуальность нормативных требований (не реже 1 раза в год)",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- SL_MNT-01-01 scheduled maintenance / records ---------------------------
    ("SL_LOG-03-01-05", "SL_MNT-01-01-01", "Измерение@ПробегТопливо", "пробег ТС (SL_LOG)"),
    ("MNT-01-04-03", "SL_MNT-01-01-01", "СОП", "регламенты ТО (MNT)"),
    ("SL_MNT-01-01-01", "SL_MNT-02-01-02", "График@ТО", "график ТО (погрузчики)"),
    ("SL_MNT-01-01-01", "SL_MNT-02-02-01", "График@ТО", "график ТО (краны)"),
    ("SL_MNT-03-01-01", "SL_MNT-01-01-02", "ТранспортноеСредство", "парк ТС (SL_MNT)"),
    ("MNT-03-01-03", "SL_MNT-01-01-02", "ЗИП", "запчасти (MNT)"),
    ("SL_MNT-01-01-02", "SL_MNT-01-01-03", "Документ@ОтметкаОбУстранении", "внутренний поток"),
    ("SL_MNT-01-01-02", "SL_MNT-01-02-01", "Протокол@ДефектнойВедомости", "внутренний поток"),
    ("SL_MNT-01-02-02", "SL_MNT-01-01-03", "Протокол@ВыполненныхРабот", "внутренний поток"),
    ("SL_MNT-01-02-02", "SL_MNT-01-01-03", "Паспорт@ТС@Актуализирован", "внутренний поток"),
    ("SL_MNT-01-01-03", "SL_MNT-03-01-02", "Документ@КарточкаТС", "внутренний поток"),
    ("SL_MNT-01-01-03", "SL_ANL-02-01-01", "Отчёт@ЗатратыНаТО", "затраты на ТО (SL_ANL)"),

    # --- SL_MNT-01-02 overhaul --------------------------------------------------
    ("MNT-03-01-02", "SL_MNT-01-02-01", "Протокол@Диагностики", "диагностика (MNT)"),
    ("MNT-03-01-02", "SL_MNT-01-02-01", "Протокол@ДефектнойВедомости", "дефектная ведомость (MNT)"),
    ("SL_MNT-01-02-01", "MNT-03-01-03", "Заявка@НаЗапчасти", "заявка на запчасти (MNT)"),
    ("MNT-03-01-03", "SL_MNT-01-02-02", "ЗИП", "запчасти (MNT)"),
    ("MNT-01-04-03", "SL_MNT-01-02-02", "СОП@Ремонт", "СОП на ремонт (MNT)"),

    # --- SL_MNT-02-01 forklift maintenance --------------------------------------
    ("INF-04-01-02", "SL_MNT-02-01-01", "ГрузоподъёмныйМеханизм", "парк ГПМ (INF)"),
    ("MNT-01-04-02", "SL_MNT-02-01-01", "СОП@Чеклист", "чек-лист осмотра (MNT)"),
    ("SL_MNT-02-01-01", "SL_MNT-02-01-02", "Документ@ОтметкаИсправности", "внутренний поток"),
    ("SL_MNT-02-01-01", "MNT-03-01-01", "Заявка@Ремонт", "заявка на ремонт (MNT)"),
    ("MNT-03-01-03", "SL_MNT-02-01-02", "ЗИП", "запчасти (MNT)"),
    ("SL_MNT-02-01-02", "INF-04-02-05", "Протокол@ТО@Погрузчик", "учёт ТО ГПМ (INF)"),
    ("SL_MNT-02-01-02", "INF-04-02-05", "Паспорт@Погрузчик", "карточка ГПМ (INF)"),

    # --- SL_MNT-02-02 crane maintenance / certification -------------------------
    ("INF-04-01-02", "SL_MNT-02-02-01", "Паспорт@Кран", "паспорт ГПМ (INF)"),
    ("SL_MNT-02-02-01", "INF-04-02-05", "Протокол@ТО@Кран", "учёт ТО ГПМ (INF)"),
    ("SL_MNT-02-02-01", "INF-04-03-06", "Паспорт@Кран@Актуализирован", "обновление паспорта ГПМ (INF)"),
    ("INF-04-01-03", "SL_MNT-02-02-02", "График@Освидетельствования", "график осмотров ГПМ (INF)"),
    ("SL_MNT-02-02-03", "SL_MNT-02-02-02", "Норматив@ТребованияРостехнадзора", "требования регулятора (внешний контур)"),
    ("SL_MNT-02-02-02", "INF-04-02-02", "ГрузоподъёмныйМеханизм@ГотовКОСвидетельствованию", "ГПМ к освидетельствованию (INF)"),
    ("SL_MNT-02-02-02", "INF-04-02-02", "Протокол@Проверки", "протокол подготовки (INF)"),

    # --- SL_MNT-03-01 pre-trip control ------------------------------------------
    ("MNT-01-04-02", "SL_MNT-03-01-01", "СОП@Чеклист", "чек-лист предрейсового осмотра (MNT)"),
    ("SL_MNT-03-01-02", "SL_LOG-03-02-01", "Документ@ОтметкаОГотовности", "готовность ТС к выезду (SL_LOG)"),
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
