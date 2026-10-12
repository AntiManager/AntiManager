"""Author the IMPR flow graph (T2.6 sub-step 3, continuous improvement).

Two idempotent operations on `IMPR.md`:

1. Insert the boundary operations (the external/reference contour: the employee
   idea feed, the corporate-media recognition channel and the external
   benchmarking sources) into their host subprocess sections.
2. Append the per-file «Потоки (Flow Links)» table closing every IMPR dangling
   I/O (internal IMPR->IMPR flow between proposal intake, expert review, kaizen
   workshop, project execution and benchmarking, plus cross-domain seams to
   PLAN / QUAL / ANLZ / EMG / ENV / ENG / HRP).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\IMPR.md")

# code -> (subprocess host, op dict). A boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("IMPR-01-01", {
        "code": "IMPR-01-01-04",
        "name": "Сотрудники — идеи и предложения по улучшению (контур авторов)",
        "type": "Simple",
        "goal": "Идеи и предложения от сотрудников доступны системе улучшений (внутренний контур авторов).",
        "horizon": "day",
        "executor": "Сотрудники / авторы предложений (внутренний контур)",
        "inputs": [],
        "outputs": ["Документ@ИдеяСотрудника"],
        "kpi": "Охват всех поступающих идей (100%)",
        "decomposition": "ATOMIC",
    }),
    ("IMPR-01-03", {
        "code": "IMPR-01-03-04",
        "name": "Доска почёта / корпоративные СМИ — публичное признание авторов (внешний контур)",
        "type": "Simple",
        "goal": "Публичное признание авторов улучшений размещено в корпоративных каналах (внешний контур).",
        "horizon": "month",
        "executor": "Корпоративные СМИ / доска почёта (внешний контур)",
        "inputs": ["Документ@ПубликацияОПризнании"],
        "outputs": [],
        "kpi": "Регулярность публикаций (ежемесячно)",
        "decomposition": "ATOMIC",
    }),
    ("IMPR-03-02", {
        "code": "IMPR-03-02-04",
        "name": "Внешний рынок практик: конференции, публикации, патенты, поставщики (внешний контур)",
        "type": "Simple",
        "goal": "Данные о передовых практиках отрасли доступны для бенчмаркинга (внешний контур).",
        "horizon": "quarter",
        "executor": "Внешние источники бенчмаркинга (внешний контур)",
        "inputs": [],
        "outputs": ["Отчёт@БенчмаркингДанные"],
        "kpi": "Полнота охвата внешних источников",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- IMPR-01-01 proposal intake (internal + boundary feed) -----------------
    ("IMPR-01-01-04", "IMPR-01-01-01", "Документ@ИдеяСотрудника", "идея от сотрудника (контур авторов)"),
    ("IMPR-01-01-01", "IMPR-01-01-02", "Заявка@НаУлучшение", "регистрация предложения (внутренний поток)"),
    ("IMPR-01-01-02", "IMPR-01-01-03", "Заявка@ПрошлаОтбор", "отбор к экспертизе (внутренний поток)"),
    ("IMPR-01-01-02", "IMPR-01-04-01", "Заявка@ПрошлаОтбор", "быстрые предложения в кайдзен (внутренний поток)"),

    # --- IMPR-01-02 expert review and decision (internal) ----------------------
    ("IMPR-01-01-03", "IMPR-01-02-01", "Заявка@НаЭкспертизе", "на техническую экспертизу (внутренний поток)"),
    ("IMPR-01-01-03", "IMPR-01-02-02", "Заявка@НаЭкспертизе", "на экономическую оценку (внутренний поток)"),
    ("IMPR-01-02-01", "IMPR-01-02-03", "Протокол@ТехническаяЭкспертиза", "техническое заключение (внутренний поток)"),
    ("IMPR-01-02-02", "IMPR-01-02-03", "Отчёт@ЭкономическийЭффект", "экономический расчёт (внутренний поток)"),
    ("IMPR-01-02-03", "IMPR-01-02-04", "Протокол@ЭкспертноеЗаключение", "итоговое заключение (внутренний поток)"),
    ("IMPR-01-02-04", "IMPR-02-01-01", "Документ@РешениеОЗапускеПроекта", "запуск проекта (внутренний поток)"),

    # --- IMPR-01-04 kaizen workshop (internal) ---------------------------------
    ("IMPR-01-04-01", "IMPR-01-04-02", "Документ@ПереченьЗадачКайдзен", "пул задач (внутренний поток)"),
    ("IMPR-01-04-02", "IMPR-01-04-03", "График@КайдзенСессии", "график сессии (внутренний поток)"),
    ("IMPR-01-04-03", "IMPR-01-04-04", "Протокол@КайдзенСессии", "протокол сессии (внутренний поток)"),
    ("IMPR-01-04-03", "IMPR-01-04-05", "Документ@РеализованноеУлучшение", "реализованное улучшение (внутренний поток)"),

    # --- IMPR-01-03 motivation (internal + media actor) ------------------------
    ("IMPR-01-04-04", "IMPR-01-03-01", "Документ@ПриказОПоощрении", "приказ о поощрении (внутренний поток)"),
    ("IMPR-01-03-01", "IMPR-01-03-02", "Документ@СлужебнаяЗапискаНаПремию", "расчёт к выплате (внутренний поток)"),
    ("IMPR-01-03-02", "IMPR-01-03-03", "Документ@ПремияВыплачена", "выплата подтверждена (внутренний поток)"),
    ("IMPR-01-03-03", "IMPR-01-03-04", "Документ@ПубликацияОПризнании", "публикация о признании (внешний контур)"),

    # --- IMPR-02 project planning (internal) -----------------------------------
    ("IMPR-02-01-01", "IMPR-02-01-02", "Документ@КомандаПроекта", "команда проекта (внутренний поток)"),
    ("IMPR-02-01-02", "IMPR-02-01-03", "Документ@ПаспортПроекта", "паспорт проекта (внутренний поток)"),
    ("IMPR-02-01-02", "IMPR-02-01-04", "Документ@ПаспортПроекта", "паспорт на защиту (внутренний поток)"),
    ("IMPR-02-01-03", "IMPR-02-01-04", "График@ПланГрафикПроекта", "план-график на защиту (внутренний поток)"),
    ("IMPR-02-01-04", "IMPR-02-02-01", "Документ@ПриказОНачалеРабот", "приказ о начале работ (внутренний поток)"),

    # --- IMPR-02 project execution (internal) ----------------------------------
    ("IMPR-02-02-01", "IMPR-02-02-02", "Протокол@СовещаниеПроекта", "итоги совещания (внутренний поток)"),
    ("IMPR-02-02-02", "IMPR-02-02-03", "АктСдачиПриёмки@Этап", "приёмка этапа (внутренний поток)"),
    ("IMPR-02-02-02", "IMPR-02-03-01", "АктСдачиПриёмки@Этап", "этапы к финальной приёмке (внутренний поток)"),
    ("IMPR-02-02-03", "IMPR-02-02-04", "План@ПроектСкорректирован", "скорректированный план (внутренний поток)"),
    ("IMPR-02-02-04", "IMPR-02-03-03", "Отчёт@ОтчётОХодеПроекта", "статусы для итогового отчёта (внутренний поток)"),

    # --- IMPR-02 project closure (internal + cross-domain out) -----------------
    ("IMPR-02-03-01", "IMPR-02-03-02", "АктСдачиПриёмки@Проект", "приёмка проекта (внутренний поток)"),
    ("IMPR-02-03-01", "IMPR-01-03-01", "АктСдачиПриёмки@Проект", "акт внедрения для мотивации (внутренний поток)"),
    ("IMPR-02-03-02", "IMPR-02-03-03", "Отчёт@ПостПроектныйАнализ", "пост-проектный анализ (внутренний поток)"),
    ("IMPR-02-03-02", "IMPR-01-03-01", "Отчёт@ПостПроектныйАнализ", "данные об эффекте для мотивации (внутренний поток)"),
    ("IMPR-02-03-03", "IMPR-02-03-04", "Отчёт@ФормаА3", "итоговый отчёт A3 (внутренний поток)"),
    ("IMPR-02-03-03", "HRP-01-08-02", "Отчёт@ФормаА3", "итоговый отчёт A3 в базу знаний (HRP)"),
    ("IMPR-02-03-04", "ENG-01-02-01", "Документ@Рацпредложение", "корректировка регламентов (ENG)"),

    # --- IMPR-03 benchmarking (internal + boundary source) ---------------------
    ("IMPR-03-02-04", "IMPR-03-02-01", "Отчёт@БенчмаркингДанные", "внешние данные бенчмаркинга (внешний контур)"),
    ("IMPR-03-02-04", "IMPR-03-02-02", "Отчёт@БенчмаркингДанные", "внешние публикации (внешний контур)"),
    ("IMPR-03-02-04", "IMPR-03-02-03", "Отчёт@БенчмаркингДанные", "опыт партнёров (внешний контур)"),

    # --- IMPR-03-01 internal ranking + cross-domain data in --------------------
    ("PLAN-02-03-03", "IMPR-03-01-01", "Отчёт@Утверждён", "сводная отчётность цехов (PLAN)"),
    ("QUAL-03-03-04", "IMPR-03-01-01", "Отчёт@Качество", "данные по качеству (QUAL)"),
    ("IMPR-03-01-01", "IMPR-03-01-02", "Сводка@ПоказателиПодразделений", "сводная база (внутренний поток)"),
    ("IMPR-03-01-02", "IMPR-03-01-03", "Отчёт@РейтингПодразделений", "рейтинг (внутренний поток)"),
    ("IMPR-03-01-03", "IMPR-03-03-01", "Документ@ЛидерыПоНаправлениям", "внутренние лидеры (внутренний поток)"),

    # --- IMPR-03-02 external benchmarking (internal) ---------------------------
    ("IMPR-03-02-01", "IMPR-03-03-01", "Отчёт@ОтраслевойОпыт", "отраслевой опыт (внутренний поток)"),
    ("IMPR-03-02-02", "IMPR-03-03-01", "Документ@ОбзорЛитературы", "обзор литературы (внутренний поток)"),
    ("IMPR-03-02-03", "IMPR-03-03-01", "Документ@ТехническоеПредложение", "технические предложения (внутренний поток)"),

    # --- IMPR-03-03 initiatives back into the proposal system ------------------
    ("IMPR-03-03-01", "IMPR-03-03-02", "Отчёт@GapАнализ", "gap-анализ (внутренний поток)"),
    ("IMPR-03-03-02", "IMPR-03-03-03", "Документ@АдаптацияПрактики", "предложения по адаптации (внутренний поток)"),
    ("IMPR-03-03-03", "IMPR-01-01-01", "Документ@ИнициативаБенчмаркинга", "инициативы в систему предложений (внутренний поток)"),

    # --- cross-domain out to ENG (rationalisation proposals) -------------------
    ("IMPR-01-01-01", "ENG-01-02-01", "Документ@Рацпредложение", "рацпредложение (ENG)"),
    ("IMPR-01-04-05", "ENG-01-02-01", "Документ@Рацпредложение", "тиражирование требует изменения стандарта (ENG)"),
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
