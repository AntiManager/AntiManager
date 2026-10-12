"""Author the QUAL flow graph (T2.6 sub-step 3, quality management).

Three idempotent operations on `QUAL.md`:

1. Insert the boundary operations — the enterprise perimeter and downstream
   in-library contours: sensors (external normative/legislation contour, external
   customer and SMK initiators, asset/stock registry, production programme,
   HRP personnel data, supplier source documents, certification/labs reference,
   NSP sources, analysis inputs, QMS documentation base) and actors (finance and
   procurement, ЦСМ metrology, HRP training, quality-service operating documents,
   management reporting, production contour, sales and warehouse, УСИС/АИЛ
   dispatch, SL_LOG logistics, supplier claims, NSP actions, customer/recall,
   investigation commission, audit group, QMS archive).

2. Append the per-file «Потоки (Flow Links)» table closing every QUAL dangling
   I/O: internal QUAL→QUAL flow (token-matched), cross-domain seams to the typed
   domains (ENG/MFG/SL_LOG/SL_QUAL/SL_PLAN/HRP/MNT/PLAN/IMPR/EMG/SL_ANL) and the
   STRAT forward seam, plus boundary links to the sensors/actors above.

Edge generation is data-driven from the declared I/O of the 147 typed QUAL
operations plus the explicit cross-domain lists below; it is deterministic and
re-runnable. CRLF-preserving.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine  # noqa: E402

VAULT = r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"
FILE = os.path.join(VAULT, "library", "QUAL.md")

# --------------------------------------------------------------------------
# Boundary operations: (host subprocess code, op dict).
# Sensors declare only `outputs`; actors declare only `inputs`.
# --------------------------------------------------------------------------
BOUNDARIES = [
    ("QUAL-01-01", {
        "code": "QUAL-01-01-06",
        "name": "Внешние нормативы, стандарты и законодательство (внешний контур)",
        "type": "Simple",
        "goal": "Действующие внешние нормативы и стандарты качества (НД, ГОСТ/ISO, законодательство, методики) доступны системе качества (внешний контур).",
        "horizon": "year",
        "executor": "Внешние регуляторы / органы стандартизации (внешний контур)",
        "inputs": [],
        "outputs": ["Норматив@НД", "Норматив@ISO9001",
                    "Норматив@ИзмененияЗаконодательства",
                    "Норматив@ТребованияСтандарта", "Норматив@МатрицаРисков",
                    "Норматив@КритерииПриемлемости", "Норматив@НаПродукцию",
                    "Норматив@МетодыКонтроля",
                    "Норматив@ЧекЛистПериодическогоКонтроля",
                    "Норматив@ЧекЛистТехническойДисциплины",
                    "Норматив@ОхранаТруда", "Норматив@МетодикИспытаний",
                    "Норматив@ТребованияСлужбыКачества",
                    "СОП@МетодикаИспытаний", "СОП@Методика",
                    "Документ@СТО", "Документ@Положение"],
        "kpi": "Полнота и актуальность внешней нормативной базы",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-01-01", {
        "code": "QUAL-01-01-07",
        "name": "Внешний заказчик, УПЛ и инициаторы СМК (внешний контур)",
        "type": "Simple",
        "goal": "Требования заказчика, решения о запуске продукции и инициативы по СМК доступны службе качества (внешний контур).",
        "horizon": "year",
        "executor": "Внешний заказчик / УПЛ / инициаторы (внешний контур)",
        "inputs": [],
        "outputs": ["Документ@ТребованияЗаказчика",
                    "Документ@РешениеОЗапускеПродукции", "Заявка@НаДокумент",
                    "Уведомление@ИзменениеПроцесса",
                    "Документ@ИнформацияПодразделений",
                    "Документ@ВнешниеФакторы", "Документ@ЛучшиеПрактики"],
        "kpi": "Полнота сбора внешних требований и инициатив",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-01-02", {
        "code": "QUAL-01-02-05",
        "name": "Реестр оборудования, СИ и остатков склада (учётная база)",
        "type": "Simple",
        "goal": "Данные учётных систем об оборудовании, СИ и остатках склада доступны службе качества (учётная база).",
        "horizon": "quarter",
        "executor": "Учётные системы / ЕРП (учётная база)",
        "inputs": [],
        "outputs": ["Оборудование@СИ", "ДанныеОперативногоУчёта@ОстаткиСклада",
                    "ДанныеОперативногоУчёта@КонтрольОТК"],
        "kpi": "Полнота и актуальность учётных данных",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-01-03", {
        "code": "QUAL-01-03-07",
        "name": "Производственный контур — производственная программа и график",
        "type": "Simple",
        "goal": "Производственная программа и график производства доступны для планирования контроля качества.",
        "horizon": "year",
        "executor": "Планово-экономический / производственный контур",
        "inputs": [],
        "outputs": ["ГрафикПроизводства", "План@Инвестиций"],
        "kpi": "Актуальность производственной программы",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-02-01", {
        "code": "QUAL-02-01-07",
        "name": "HRP — данные по персоналу и трудовому распорядку",
        "type": "Simple",
        "goal": "Данные по персоналу и внутреннему трудовому распорядку доступны службе качества (кадровый контур).",
        "horizon": "year",
        "executor": "HRP / кадровая служба",
        "inputs": [],
        "outputs": ["Документ@ПравилаВнутреннегоТрудовогоРаспорядка",
                    "Отчёт@ОценкаПерсонала"],
        "kpi": "Полнота кадровых данных",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-03-01", {
        "code": "QUAL-03-01-09",
        "name": "Внешний поставщик — сопроводительные документы и отгрузка сырья/материалов",
        "type": "Simple",
        "goal": "Сопроводительные документы и поставленные сырьё/материалы от внешних поставщиков доступны входному контролю.",
        "horizon": "event",
        "executor": "Внешний поставщик (внешний контур)",
        "inputs": [],
        "outputs": ["Сертификат@Отсутствует", "Материал@Получен"],
        "kpi": "Полнота сопроводительных документов",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-04-01", {
        "code": "QUAL-04-01-07",
        "name": "УСИС и АИЛ — исходные данные сертификации и испытаний (внешний контур)",
        "type": "Simple",
        "goal": "Исходные данные внешней сертификации и испытаний (план, сведения об АИЛ, перечень документации УСИС) доступны службе качества.",
        "horizon": "year",
        "executor": "УСИС / аккредитованные испытательные лаборатории (внешний контур)",
        "inputs": [],
        "outputs": ["План@СертификационныхИспытаний", "Документ@ИнформацияОбАИЛ",
                    "Документ@ПереченьДокументацииУСИС"],
        "kpi": "Актуальность внешних требований к сертификации",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-05-01", {
        "code": "QUAL-05-01-05",
        "name": "Источники НСП — брак производства и склада, паспорта, решения о возврате",
        "type": "Simple",
        "goal": "Сигналы о несоответствующей продукции (брак, паспорта качества, решения о возврате) поступают в управление НСП.",
        "horizon": "event",
        "executor": "Производство / склад / внешний контур (источники НСП)",
        "inputs": [],
        "outputs": ["Брак@Производства", "Брак@Склад", "Паспорт@Качества",
                    "Документ@РешениеОВозврате"],
        "kpi": "Полнота регистрации сигналов НСП",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-06-01", {
        "code": "QUAL-06-01-08",
        "name": "Смежные процессы — сводные данные для анализа качества",
        "type": "Simple",
        "goal": "Сводные данные смежных процессов (НСП, претензии, проверки, статусы КД, риски) доступны регулярному анализу качества.",
        "horizon": "month",
        "executor": "Смежные процессы (PLAN / MFG / SL_QUAL / ANLZ / HRP)",
        "inputs": [],
        "outputs": ["Отчёт@НСП", "Отчёт@Претензии", "Отчёт@ЧекЛисты",
                    "Протокол@КД", "Отчёт@ВнутренниеПроверки",
                    "Протокол@СтатусКД", "Протокол@СтатусВыполненияКД",
                    "Документ@ИзмененияВПроцессах", "Протокол@Интервью",
                    "График@ЗагрузкиАудиторов", "РеестрРисков@ОписаниеРиска"],
        "kpi": "Полнота входных данных анализа",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-08-01", {
        "code": "QUAL-08-01-05",
        "name": "База документации СМК — действующие документы и рассылка",
        "type": "Simple",
        "goal": "Действующая документация СМК, лучшие практики и списки рассылки доступны для разработки и актуализации документов.",
        "horizon": "quarter",
        "executor": "Владельцы процессов СМК / архив документации",
        "inputs": [],
        "outputs": ["Документ@ДокументацияСМК", "Документ@ДействующаяДокументация",
                    "Документ@СписокРассылки", "Уведомление@ЗаменаДокумента",
                    "Документ@ПереченьМестХранения"],
        "kpi": "Актуальность базы документации СМК",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-01-02", {
        "code": "QUAL-01-02-06",
        "name": "Финансово-экономическая служба и закупки — бюджеты и заявки на закуп",
        "type": "Simple",
        "goal": "Бюджеты службы качества, план закупок и заявки на закуп сырья/материалов переданы финансово-экономической службе (внешний контур).",
        "horizon": "year",
        "executor": "Финансово-экономическая служба / отдел закупок (внешний контур)",
        "inputs": ["Бюджет@БИЗ", "План@Закупок", "ЗаявкаНаЗакуп@ДокументыНаСырьё",
                   "ЗаявкаНаЗакуп@ДокументыНаМатериалы"],
        "outputs": [],
        "kpi": "Своевременность передачи бюджетов и заявок",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-01-03", {
        "code": "QUAL-01-03-08",
        "name": "ЦСМ — внешняя поверка и списание СИ (внешний контур)",
        "type": "Simple",
        "goal": "Согласованный график поверки и списанные СИ переданы ЦСМ (внешний контур).",
        "horizon": "quarter",
        "executor": "ЦСМ / государственная метрологическая служба (внешний контур)",
        "inputs": ["График@Поверки@Согласован", "Протокол@СписанияСИ"],
        "outputs": [],
        "kpi": "Своевременность передачи данных о поверке",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-02-01", {
        "code": "QUAL-02-01-08",
        "name": "HRP — заявки на обучение и материалы развития персонала",
        "type": "Simple",
        "goal": "Заявки на обучение и материалы развития персонала службы качества переданы в HRP.",
        "horizon": "month",
        "executor": "HRP / служба обучения",
        "inputs": ["План@Адаптации", "СОП@ПрограммаОбучения",
                   "График@ПроверкиЗнаний", "Отчёт@СоответствиеПерсонала",
                   "ЗаявкаНаОбучение@Внеплановое"],
        "outputs": [],
        "kpi": "Своевременность передачи заявок на обучение",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-02-01", {
        "code": "QUAL-02-01-09",
        "name": "Подразделения службы качества — операционные документы",
        "type": "Simple",
        "goal": "Операционные документы службы качества (графики, задания, формы, инструкции) доведены до подразделений.",
        "horizon": "month",
        "executor": "Подразделения службы качества",
        "inputs": ["График@Сменности", "СменноеЗадание", "Документ@Табель",
                   "Заявка@НаСпецодежду", "Документ@ФормаЖурнала",
                   "Норматив@ОбразецМаркировки", "Документ@ЛистОзнакомления",
                   "СОП@Инструкция@Доведена",
                   "Документ@МатрицаКомпетенций@Актуализирована"],
        "outputs": [],
        "kpi": "100% доведение операционных документов",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-02-01", {
        "code": "QUAL-02-01-10",
        "name": "Руководство производства — отчётность по качеству и решения",
        "type": "Simple",
        "goal": "Управленческая отчётность по качеству и НСП принята руководством производства (внешний контур управления).",
        "horizon": "month",
        "executor": "Руководство производства (внутренний контур управления)",
        "inputs": ["Отчёт@РаботаОТК", "Отчёт@РезультативностьСМК",
                   "Показатель@ЗагруженностьПерсонала",
                   "Показатель@СтатистикаИспытаний",
                   "Протокол@ТехнологическихРежимов", "Сводка@Сменная",
                   "Протокол@ЧекЛистОперационногоКонтроля",
                   "Протокол@ЧекЛистПериодическогоКонтроля",
                   "Отчёт@СводныйЗаНеделю",
                   "Протокол@ЧекЛистТехническойДисциплины",
                   "Протокол@ВерификацииКД", "Отчёт@СистемныеДефектыИПричины",
                   "Уведомление@НачальникуОТК", "Уведомление@Руководителям",
                   "Протокол@ОтметкиОВыполнении",
                   "Отчёт@РезультативностьРасследования", "Протокол@СтатусыКД",
                   "Отчёт@ПовторяемостьПроблем", "Протокол@Наблюдения",
                   "План@МероприятийПоРискам@Выполнен",
                   "Отчёт@ЗаключениеОСниженииРиска", "Отчёт@АнализСМК",
                   "ДанныеОперативногоУчёта@КонтрольОТК"],
        "outputs": [],
        "kpi": "Принятие отчётности и решений руководством",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-03-01", {
        "code": "QUAL-03-01-10",
        "name": "Производственный контур — принятые сырьё и материалы",
        "type": "Simple",
        "goal": "Проверенное сырьё, маркировка соответствия и разрешения на использование материалов переданы производственному контуру.",
        "horizon": "event",
        "executor": "Производственный контур (MFG)",
        "inputs": ["Сырьё@Проверено", "Этикетка@СоответствияСырья",
                   "Разрешение@НаИспользованиеМатериалов"],
        "outputs": [],
        "kpi": "Своевременность передачи принятых ресурсов",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-03-05", {
        "code": "QUAL-03-05-04",
        "name": "Склад и отдел сбыта — паспорт качества и передача продукции",
        "type": "Simple",
        "goal": "Зарегистрированный паспорт качества и отметки о передаче продукции переданы складу и отделу сбыта.",
        "horizon": "event",
        "executor": "Склад / отдел сбыта (SL_LOG)",
        "inputs": ["График@ПериодическихИспытаний@Актуализирован",
                   "График@ПериодическихИспытаний@СОтметками",
                   "Паспорт@Зарегистрирован", "Документ@ОтметкаОПередаче"],
        "outputs": [],
        "kpi": "Своевременность передачи паспортов и отметок",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-04-01", {
        "code": "QUAL-04-01-08",
        "name": "УСИС / АИЛ — отправка образцов и документов (внешний контур)",
        "type": "Simple",
        "goal": "Уведомления об отправке образцов и документов переданы УСИС / аккредитованным лабораториям.",
        "horizon": "event",
        "executor": "УСИС / АИЛ (внешний контур)",
        "inputs": ["Уведомление@ИЛ", "Уведомление@ОбОтправкеДокументов"],
        "outputs": [],
        "kpi": "Своевременность отправки документов",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-04-01", {
        "code": "QUAL-04-01-09",
        "name": "Транспорт и склад (SL_LOG) — перемещение образцов и продукции",
        "type": "Simple",
        "goal": "Накладные на перемещение образцов и продукции переданы транспортно-складскому контуру.",
        "horizon": "event",
        "executor": "Транспорт / склад (SL_LOG)",
        "inputs": ["Накладная@Перемещение"],
        "outputs": [],
        "kpi": "Своевременность оформления перемещений",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-05-01", {
        "code": "QUAL-05-01-06",
        "name": "Внешний поставщик — претензионная работа по НСП",
        "type": "Simple",
        "goal": "Претензионные документы по несоответствующему сырью/материалам переданы внешнему поставщику и отделу закупок.",
        "horizon": "event",
        "executor": "Внешний поставщик / отдел закупок (внешний контур)",
        "inputs": ["Документ@АктТОРГ2", "Уведомление@ОтделЗакупок",
                   "Документ@ПретензионныйАкт"],
        "outputs": [],
        "kpi": "Своевременность претензионной работы",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-05-02", {
        "code": "QUAL-05-02-08",
        "name": "Склад, производство и экология — действия с НСП",
        "type": "Simple",
        "goal": "Решения и документы по действиям с НСП (перевод в отходы, списание, перемещение, доработка) переданы складскому, производственному и экологическому контуру.",
        "horizon": "event",
        "executor": "Склад / производство / экология (ENV)",
        "inputs": ["Документ@АктПереводаВОтходы",
                   "ДанныеОперативногоУчёта@ЭтапПроизводства",
                   "ДанныеОперативногоУчёта@НСП", "Документ@СписаниеПродукции",
                   "ГотоваяПродукция@Исправлена", "Документ@РешениеПоПриёмке",
                   "Документ@ЖурналНСП"],
        "outputs": [],
        "kpi": "Полнота отработки решений по НСП",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-05-04", {
        "code": "QUAL-05-04-12",
        "name": "Внешний клиент — ответ на претензию и отзыв продукции",
        "type": "Simple",
        "goal": "Ответ заявителю и решение об отзыве отгруженной продукции переданы внешнему клиенту (внешний контур).",
        "horizon": "event",
        "executor": "Внешний клиент (внешний контур)",
        "inputs": ["Документ@РешениеНаОтзывПродукции", "Уведомление@ОтветКлиенту"],
        "outputs": [],
        "kpi": "Своевременность ответа и отзыва",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-06-02", {
        "code": "QUAL-06-02-05",
        "name": "Комиссия по расследованию — состав и совещания",
        "type": "Simple",
        "goal": "Состав комиссии, уведомления и график совещаний по критическому инциденту доведены до участников.",
        "horizon": "event",
        "executor": "Комиссия по расследованию инцидента",
        "inputs": ["Документ@СоставКомиссии", "Уведомление@Комиссии",
                   "График@Совещания"],
        "outputs": [],
        "kpi": "Своевременность оповещения комиссии",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-07-02", {
        "code": "QUAL-07-02-05",
        "name": "Аудиторская группа — приказы и состав",
        "type": "Simple",
        "goal": "Приказ об аудите и состав аудиторской группы доведены до участников аудита.",
        "horizon": "event",
        "executor": "Аудиторская группа",
        "inputs": ["Документ@ПриказОАудите", "Документ@СоставГруппы"],
        "outputs": [],
        "kpi": "Своевременность назначения аудита",
        "decomposition": "ATOMIC",
    }),
    ("QUAL-08-02", {
        "code": "QUAL-08-02-05",
        "name": "Архив СМК — реестры, контрольные копии и планы в архив",
        "type": "Simple",
        "goal": "Реестры документации, контрольные копии, аннулированные документы и утверждённые планы переданы в архив СМК.",
        "horizon": "quarter",
        "executor": "Архив / канцелярия СМК",
        "inputs": ["План@КорректирующихДействий@Утверждён", "Документ@РеестрКД",
                   "План@ПрограммаАудитов", "Документ@ЗаданиеНаРазработку",
                   "Документ@ВведёнВДействие", "Документ@РеестрДокументации",
                   "Документ@КонтрольнаяКопия", "Документ@Аннулирован",
                   "Документ@Архив", "Документ@ИзмененияУтверждены"],
        "outputs": [],
        "kpi": "Полнота архивирования документации",
        "decomposition": "ATOMIC",
    }),
]

# --------------------------------------------------------------------------
# Cross-domain seams.
# --------------------------------------------------------------------------
# QUAL dangling outputs consumed by a typed op in another domain.
CROSS_OUT = [
    ("QUAL-01-03-02", "HRP-01-03-02", "График@Аттестации", "график аттестации СИ (HRP)"),
    ("QUAL-02-01-01", "MNT-03-03-01", "График@Отпусков", "график отпусков персонала (MNT)"),
    ("QUAL-05-02-03", "HRP-01-01-01", "ЗаявкаНаОбучение", "заявка на обучение по НСП (HRP)"),
    ("QUAL-05-04-07", "HRP-01-01-01", "ЗаявкаНаОбучение", "заявка на обучение по НСП (HRP)"),
    ("QUAL-05-05-03", "HRP-01-01-01", "ЗаявкаНаОбучение", "заявка на обучение по НСП (HRP)"),
    ("QUAL-06-01-02", "HRP-02-03-03", "Документ@ПриказОКомиссии", "приказ о комиссии (HRP)"),
    ("QUAL-06-01-03", "HRP-02-03-04", "Протокол@Осмотра", "протокол осмотра (HRP)"),
    ("QUAL-06-02-01", "SL_EMG-02-02-01", "Документ@Фотофиксация", "фотофиксация инцидента (SL_EMG)"),
]

# QUAL dangling inputs whose provider is a typed op in another domain (or the
# STRAT forward seam — STRAT is converted after QUAL, so the token is a
# forward reference on the legacy op, following the MFG/PLAN precedent).
CROSS_IN_SRC = {
    "Документ@ПереченьОборудования": "MFG-02-04-01",
    "Бюджет@БТЗ": "MNT-02-01-02",
    "Документ@ПоложениеОбОплатеТруда": "HRP-01-04-04",
    "Норматив@МетодикОтбораПроб": "SL_QUAL-01-01-04",
    "ТехнологическаяКарта": "ENG-01-01-02",
    "СменносуточноеЗадание": "PLAN-01-03-04",
    "ДоговорЗаявка": "SL_PLAN-02-01-03",
    "Норматив@УсловийХранения": "SL_LOG-01-02-09",
    "ЗоныХранения": "SL_PLAN-01-02-02",
    "ГотоваяПродукция": "MFG-01-02-04",
    "АктСдачиПриёмки": "MFG-01-03-02",
    "Уведомление@Претензия": "SL_ANL-01-01-04",
    "РеестрРисков": "SL_ANL-04-02-01",
    "Документ@Рацпредложение": "IMPR-01-01-01",
    "Протокол@НСП": "SL_QUAL-04-01-01",
    "ПотребностьВРесурсах": "PLAN-01-02-03",
    "Отчёт@Инцидент": "EMG-01-04-03",
    "ПланПроизводства": "STRAT-01-01-01",
}

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
    lines.append(f"- **Входы:** {io_cell(op.get('inputs'))}")
    lines.append(f"- **Выходы:** {io_cell(op.get('outputs'))}")
    lines.append(f"- **КПЭ:** {op['kpi']}")
    lines.append(f"- **decomposition:** {op.get('decomposition', 'ATOMIC')}")
    return lines


def insert_boundaries(lines):
    for host, op in BOUNDARIES:
        present = {OPNODE_RE.match(x).group(1) for x in lines
                   if OPNODE_RE.match(x)}
        if op["code"] in present:
            continue
        start = next((i for i, x in enumerate(lines)
                      if SUB_RE.match(x) and SUB_RE.match(x).group(1) == host),
                     None)
        if start is None:
            raise SystemExit(f"host subprocess {host} not found")
        j = start + 1
        while j < len(lines) and not HEAD_RE.match(lines[j]):
            j += 1
        lines[j:j] = [""] + block(op)
    return lines


def build_edges():
    """Derive the edge list from declared I/O + explicit cross/boundary lists.

    QUAL tokens already consumed/provided by another domain's flow table are
    seeded from the on-disk links (excluding `QUAL.md` itself, so the pass stays
    idempotent)."""
    libdir = os.path.join(VAULT, "library")
    lib = engine.parse_paths(libdir)
    qual = {n.code: n for n in engine._iter_nodes(lib)
            if n.level == "OPERATION" and n.code.startswith("QUAL-")}
    boundary_codes = {op["code"] for _, op in BOUNDARIES}
    core = {c: n for c, n in qual.items() if c not in boundary_codes}

    # Seed with cross-file (external) links only.
    ext_out, ext_in = set(), set()
    for path in engine.collect_files(libdir):
        if os.path.basename(path) == "QUAL.md":
            continue
        for lk in engine.parse_paths(path).links:
            ext_out.add((lk["src"], engine.norm(lk["src_type"])))
            ext_in.add((lk["dst"], engine.norm(lk["dst_type"])))

    producers, consumers = {}, {}
    for code, op in core.items():
        for it in op.io_out:
            producers.setdefault(engine.norm(it["raw"]), []).append(code)
        for it in op.io_in:
            consumers.setdefault(engine.norm(it["raw"]), []).append(code)

    actor_in, sensor_out = {}, {}
    for _, op in BOUNDARIES:
        for tok in op.get("inputs", []):
            actor_in.setdefault(engine.norm(tok), op["code"])
        for tok in op.get("outputs", []):
            sensor_out.setdefault(engine.norm(tok), op["code"])
    cross_out = {(s, engine.norm(t)): (d, t) for s, d, t, _ in CROSS_OUT}
    cross_out_cond = {(s, engine.norm(t)): c for s, d, t, c in CROSS_OUT}
    cross_in = {engine.norm(t): s for t, s in CROSS_IN_SRC.items()}

    edges = {}
    unresolved = []

    def add(src, dst, tok, cond):
        if src and dst and src != dst:
            edges[(src, dst, tok)] = cond

    # 1. every QUAL output -> a consumer (qual -> cross -> boundary actor).
    for code in sorted(core):
        op = core[code]
        for it in op.io_out:
            tok = it["raw"]
            ntok = engine.norm(tok)
            if (code, ntok) in ext_out:
                continue
            if (code, ntok) in cross_out:
                dst, ctok = cross_out[(code, ntok)]
                add(code, dst, ctok, cross_out_cond[(code, ntok)])
            elif ntok in actor_in:
                add(code, actor_in[ntok], tok, "внешний контур (актор)")
            else:
                cands = [c for c in consumers.get(ntok, []) if c != code]
                if cands:
                    add(code, cands[0], tok, "внутренний поток")
                else:
                    unresolved.append(("OUT", code, tok))

    # 2. every QUAL input <- a producer (boundary sensor -> cross -> qual).
    covered_in = {(d, engine.norm(t)) for (s, d, t) in edges} | ext_in
    for code in sorted(core):
        op = core[code]
        for it in op.io_in:
            tok = it["raw"]
            ntok = engine.norm(tok)
            if (code, ntok) in covered_in:
                continue
            if ntok in sensor_out:
                add(sensor_out[ntok], code, tok, "внешний контур (сенсор)")
            elif ntok in cross_in:
                add(cross_in[ntok], code, tok, "кросс-доменный шов")
            else:
                cands = [p for p in producers.get(ntok, []) if p != code]
                if cands:
                    add(cands[0], code, tok, "внутренний поток")
                else:
                    unresolved.append(("IN", code, tok))

    return edges, unresolved


def build_section(edges):
    out = [HEADER, "", TABLE_HEAD, TABLE_SEP]
    for (src, dst, tok), cond in sorted(edges.items()):
        out.append(f"| {src}.{tok} | → | {dst}.{tok} | {cond} |")
    return "\r\n".join(out) + "\r\n"


def main():
    edges, unresolved = build_edges()
    if unresolved:
        for side, code, tok in unresolved:
            print(f"UNRESOLVED {side} {code}.{tok}")
        raise SystemExit(f"{len(unresolved)} unresolved QUAL I/O")
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
    text += build_section(edges).replace("\r\n", eol)
    with io.open(FILE, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"boundaries={len(BOUNDARIES)} edges={len(edges)} eol={repr(eol)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
