"""Author the SL_HRP flow graph (T2.6 sub-step 3, logistics personnel).

Two idempotent operations on `SL_HRP.md`:

1. Insert the boundary operations (external-perimeter sensors/actors) into their
   host subprocess sections — the residual I/O the in-library domains do not
   provide: the external labour market, external training providers, and the
   internal-standards / budget contour the logistics service consumes.
2. Append the per-file «Потоки (Flow Links)» table closing every SL_HRP dangling
   I/O (internal SL_HRP->SL_HRP flow + cross-domain seams to HRP / ORG / PLAN /
   SL_LOG / SL_MNT).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\SL_HRP.md")

# code -> (subprocess host, op dict). A boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("SL_HRP-01-01", {
        "code": "SL_HRP-01-01-03",
        "name": "Внутренние нормативы и заявки службы логистики (внутренний контур)",
        "type": "Simple",
        "goal": "Нормативы подбора/обучения и заявка на подбор получены (внутренний стандарт логистики).",
        "horizon": "year",
        "executor": "Внутренний стандарт службы логистики",
        "inputs": [],
        "outputs": ["Норматив@ТиповаяСтруктура", "Норматив@ПрофильДолжности",
                    "Норматив@ОбязательныеКурсы", "Норматив@ТребованияАттестации",
                    "Заявка@НаПодбор"],
        "kpi": "Актуальность нормативов (пересмотр при изменениях)",
        "decomposition": "ATOMIC",
    }),
    ("SL_HRP-01-01", {
        "code": "SL_HRP-01-01-04",
        "name": "Бюджет службы логистики (внутренний контур)",
        "type": "Simple",
        "goal": "Лимиты бюджета ФОТ и обучения службы логистики получены (внутренний контур).",
        "horizon": "year",
        "executor": "Финансовая служба (внутренний контур)",
        "inputs": [],
        "outputs": ["Бюджет@ФОТ", "Бюджет@Обучение"],
        "kpi": "Соблюдение лимитов бюджета службы логистики",
        "decomposition": "ATOMIC",
    }),
    ("SL_HRP-01-02", {
        "code": "SL_HRP-01-02-04",
        "name": "Внешний рынок труда — резюме кандидатов (внешний контур)",
        "type": "Simple",
        "goal": "Резюме кандидатов получены с внешнего рынка труда (внешний контур).",
        "horizon": "event",
        "executor": "Внешний рынок труда",
        "inputs": [],
        "outputs": ["Кандидат@Резюме"],
        "kpi": "Поток релевантных резюме (в установленные сроки)",
        "decomposition": "ATOMIC",
    }),
    ("SL_HRP-01-02", {
        "code": "SL_HRP-01-02-05",
        "name": "Внешние площадки по подбору персонала (внешний контур)",
        "type": "Simple",
        "goal": "Вакансия передана на внешние площадки подбора (внешний контур).",
        "horizon": "event",
        "executor": "Внешние площадки по подбору персонала",
        "inputs": ["Вакансия@Опубликована"],
        "outputs": [],
        "kpi": "Размещение вакансии на площадках (в течение 3 дней)",
        "decomposition": "ATOMIC",
    }),
    ("SL_HRP-02-01", {
        "code": "SL_HRP-02-01-03",
        "name": "Внешний обучающий центр — договор (внешний контур)",
        "type": "Simple",
        "goal": "Договор на обучение передан внешнему обучающему центру (внешний контур).",
        "horizon": "event",
        "executor": "Внешний обучающий центр",
        "inputs": ["Документ@ДоговорОбучения"],
        "outputs": [],
        "kpi": "Заключение договора до начала периода обучения",
        "decomposition": "ATOMIC",
    }),
    ("SL_HRP-02-02", {
        "code": "SL_HRP-02-02-03",
        "name": "Внешний обучающий центр — удостоверения (внешний контур)",
        "type": "Simple",
        "goal": "Удостоверения/сертификаты о прохождении обучения получены от внешнего центра.",
        "horizon": "year",
        "executor": "Внешний обучающий центр / аттестационная комиссия",
        "inputs": [],
        "outputs": ["Сертификат@Удостоверение"],
        "kpi": "Действующие удостоверения у 100% обученного персонала",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- SL_HRP-01-01 staff structure ------------------------------------------
    ("ORG-01-02-02", "SL_HRP-01-01-01", "Норматив@НормыТруда", "нормы труда (ORG)"),
    ("HRP-01-04-02", "SL_HRP-01-01-01", "Документ@ДолжностнаяИнструкция", "проект штатного расписания (HRP)"),
    ("SL_HRP-01-01-03", "SL_HRP-01-01-01", "Норматив@ТиповаяСтруктура", "типовая структура (внутренний стандарт)"),
    ("SL_HRP-01-01-01", "SL_HRP-01-01-02", "ПотребностьВРесурсах@Персонал", "внутренний поток"),
    ("SL_HRP-01-01-04", "SL_HRP-01-01-02", "Бюджет@ФОТ", "бюджет ФОТ (внутренний контур)"),

    # --- SL_HRP-01-02 recruitment ----------------------------------------------
    ("SL_HRP-01-01-03", "SL_HRP-01-02-01", "Заявка@НаПодбор", "заявка на подбор (внутренний контур)"),
    ("SL_HRP-01-01-03", "SL_HRP-01-02-01", "Норматив@ПрофильДолжности", "профиль должности (внутренний стандарт)"),
    ("SL_HRP-01-02-01", "SL_HRP-01-02-05", "Вакансия@Опубликована", "внешние площадки подбора"),
    ("SL_HRP-01-02-04", "SL_HRP-01-02-02", "Кандидат@Резюме", "резюме кандидатов (внешний рынок труда)"),
    ("SL_HRP-01-01-03", "SL_HRP-01-02-02", "Норматив@ПрофильДолжности", "профиль должности (внутренний стандарт)"),
    ("SL_HRP-01-02-02", "SL_HRP-01-02-03", "Кандидат@Отобран", "внутренний поток"),
    ("HRP-01-01-06", "SL_HRP-01-02-03", "Документ@RACI", "матрица компетенций (HRP)"),
    ("HRP-01-04-02", "SL_HRP-01-02-03", "Документ@ДолжностнаяИнструкция", "должностная инструкция (HRP)"),
    ("SL_HRP-01-02-03", "HRP-01-05-01", "Сотрудник@Ознакомлен", "адаптация нового сотрудника (HRP)"),

    # --- SL_HRP-02-01 training planning ----------------------------------------
    ("SL_HRP-01-02-03", "SL_HRP-02-01-01", "Сотрудник@Оформлен", "внутренний поток"),
    ("SL_HRP-01-01-03", "SL_HRP-02-01-01", "Норматив@ОбязательныеКурсы", "обязательные курсы (внутренний стандарт)"),
    ("SL_HRP-02-01-01", "SL_HRP-02-01-02", "План@Обучения", "внутренний поток"),
    ("SL_HRP-01-01-04", "SL_HRP-02-01-02", "Бюджет@Обучение", "бюджет обучения (внутренний контур)"),
    ("SL_HRP-02-01-02", "SL_HRP-02-01-03", "Документ@ДоговорОбучения", "договор с обучающим центром"),
    ("SL_HRP-02-01-02", "SL_HRP-02-02-01", "План@Обучения@Утверждён", "внутренний поток"),
    ("SL_HRP-02-01-02", "SL_HRP-02-02-01", "Документ@ДоговорОбучения", "внутренний поток"),

    # --- SL_HRP-02-02 training / attestation -----------------------------------
    ("SL_HRP-02-02-03", "SL_HRP-02-02-01", "Сертификат@Удостоверение", "удостоверения (внешний центр)"),
    ("SL_HRP-02-02-01", "SL_HRP-02-02-02", "Сотрудник@Обучен", "внутренний поток"),
    ("HRP-01-03-02", "SL_HRP-02-02-02", "График@Аттестации", "график аттестации (HRP)"),
    ("SL_HRP-01-01-03", "SL_HRP-02-02-02", "Норматив@ТребованияАттестации", "требования аттестации (внутренний стандарт)"),
    ("SL_HRP-02-02-02", "HRP-01-03-04", "Сотрудник@Аттестован", "база квалификации персонала (HRP)"),
    ("SL_HRP-02-02-02", "SL_MNT-03-01-01", "Разрешение@Допуск", "допуск водителя к рейсу (SL_MNT)"),

    # --- SL_HRP-03-01 shift planning -------------------------------------------
    ("SL_HRP-01-01-02", "SL_HRP-03-01-01", "Документ@ШтатноеРасписание", "внутренний поток"),
    ("PLAN-01-03-04", "SL_HRP-03-01-01", "СменносуточноеЗадание", "сменно-суточное задание (PLAN)"),
    ("ORG-01-02-02", "SL_HRP-03-01-01", "Норматив@НормыТруда", "нормы труда (ORG)"),
    ("SL_HRP-03-01-01", "SL_HRP-03-01-02", "ПотребностьВРесурсах@Смены", "внутренний поток"),
    ("SL_HRP-01-02-03", "SL_HRP-03-01-02", "Сотрудник@Оформлен", "внутренний поток"),
    ("SL_HRP-03-01-02", "SL_LOG-01-01-01", "График@Смен", "персонал на смене (SL_LOG)"),
    ("SL_HRP-03-01-02", "SL_LOG-02-01-01", "График@Смен", "персонал на смене (SL_LOG)"),
    ("SL_HRP-03-01-02", "SL_LOG-03-01-01", "График@Смен", "персонал на смене (SL_LOG)"),
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
