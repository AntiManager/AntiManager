"""Author the SL_EMG flow graph (T2.6 sub-step 3, logistics emergencies).

Two idempotent operations on `SL_EMG.md`:

1. Insert the boundary operations (external-perimeter sensors/actors) into their
   host subprocess sections: the ДТП event, emergency services, ГИБДД documents,
   the insurance company, and the client return/refusal contour.
2. Append the per-file «Потоки (Flow Links)» table closing every SL_EMG dangling
   I/O (internal SL_EMG->SL_EMG flow + cross-domain seams to SL_LOG / SL_QUAL /
   SL_ANL).

Edges are same-token links (src.TOKEN -> dst.TOKEN). CRLF-preserving.
"""
import io
import re
import sys

FILE = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
        r"\library\SL_EMG.md")

# code -> (subprocess host, op dict). A boundary op is inserted at the end of
# its host subprocess section.
BOUNDARIES = [
    ("SL_EMG-02-01", {
        "code": "SL_EMG-02-01-03",
        "name": "Внешний контур: ДТП / авария ТС склада",
        "type": "Simple",
        "goal": "Факт ДТП/аварии с участием ТС склада зафиксирован (внешний контур).",
        "horizon": "event",
        "executor": "Внешний контур (ДТП/авария)",
        "inputs": [],
        "outputs": ["Уведомление@ОДТП"],
        "kpi": "Получение сообщения о ДТП",
        "decomposition": "ATOMIC",
    }),
    ("SL_EMG-02-01", {
        "code": "SL_EMG-02-01-04",
        "name": "Экстренные службы (скорая, МЧС) — внешний контур",
        "type": "Simple",
        "goal": "Вызов экстренных служб передан (внешний контур).",
        "horizon": "event",
        "executor": "Экстренные службы (внешний контур)",
        "inputs": ["Уведомление@ЭкстренныхСлужб"],
        "outputs": [],
        "kpi": "Своевременность вызова экстренных служб",
        "decomposition": "ATOMIC",
    }),
    ("SL_EMG-02-02", {
        "code": "SL_EMG-02-02-03",
        "name": "ГИБДД — документы о ДТП (внешний контур)",
        "type": "Simple",
        "goal": "Документы ГИБДД по ДТП получены (внешний контур).",
        "horizon": "event",
        "executor": "ГИБДД (внешний контур)",
        "inputs": [],
        "outputs": ["Документ@ПротоколГИБДД"],
        "kpi": "Наличие документов ГИБДД по каждому ДТП (100%)",
        "decomposition": "ATOMIC",
    }),
    ("SL_EMG-02-02", {
        "code": "SL_EMG-02-02-04",
        "name": "Страховая компания — заявление (внешний контур)",
        "type": "Simple",
        "goal": "Заявление в страховую компанию передано (внешний контур).",
        "horizon": "event",
        "executor": "Страховая компания (внешний контур)",
        "inputs": ["Заявка@ВСтраховую"],
        "outputs": [],
        "kpi": "Подача заявления в течение 1 дня",
        "decomposition": "ATOMIC",
    }),
    ("SL_EMG-03-01", {
        "code": "SL_EMG-03-01-04",
        "name": "Внешний контур: отказ клиента / возврат груза",
        "type": "Simple",
        "goal": "Отказ клиента и акт о возврате получены (внешний контур).",
        "horizon": "event",
        "executor": "Клиент / транспортная компания (внешний контур)",
        "inputs": [],
        "outputs": ["Уведомление@Претензия", "Документ@АктОВозврате"],
        "kpi": "Регистрация отказа/возврата в день получения",
        "decomposition": "ATOMIC",
    }),
]

# (src, dst, token, condition)
EDGES = [
    # --- SL_EMG-01 incident on the warehouse floor -----------------------------
    ("SL_EMG-01-01-01", "SL_EMG-01-01-02", "ЗоныХранения@Блокирована", "внутренний поток"),
    ("SL_EMG-01-01-02", "SL_EMG-01-02-01", "Протокол@Инцидента", "внутренний поток"),
    ("SL_EMG-01-01-02", "SL_QUAL-04-01-01", "Протокол@Несоответствия", "регистрация НСП (SL_QUAL)"),
    ("SL_EMG-01-02-01", "SL_EMG-01-02-02", "Документ@АктСписания", "внутренний поток"),
    ("SL_EMG-01-02-02", "SL_LOG-01-04-01", "Брак", "повреждённые ТМЦ в зону брака (SL_LOG)"),
    ("SL_LOG-01-01-02", "SL_EMG-01-02-01", "Документ@ПриходныйОрдер", "приходный ордер (SL_LOG)"),

    # --- SL_EMG-02 traffic accident --------------------------------------------
    ("SL_EMG-02-01-03", "SL_EMG-02-01-01", "Уведомление@ОДТП", "ДТП (внешний контур)"),
    ("SL_EMG-02-01-03", "SL_EMG-02-01-02", "Уведомление@ОДТП", "ДТП (внешний контур)"),
    ("SL_EMG-02-01-01", "SL_EMG-02-01-04", "Уведомление@ЭкстренныхСлужб", "вызов экстренных служб (внешний контур)"),
    ("SL_EMG-02-01-02", "SL_EMG-02-02-01", "Уведомление@НТС", "внутренний поток"),
    ("SL_EMG-02-01-02", "SL_EMG-02-02-02", "Уведомление@НТС", "внутренний поток"),
    ("SL_EMG-02-01-02", "SL_EMG-02-02-01", "Документ@Фотофиксация", "фотофиксация места ДТП"),
    ("SL_EMG-02-02-03", "SL_EMG-02-02-01", "Документ@ПротоколГИБДД", "документы ГИБДД (внешний контур)"),
    ("SL_EMG-02-02-01", "SL_EMG-02-02-04", "Заявка@ВСтраховую", "заявление в страховую (внешний контур)"),
    ("SL_LOG-03-01-05", "SL_EMG-02-02-02", "Измерение@GPS", "телематика ТС (SL_LOG)"),
    ("SL_EMG-02-02-02", "SL_ANL-01-01-02", "Протокол@Разбора", "данные по инцидентам (SL_ANL)"),
    ("SL_EMG-02-02-02", "SL_ANL-01-01-02", "План@Мероприятий", "профилактика инцидентов (SL_ANL)"),

    # --- SL_EMG-03 delivery incidents / returns --------------------------------
    ("SL_EMG-03-01-04", "SL_EMG-03-01-01", "Уведомление@Претензия", "отказ клиента (внешний контур)"),
    ("SL_EMG-03-01-04", "SL_EMG-03-01-01", "Документ@АктОВозврате", "акт о возврате (внешний контур)"),
    ("SL_EMG-03-01-04", "SL_EMG-03-01-02", "Документ@АктОВозврате", "акт о возврате (внешний контур)"),
    ("SL_EMG-03-01-01", "SL_EMG-03-01-02", "Протокол@РегистрацииВозврата", "внутренний поток"),
    ("SL_EMG-03-01-01", "SL_EMG-03-01-03", "Протокол@РегистрацииВозврата", "внутренний поток"),
    ("SL_EMG-03-01-02", "SL_EMG-03-01-03", "ТаймСлот@Согласован", "внутренний поток"),
    ("SL_EMG-03-01-02", "SL_LOG-03-01-01", "ЗаявкаНаПеревозку@Обратная", "обратная перевозка (SL_LOG)"),
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
