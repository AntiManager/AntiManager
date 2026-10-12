"""Author the ENG flow graph (T2.6 sub-step 3, technology preparation of production).

Two idempotent operations on `ENG.md`:

1. Insert the boundary operations (external / reference-contour sensors) into
   their host subprocess sections: the design documentation feed (external
   constructor/customer), the technology reference base (NSI, equipment
   passports, competence matrices, regime handbooks), the measurement contour
   (time studies, actual productivity, over-consumption claims) and the external
   standards feed (GOST/TU).
2. Append the per-file «Потоки (Flow Links)» table closing every ENG dangling
   I/O (internal ENG->ENG flow + cross-domain seams to PLAN / MNT / IMPR / QUAL /
   ANLZ / ORG / STRAT / MFG / INF).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\ENG.md")

# code -> (subprocess host, op dict). A boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("ENG-01-01", {
        "code": "ENG-01-01-06",
        "name": "Конструкторский отдел / заказчик — конструкторская документация (внешний контур)",
        "type": "Simple",
        "goal": "Конструкторская документация на новое или модернизируемое изделие доступна технологической службе (внешний контур).",
        "horizon": "event",
        "executor": "Конструкторский отдел / заказчик (внешний контур)",
        "inputs": [],
        "outputs": ["Чертёж"],
        "kpi": "Полнота и комплектность конструкторской документации",
        "decomposition": "ATOMIC",
    }),
    ("ENG-01-01", {
        "code": "ENG-01-01-07",
        "name": "Справочная база техподготовки: НСИ, паспорта оборудования, матрицы компетенций, режимы (справочный контур)",
        "type": "Simple",
        "goal": "Нормативно-справочная информация, паспорта оборудования, матрицы компетенций и справочники режимов доступны для проектирования техпроцесса (справочный контур).",
        "horizon": "day",
        "executor": "НСИ / справочная база техподготовки (справочный контур)",
        "inputs": [],
        "outputs": ["Норматив@ТиповойТехпроцесс", "Норматив@СправочникРежимов",
                    "Паспорт@Оборудования", "Документ@МатрицаКомпетенций"],
        "kpi": "Актуальность справочной базы (100%)",
        "decomposition": "ATOMIC",
    }),
    ("ENG-01-03", {
        "code": "ENG-01-03-05",
        "name": "Хронометраж, фактическая производительность и рекламации по перерасходу (контур измерений)",
        "type": "Simple",
        "goal": "Результаты хронометража, данные о фактической производительности и рекламации по перерасходу доступны для актуализации нормативов (контур измерений).",
        "horizon": "month",
        "executor": "Контур измерений / отчётность (внешний контур)",
        "inputs": [],
        "outputs": ["Протокол@Хронометраж", "Отчёт@ФактическаяПроизводительность",
                    "Документ@РекламацияПоПерерасходу"],
        "kpi": "Полнота данных о фактических показателях (100%)",
        "decomposition": "ATOMIC",
    }),
    ("ENG-01-04", {
        "code": "ENG-01-04-04",
        "name": "Внешние стандарты ГОСТ/ТУ (внешний контур)",
        "type": "Simple",
        "goal": "Действующие требования ГОСТ/ТУ на сырьё и материалы доступны для разработки входного контроля (внешний контур).",
        "horizon": "year",
        "executor": "Внешние стандарты ГОСТ/ТУ (внешний контур)",
        "inputs": [],
        "outputs": ["Норматив@ГОСТ"],
        "kpi": "Актуальность нормативной базы (пересмотр не реже 1 раза в год)",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- ENG-01-01 design and approval chain (internal) ------------------------
    ("ENG-01-01-01", "ENG-01-01-02", "Документ@ТехническоеЗадание", "ТЗ на разработку техпроцесса (внутренний поток)"),
    ("ENG-01-01-01", "ENG-01-01-04", "Документ@ОценкаТехнологичности", "оценка технологичности (внутренний поток)"),
    ("ENG-01-01-02", "ENG-01-01-03", "ТехнологическаяКарта", "техпроцесс на нормирование (внутренний поток)"),
    ("ENG-01-01-02", "ENG-01-01-04", "ТехнологическаяКарта", "техпроцесс на согласование (внутренний поток)"),
    ("ENG-01-01-02", "ENG-01-03-02", "ТехнологическаяКарта", "изменения в технологии (внутренний поток)"),
    ("ENG-01-01-02", "ENG-01-04-01", "ТехнологическаяКарта", "техпроцесс для входного контроля (внутренний поток)"),
    ("ENG-01-01-03", "ENG-01-01-04", "Норматив@НормыВремени", "результаты нормирования (внутренний поток)"),
    ("ENG-01-01-04", "ENG-01-01-05", "ТехнологическаяКарта@Утверждена", "утверждённый техпроцесс (внутренний поток)"),

    # --- ENG-01-01 boundary feeds ---------------------------------------------
    ("ENG-01-01-06", "ENG-01-01-01", "Чертёж", "конструкторская документация (внешний контур)"),
    ("ENG-01-01-07", "ENG-01-01-02", "Норматив@ТиповойТехпроцесс", "справочная база ТП (справочный контур)"),
    ("ENG-01-01-07", "ENG-01-01-02", "Паспорт@Оборудования", "паспорта оборудования (справочный контур)"),
    ("ENG-01-01-07", "ENG-01-01-02", "Документ@МатрицаКомпетенций", "матрица компетенций (справочный контур)"),
    ("ENG-01-01-07", "ENG-01-01-03", "Норматив@СправочникРежимов", "справочники режимов (справочный контур)"),
    ("ENG-01-01-07", "ENG-01-01-04", "Паспорт@Оборудования", "паспорта оборудования (справочный контур)"),
    ("ENG-01-01-07", "ENG-01-03-03", "Паспорт@Оборудования", "паспортные данные ТП (справочный контур)"),

    # --- ENG-01-02 change management (internal) --------------------------------
    ("ENG-01-02-01", "ENG-01-02-02", "Уведомление@Изменение", "извещение об изменении (внутренний поток)"),
    ("ENG-01-02-02", "ENG-01-02-03", "ТехнологическаяКарта@НоваяВерсия", "новая версия документа (внутренний поток)"),

    # --- ENG-01-03 NSI actualisation (internal) --------------------------------
    ("ENG-01-03-01", "ENG-01-03-02", "Отчёт@ОтклоненияРасхода", "записка об отклонениях (внутренний поток)"),
    ("ENG-01-03-02", "ENG-01-03-04", "ЗаявкаНаПересмотрНормативов", "предложения по нормам (внутренний поток)"),
    ("ENG-01-03-03", "ENG-01-03-04", "Норматив@ТехническаяПроизводительность", "утверждённая ТП (внутренний поток)"),
    ("ENG-01-03-05", "ENG-01-03-01", "Документ@РекламацияПоПерерасходу", "рекламации по перерасходу (контур измерений)"),
    ("ENG-01-03-05", "ENG-01-03-03", "Протокол@Хронометраж", "результаты хронометража (контур измерений)"),
    ("ENG-01-03-05", "ENG-01-03-03", "Отчёт@ФактическаяПроизводительность", "фактическая производительность (контур измерений)"),

    # --- ENG-01-04 incoming control norms (internal + external standard) --------
    ("ENG-01-04-01", "ENG-01-04-02", "Документ@ПроектТребованийВходногоКонтроля", "проект требований (внутренний поток)"),
    ("ENG-01-04-02", "ENG-01-04-03", "Документ@ПроектПеречняВходногоКонтроля", "проект перечня (внутренний поток)"),
    ("ENG-01-04-04", "ENG-01-04-01", "Норматив@ГОСТ", "ГОСТ/ТУ (внешний контур)"),

    # --- cross-domain inbound --------------------------------------------------
    ("PLAN-02-01-04", "ENG-01-03-01", "ДанныеОперативногоУчёта@Валидированы", "данные о выпуске и списании (PLAN)"),
    ("MNT-01-04-05", "ENG-01-01-04", "Документ@КарточкаОбъектаТОиР", "карточка объекта ТОиР (MNT)"),
    ("MNT-01-04-05", "ENG-01-01-04", "ТехнологическаяКарта@ОбъектаТОиР", "техкарта объекта ТОиР (MNT)"),
    ("IMPR-01-01-01", "ENG-01-02-01", "Документ@Рацпредложение", "рацпредложение (IMPR)"),
    ("QUAL-05-02-01", "ENG-01-02-01", "Протокол@Брак", "акт о браке (QUAL)"),
    ("MNT-05-01-03", "ENG-01-02-01", "Документ@КорректирующиеМероприятия", "предложения механиков (MNT)"),
    ("ANLZ-01-01-01", "ENG-01-03-02", "Отчёт@АнализОтклонений", "анализ отклонений (ANLZ)"),

    # --- cross-domain outbound -------------------------------------------------
    ("ENG-01-01-03", "ORG-01-02-01", "Норматив@НормыВремени", "нормы времени на утверждение (ORG)"),
    ("ENG-01-01-05", "MFG-03-01-01", "ТехнологическаяКарта@Визуализация", "визуализация критических параметров (MFG)"),
    ("ENG-01-02-03", "MFG-01-01-05", "ТехнологическаяКарта@Действующая", "актуальная документация (MFG)"),
    ("ENG-01-02-03", "INF-14-04-07", "Документ@Аннулировано", "аннулированные версии в архив (INF)"),
    ("ENG-01-03-04", "STRAT-01-01-01", "Норматив@Расхода", "нормы расхода (STRAT)"),
    ("ENG-01-03-04", "ANLZ-01-01-01", "Норматив@Расхода", "нормы расхода (ANLZ)"),
    ("ENG-01-03-04", "PLAN-01-02-01", "Норматив@Расхода", "нормы расхода (PLAN)"),
    ("ENG-01-04-03", "QUAL-03-01-01", "Норматив@ВходногоКонтроля", "перечень входного контроля (QUAL)"),
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
