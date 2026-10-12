# Process-library engine (T0.9)

Parser + validator + CLI for the Spiral A process-library template
(`docs/mes-apc/ontology-processes.md` v3.0). Standalone; no dependency on the
`Proc_library` backend.

## Run

```powershell
# validate a library folder (scoped to <folder>/library) :
python engine.py "C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов"

# validate a single file (e.g. the template stub) :
python engine.py "...\Библиотека процессов\specs\_template-stub.md"

# dump graph + report :
python engine.py <path> --json report.json
python engine.py <path> --vocab <path-to-vocabulary-spec.md>
python engine.py <path> --all      # include specs/ and _-prefixed files
```

Exit code: `0` = VALID, `1` = INVALID, `2` = usage/IO error.

## What it checks

- Structure: `#`..`#####` → LIBRARY/GROUP/PROCESS/SUBPROCESS/OPERATION (T0.7).
- Attribute blocks may be separated from their heading by a blank line (T1.2):
  leading blank lines are skipped, so the regulated `Цель`/`КПЭ`/`APQC` block is
  collected even though the split files put a blank line after every heading.
- Typing: every backticked I/O ref resolves to an `Entity-State` type (T0.3, §7.1).
- Free-text I/O is a **warning** (unconverted, T0.8), an unknown backticked type
  is an **error**.
- Flow conservation §4.1; no dangling I/O §4.2; cycles with exit §4.5;
  hierarchy §4.7/§4.9/§4.10; duplicates §7.9 (warning).
- Goals: non-empty on every node + LIBRARY root (T0.4); means–end implicit via
  the tree.
- APQC: every PROCESS carries `**APQC:**` (T0.2, filled in T1.3).

## Split regression (T1.1)

`graph_signature(lib)` returns sorted `(code, level, parent)` nodes +
`(src, src_type, dst, dst_type)` edges. Capture it with `--json` before and
after splitting `Proc_lib.md`; the signatures must be identical.

## APQC crosswalk (T1.3)

- `apqc_catalog.py` → `apqc_catalog.json`: APQC PCF v7.4 (ru) L1/L2/L3 catalog
  (13/72/350) from the `Combined` sheet. Level = segment count; `X.0` is L1.
- `apqc_mapping.json`: `PROCESS code -> [L3 codes]` (first = primary), 40 entries.
- `apqc_crosswalk.py <library> apqc_mapping.json [--dry-run]`: writes
  `**APQC:** a.b.c, d.e.f` after `**Код:**` in every PROCESS block. Idempotent
  (replaces an existing line), preserves UTF-8/CRLF, backs up before writing.

## Legacy migration (T1.6)

`migrate_group_file.py <source.md> <out_dir> <group_goals.json> <apqc_mapping.json>`
splits a legacy library by `## Группа <CODE>:` into one `<CODE>.md` per group and
normalises it: group italic attrs → bold §9.1 (+ authored `**Цель группы:**` from
`group_goals.json`), `Код процесса` → `Код`, inserts `**APQC:**` from the mapping,
and removes `\<` Obsidian escapes. Non-group `##` sections (Содержание,
Приложения) are skipped. Used for `INF` and the `SL_*` logistics groups (T1.6).

## Client-token scan (T1.5)

`token_scan.py <library_dir> [--json out.json]` enforces the *token-free*
criterion of `specs/T0.6` (Decision 1). It **fails** (exit 1) on client-identity
tokens — legal-entity names, monetary figures/targets, plant codes, person
names — and prints two INFO classes that do **not** fail: `SOURCE-REF`
cross-references to the client regulation layer (`REG-<n>`, `../reglaments/*`,
`И <name>`, `ПС ПП`; Phase 4) and `TOOL` generic tool references (`1С`, `АРМ`)
plus possible brand/equipment-model Latin tokens.

## Freeze "subprocess-level v1" (T1.5)

`freeze_v1_subprocess.json` records the frozen baseline (2026-10-11):
**20 groups / 79 processes / 238 subprocesses / 995 operations** ·
graph-signature `sha256 a506b2f5…`. Gate: the validator has **0 errors at
LIBRARY/GROUP/PROCESS/SUBPROCESS** (goals present, APQC 79/79, §4.7/§4.9/§4.10
green, 0 duplicate codes); **all 4823 remaining errors are OPERATION-level**
(3844 dangling I/O §4.2 + 979 missing goals) and every free-text warning is
OPERATION-level — both are Phase-2 (T2.2). Identity-token scan: **0**.

Two falsifiable tests lock the gate: `test_vault_subprocess_freeze_errors_are_operation_only`
and `test_vault_has_no_client_identity_tokens`. `SLA` and `ENG-04` are kept
**out** of the SME template (user decision).

## Operation economics (T2.4)

`author_economics.py <file.md> <mapping.json> [--rate N]` inserts the T0.5
economics bullets after `- **КПЭ:**` for every mapped operation:
`Критичность` (authored), `Периодичность` = `<Горизонт> ×1`, `Трудоёмкость`
(authored), `Стоимость` = `Трудоёмкость × rate` (default `REF_RATE` 1000 руб/ч).
It preserves CRLF and is idempotent (skips an operation that already carries
`Критичность`). Pilot data: `planning_economics.json` (49 `PLAN` ops),
`sl_planning_economics.json` (17 `SL_PLAN` ops).

The mapping keys are **operation codes only** — unlike the operations data file,
do not add a `_note` key: every top-level key is required to match a node, so a
comment key aborts the run with `mapped but not found`.

The validator checks the economics/decomposition **domains** when the attribute
is present (errors, rule tags `BAD …`): `Критичность ∈ {high, medium, low}`;
`Периодичность` = `<year|quarter|month|week|day|shift|event> ×<n>`;
`Трудоёмкость` = `<n> ч`; `Стоимость` = `<n> руб`;
`decomposition ∈ {ATOMIC, DECOMPOSABLE, PARTIALLY_DECOMPOSABLE}`. The
reference-rate convention and roll-up example: `specs/T2.4-operation-characteristics.md`.

## Economic roll-up (T2.5)

`rollup.py <library> [--scope PREFIX …] [--json out.json]` implements T0.5
Decision 2: one row per node at **SUBPROCESS → PROCESS → GROUP (domain)** level
that carries economics. Columns: `code, level, name, ops (econ/total)`,
`Hours ч/год` (`Σ Трудоёмкость × F`), `FTE` (`Hours / AnnualFund`),
`Cost руб/год` (`Σ Стоимость × F`), `criticality`, `periodicity`; constants
`AnnualFund = 1700 ч`, `REF_RATE = 1000 руб/ч`. The matrix is **additive**
(parent = Σ children) and `Cost = Hours × REF_RATE =
FTE × AnnualFund × REF_RATE`. Reference convention + worked Planning matrix:
`specs/T2.5-economic-rollup.md`; generated artifact `rollup_planning.json`
(pilot 66 ops → 11,008 FTE, 18 713 750 руб/год).

## Domain replication (T2.6)

`author_operations.py <file.md> <ops.json>` rewrites a subprocess's operations
into typed `##### Операция CODE: name` nodes with the regulated block
(`Тип/Цель/Горизонт/Исполнитель/Входы/Выходы/КПЭ/decomposition`), from a
data file (`{ "<subprocess-code>": [ {code,name,type,goal,horizon,executor,
inputs,outputs,kpi,decomposition}, … ] }`). Two source forms are handled: the
legacy container (`##### Операции подпроцесса CODE:` + numbered list) and an
existing `##### Операция CODE` node (**retype**: the node is rewritten). The
run is **re-runnable** — a group already converted to nodes is skipped. I/O
entries are Entity-State refs (backticks added); an empty list renders `—`.
CRLF-preserving; economics are added afterwards by `author_economics.py`. Type
is chosen from the cardinality matrix (Simple 1/1, Splitter 1/>1, Joiner >1/1,
Multiplicator ≥1/≥1). Method + production-core decisions:
`specs/T2.6-domain-replication.md`; tranche data `mfg_operations.json`
(MFG-01, 17 ops) and `mfg_operations_2.json` (MFG-02..05, 46 ops).

### MFG flow graph (sub-step 3, done 2026-10-11)

`MFG.md` now ends with a per-file «Потоки (Flow Links)» table (159 edges) that
closes all **199 dangling I/O** of the production core: internal MFG→MFG flow
plus cross-domain seams to PLAN (`СменносуточноеЗадание`), STRAT
(`ПланПроизводства`), ENG (`ТехнологическаяКарта`/`Чертёж`/`СОП`), QUAL
(`Разрешение@НаИспользованиеСырья`, `Паспорт`), SL_LOG (`Сырьё`/`Тара`/
`Этикетка`/`Комплектующие`, приём брака), INF (`Энергоресурс`, отчёт ВКХ),
MNT (`Оснастка`/`Инструмент`/`КИП`, загрузка оборудования), HRP
(`Сотрудник@Квалификация`), ORG (`Норматив@ВремяПереналадки`) and ANLZ
(`Показатель@OEE`/`@Простой`/`@Отклонение`/`@ВремяПереналадки`). No new
boundary operation was needed — the MFG perimeter is entirely covered by
in-library domains. Result: MFG scope **0 errors / 0 warnings**; library errors
4457 → **4257**; links 141 → **300**; structure 20/79/238/999 unchanged.

### MFG economics and roll-up (sub-steps 4-5, done 2026-10-11)

`author_economics.py` with data `mfg_economics.json` populates the T0.5 economics
block on all **63** production-core operations (hours authored from each step's
nature, rounded to 0,25 ч; `Критичность` per control/bottleneck/entry role). No
library edit beyond the attributes: structure stays 20/79/238/999/300, errors
**4257**, warnings **3391**; MFG scope stays **0 errors / 0 warnings**. The
domain roll-up (`rollup.py --scope MFG --json rollup_mfg.json`) yields
**63 ops → 22,749 FTE · 38 672,8 ч/год · 38 672 750 руб/год** (additive across
subprocess → process → group; identity `Cost = Hours × REF_RATE`).

### Logistics — SL_LOG tranche 1 (sub-step 2, done 2026-10-11)

Process `SL_LOG-01` (5 subprocesses, 33 ops) converted to typed `##### Операция`
nodes in `SL_LOG.md`; new data `sl_log_operations.json`. Codes unchanged;
legacy `SLA-*`/client-regulation annotations dropped (Phase 4). SL_LOG-01 scope
gate: **0 MISSING GOAL / 0 FREE-TEXT / 0 UNKNOWN TYPE / 0 TYPE-CARDINALITY**
(dangling §4.2 is the flow-graph step). Cross-domain reconciliation: PLAN/SL_PLAN
flow tables moved `Отчёт@ДвижениеЗапасов`/`Отчёт@Остатки` from
`SL_LOG-01-02-01` to `SL_LOG-01-02-03` (движение запасов) so the stock reports
sit on the producing operation. Library errors 4257 → **4162**, warnings
3391 → **3223**; structure 20/79/238/999/300 unchanged.

### Logistics — SL_LOG tranche 2 (sub-step 2, done 2026-10-11)

The remaining processes `SL_LOG-02` (ГП и отгрузка), `SL_LOG-03` (транспортная
логистика) and `SL_LOG-04` (возвратная логистика) — **35 ops** across 7
subprocesses — converted from the legacy container form to typed `##### Операция`
nodes with data `sl_log_operations_2.json`. Codes unchanged; the last legacy
`SLA-*`/client-regulation annotations dropped (Phase 4). SL_LOG-02..04 scope gate:
**0 MISSING GOAL / 0 FREE-TEXT / 0 UNKNOWN TYPE / 0 TYPE-CARDINALITY**. The whole
`SL_LOG` group now has **0 warnings**, errors reduced to dangling §4.2 only
(SL_LOG scope 295/154 → **235/0**); library errors 4162 → **4102**, warnings
3223 → **3069**; structure 20/79/238/999/300 unchanged.

### Logistics — SL_LOG flow graph (sub-step 3, done 2026-10-11)

`SL_LOG.md` ends with a per-file «Потоки (Flow Links)» table (**209 edges**) plus
**10 boundary operations** (8 sensors + 2 actors) that close all **235 dangling
I/O** (134 in + 101 out) of the logistics group. Edges are internal SL_LOG→SL_LOG
flow and cross-domain seams to MFG/PLAN/SL_PLAN/QUAL/SL_QUAL/ENV/SL_MNT/SL_ANL/ORG/
SL_EMG. Unlike MFG, the logistics group sits at the enterprise perimeter, so
supplier/customer/recycler/telematics endpoints are explicit boundary operations
(the sensors carry several entities — a recorded deviation from the `|Выходы|=1`
guideline). Result: SL_LOG scope **0 errors / 0 warnings**; library errors
4102 → **3866** (−236: 235 SL_LOG + 1 ENV `Отходы` output); links 300 → **509**;
structure 20/79/238/**1009**/509.

### Logistics — SL_LOG economics and roll-up (sub-steps 4-5, done 2026-10-11)

`author_economics.py` with data `sl_log_economics.json` populates the T0.5
economics block on all **78** logistics operations (the 68 converted operations
plus the 11 boundary sensors/actors; hours authored from each step's nature,
rounded to 0,25 ч; `Критичность` high for control/gates/exceptions, low for pure
entry/forwarding). No library edit beyond the attributes: structure stays
20/79/238/**1009**/**509**, errors **3866**, warnings **3069**; SL_LOG scope stays
**0 errors / 0 warnings**. The domain roll-up (`rollup.py --scope SL_LOG --json
rollup_sl_log.json`) yields **78 ops → 7,849 FTE · 13 343,0 ч/год · 13 343 000
руб/год** (additive across subprocess → process → group; identity `Cost = Hours ×
REF_RATE`).

### Logistics — SL_QUAL (sub-steps 2-5, done 2026-10-11)

The next logistics group, quality-in-storage-and-transport (`SL_QUAL`, 5 processes
/ 8 subprocesses / **21 ops**), was converted from the legacy container form to
typed `##### Операция` nodes; data `sl_qual_operations.json` via
`author_operations.py` (codes unchanged; type per cardinality matrix). The flow
graph (`author_sl_qual_flows.py`) adds a «Потоки (Flow Links)» table (**62
edges**) plus **5 boundary ops** (4 sensors + 1 actor), closing all **73 dangling
I/O** (internal + cross-domain QUAL/SL_LOG/MFG/SL_ANL/ORG/SL_MNT seams; the
standards/claims perimeter). Economics (`author_economics.py` + data
`sl_qual_economics.json`) on all **26** ops; roll-up
(`rollup.py --scope SL_QUAL --json rollup_sl_qual.json`) → **26 ops → 1,224 FTE ·
2 080,8 ч/год · 2 080 750 руб/год** (additive; `Cost = Hours × REF_RATE`). Result:
SL_QUAL scope **0 errors / 0 warnings**; library errors 3866 → **3752**,
warnings 3069 → **2976**; links 509 → **571**; structure 20/79/238/**1014**/571;
identity 0; suite **34/34** (+`test_vault_sl_qual_processes_are_typed_and_goaled`,
`test_vault_sl_qual_flow_graph_is_closed`,
`test_vault_sl_qual_economics_complete_and_rolls_up`). Cross-domain fix: the
`SL_LOG` pin `SL_LOG-01-01-06.Уведомление@Претензия` moved from
`SL_QUAL-04-01-02` to the registration op `SL_QUAL-04-01-01`.

### Logistics — SL_MNT (sub-steps 2-5, done 2026-10-11)

The maintenance-of-logistics-fleet group (`SL_MNT`, 3 processes / 5 subprocesses /
**11 ops**) was converted from the legacy container form to typed `##### Операция`
nodes; data `sl_mnt_operations.json` via `author_operations.py` (codes unchanged;
type per cardinality matrix). The flow graph (`author_sl_mnt_flows.py`) adds a
«Потоки (Flow Links)» table (**33 edges**) plus **1 boundary sensor** (regulator's
certification requirements), closing all **38 dangling I/O** (internal + cross-domain
SL_LOG/MNT/INF-04/SL_ANL seams). Economics (`author_economics.py` + data
`sl_mnt_economics.json`) on all **12** ops; roll-up
(`rollup.py --scope SL_MNT --json rollup_sl_mnt.json`) → **12 ops → 0,540 FTE ·
918,5 ч/год · 918 500 руб/год** (additive; `Cost = Hours × REF_RATE`). Result:
SL_MNT scope **0 errors / 0 warnings**; library errors 3737 → **3699**, warnings
2934 (unchanged); links 571 → **604**; structure 20/79/238/**1015**/604; identity 0;
suite **37/37** (+`test_vault_sl_mnt_processes_are_typed_and_goaled`,
`test_vault_sl_mnt_flow_graph_is_closed`,
`test_vault_sl_mnt_economics_complete_and_rolls_up`).

### Logistics — SL_HRP (sub-steps 2-5, done 2026-10-11)

The personnel-of-logistics group (`SL_HRP`, 3 processes / 5 subprocesses /
**11 ops**) was converted from the legacy container form to typed `##### Операция`
nodes; data `sl_hrp_operations.json` via `author_operations.py` (codes unchanged;
type per cardinality matrix). The flow graph (`author_sl_hrp_flows.py`) adds a
«Потоки (Flow Links)» table (**35 edges**) plus **6 boundary ops** (4 sensors + 2
actors: internal standards + budget contour, external labour market, job boards,
external training centre) closing all **40 dangling I/O** (internal +
cross-domain HRP/ORG/PLAN/SL_LOG/SL_MNT seams). Economics (`author_economics.py` +
data `sl_hrp_economics.json`) on all **17** ops; roll-up
(`rollup.py --scope SL_HRP --json rollup_sl_hrp.json`) → **17 ops → 0,043 FTE ·
72,8 ч/год · 72 750 руб/год** (additive; `Cost = Hours × REF_RATE`). Result:
SL_HRP scope **0 errors / 0 warnings**; library errors 3699 → **3640**, warnings
2934 → **2886**; links 604 → **639**; structure 20/79/238/**1021**/639; identity 0;
suite **40/40** (+`test_vault_sl_hrp_processes_are_typed_and_goaled`,
`test_vault_sl_hrp_flow_graph_is_closed`,
`test_vault_sl_hrp_economics_complete_and_rolls_up`).

### Logistics — SL_EMG (sub-steps 2-5, done 2026-10-11)

The emergency-situations group (`SL_EMG`, 3 processes / 5 subprocesses /
**11 ops**) was converted from the legacy container form to typed `##### Операция`
nodes; data `sl_emg_operations.json` via `author_operations.py` (codes unchanged;
type per cardinality matrix). The flow graph (`author_sl_emg_flows.py`) adds a
«Потоки (Flow Links)» table (**24 edges**) plus **5 boundary ops** (3 sensors + 2
actors: the ДТП event, emergency services, ГИБДД documents, the insurance
company, the client return/refusal contour) closing all **31 dangling I/O**
(17 in + 14 out); the cross-domain seams are SL_LOG (приходный ордер, телематика,
повреждённые ТМЦ в зону брака, обратная перевозка), SL_QUAL (регистрация НСП)
and SL_ANL (данные по инцидентам). The three `SL_EMG-*` cross-domain pins already
owned by SL_QUAL / SL_LOG (`Протокол@Осмотра` → `SL_EMG-01-01-01`,
`Протокол@ОсмотраОпасныхГрузов` → `SL_EMG-01-01-02`,
`SL_EMG-03-01-03.Материал@Возврат` → SL_LOG-04-01-01/-02) are kept coherent.
Economics (`author_economics.py` + data `sl_emg_economics.json`) on all **16** ops;
roll-up (`rollup.py --scope SL_EMG --json rollup_sl_emg.json`) → **16 ops ·
0,007 FTE · 12,0 ч/год · 12 000 руб/год** (additive; `Cost = Hours × REF_RATE`).
Result: SL_EMG scope **0 errors / 0 warnings**; library errors 3640 → **3589**,
warnings 2886 → **2846**; links 639 → **663**; structure 20/79/238/**1026**/663;
identity 0; suite **43/43** (+`test_vault_sl_emg_processes_are_typed_and_goaled`,
`test_vault_sl_emg_flow_graph_is_closed`,
`test_vault_sl_emg_economics_complete_and_rolls_up`).

### Logistics — SL_ANL (sub-steps 2-5, done 2026-10-11)

The analytics/KPI group (`SL_ANL`, 4 processes / 5 subprocesses / **12 ops**) was
converted from the legacy container form to typed `##### Операция` nodes; data
`sl_anl_operations.json` via `author_operations.py` (codes unchanged; type per
cardinality matrix — Joiner/Multiplicator/Splitter). The flow graph
(`author_sl_anl_flows.py`) adds a «Потоки (Flow Links)» table (**35 edges**) plus
**3 boundary ops** (2 sensors + 1 actor: the ERP/accounting data feed, the
transport portal / carrier contracts feed, and the operational-management
consumer of the summary report), closing all **43 dangling I/O** (27 in + 16 out).
Because logistics analytics sits at the enterprise perimeter, the 11 cross-domain
inputs already pinned by SL_LOG/SL_QUAL/SL_MNT/SL_EMG on their op codes
(`SL_ANL-01-01-02`, `-01-01-03`, `-02-01-01`, `-02-01-02`, `-03-01-01`) are kept
coherent; outbound seams wire to SL_PLAN (capacity/transport limits,
carrier-choice recommendations) and SL_MNT (corrected maintenance schedule).
Economics (`author_economics.py` + data `sl_anl_economics.json`) on all **15** ops;
roll-up (`rollup.py --scope SL_ANL --json rollup_sl_anl.json`) → **15 ops ·
0,317 FTE · 539,5 ч/год · 539 500 руб/год** (additive; `Cost = Hours × REF_RATE`).
Result: SL_ANL scope **0 errors / 0 warnings**; library errors 3589 → **3530**,
warnings 2846 → **2799**; links 663 → **698**; structure 20/79/238/**1029**/698;
identity 0; suite **46/46** (+`test_vault_sl_anl_processes_are_typed_and_goaled`,
`test_vault_sl_anl_flow_graph_is_closed`,
`test_vault_sl_anl_economics_complete_and_rolls_up`).
**Logistics complete (`SL_LOG`, `SL_QUAL`, `SL_MNT`, `SL_HRP`, `SL_EMG`, `SL_ANL`).
Next: infrastructure (`INF`, `MNT`, `ENG`).**

### Infrastructure — INF tranches 1–2 (sub-step 2, done 2026-10-11)

The service of the chief engineer (`INF`, 14 processes / 56 subprocesses /
**272 ops**) is the largest remaining group. Two sub-step-2 tranches are done:
`INF-01` (Управление зданиями и территорией; 5 subprocesses / **22 ops**) with
data `inf_operations.json`, and `INF-02` (Управление энергоресурсами, 27 ops) +
`INF-03` (Управление инженерными сетями, 11 ops) with data
`inf_operations_2.json` — both converted from the legacy container form via
`author_operations.py` (codes unchanged; type per cardinality matrix). Each
tranche gate is **0 MISSING GOAL / 0 FREE-TEXT / 0 UNKNOWN TYPE /
0 TYPE-CARDINALITY** (dangling §4.2 stays open until the domain flow pass).
`INF` sits partly at the enterprise perimeter (energy/water/gas suppliers,
regulators, contractors, metering/telemetry) and partly against in-library
domains (MFG/MNT/ENG/PLAN/HRP/SL_LOG/ENV/QUAL/ANLZ); the boundary operations and
cross-domain flow links are authored in the domain flow-graph pass. No
vocabulary bump: every `INF` I/O resolves on `T0.3` **v0.3**. Library errors
3530 → **3434**, warnings 2799 → **2589**; structure 20 / 79 / 238 / **1029** /
698 unchanged; suite **48/48** (+`test_vault_inf_process_01_is_typed_and_goaled`,
`test_vault_inf_processes_02_to_03_are_typed_and_goaled`).

### Infrastructure — INF tranches 3–8 (sub-step 2, done 2026-10-11)

The remaining six `INF` tranches complete sub-step 2. Tranche 3 — `INF-04`
(Управление грузоподъёмными механизмами; 5 subprocesses / 24 ops) + `INF-05`
(Управление компрессорным и холодильным оборудованием; 4 / 20) with data
`inf_operations_3.json`. Tranche 4 — `INF-06` (Управление водоснабжением и
водоотведением; 4 / 20) + `INF-07` (Управление газовым хозяйством; 4 / 20) with
data `inf_operations_4.json`. Tranche 5 — `INF-08` (Капитальное строительство,
реконструкция и модернизация; 4 / 20) + `INF-09` (Промышленная безопасность,
охрана труда и экология; 4 / 20) with data `inf_operations_5.json`. Tranche 6 —
`INF-10` (Бюджетирование и экономика ТОиР; 3 / 15) + `INF-11` (Управление
персоналом СГИ; 4 / 20) with data `inf_operations_6.json`. Tranche 7 — `INF-12`
(Непрерывное совершенствование и повышение надёжности; 4 / 21) + `INF-13`
(Стратегия развития инфраструктуры; 3 / 11) with data `inf_operations_7.json`.
Tranche 8 — `INF-14` (Эксплуатация и техническое обслуживание инженерных
систем; 4 / 21) with data `inf_operations_8.json`. All converted from the legacy
container form via `author_operations.py` (codes unchanged; type per cardinality
matrix). Each tranche gate is **0 MISSING GOAL / 0 FREE-TEXT / 0 UNKNOWN TYPE /
0 TYPE-CARDINALITY** (dangling §4.2 stays open until the domain flow pass).

With tranche 8 the whole `INF` domain — **14 processes / 56 subprocesses /
272 operations** — is typed (`INF.md` carries 0 legacy containers). Boundary
operations and cross-domain flow links are authored in the domain flow-graph
pass. Cross-domain reconciliation (per the caveat below): the stale T2.3 pin
`PLAN-03-03-04.Подрядчик → INF-08-02-01.Подрядчик` was retargeted to the
contract-conclusion op `INF-08-02-04` and `Подрядчик` added to its inputs, so the
edge is coherent again (PLAN-03-03 scope **0/0**). No vocabulary bump: every `INF`
I/O resolves on `T0.3` **v0.3**. Library errors 3434 → **3114**, warnings
2589 → **1973**; structure 20 / 79 / 238 / **1029** / 698 unchanged; identity 0;
suite **54/54**
(+`test_vault_inf_processes_04_to_05_are_typed_and_goaled`,
`test_vault_inf_processes_06_to_07_are_typed_and_goaled`,
`test_vault_inf_processes_08_to_09_are_typed_and_goaled`,
`test_vault_inf_processes_10_to_11_are_typed_and_goaled`,
`test_vault_inf_processes_12_to_13_are_typed_and_goaled`,
`test_vault_inf_process_14_is_typed_and_goaled`).

### Infrastructure — INF flow graph (sub-step 3, done 2026-10-11)

`INF.md` ends with a per-file «Потоки (Flow Links)» table (**540 edges**) plus
**11 boundary operations** (6 sensors + 5 actors) that close all **680 dangling
I/O** (390 in + 290 out) of the infrastructure service. The domain sits partly at
the enterprise perimeter and partly against in-library domains, so the perimeter
is larger than any other: the boundary operations are grouped by **external
counterparty** (АСУТП/телеметрия, учётная база ОС, НСИ, заявители, внешний
рынок, финансовый контур; руководство, ЕРП/архив, надзор, подрядчики,
исполнители) and carry multiple entities (a deliberate deviation from the
`|Выходы|=1` guideline in T2.1 Decision 1, as recorded for logistics). Edges are
internal INF→INF flow plus cross-domain seams inbound from SL_HRP (`Бюджет@Обучение`,
`Документ@ШтатноеРасписание`), SL_LOG (`Документ@Договор`, `Запас@Склад`,
`Накладная@Приход`), SL_QUAL (`Документ@Договор`), PLAN (`Подрядчик`), MFG
(`РапортПроизводства`) and outbound to MFG/SL_ANL (`План@Мероприятий`) and
SL_QUAL (`Протокол@Расследования`). Result: INF scope **0 errors / 0 warnings**;
library errors 3114 → **2434** (−680); links 698 → **1238**; structure
20/79/238/**1040**/1238; identity 0; suite **55/55**. New tool
`author_inf_flows.py` (data-driven, CRLF, idempotent).

### Equipment maintenance — MNT tranche 1 (sub-step 2, done 2026-10-11)

The technical service for process equipment (`MNT`, 7 processes / 23 subprocesses
/ **73 operations**) is the next domain. Tranche 1 converts `MNT-01` (Мониторинг
технического состояния оборудования; 5 subprocesses, 21 ops) and `MNT-02`
(Планирование ресурсов; 3 subprocesses, 9 ops) — **30 ops** — from the legacy
container form to typed `##### Операция` nodes; data `mnt_operations.json` via
`author_operations.py` (codes unchanged; type per cardinality matrix). Tranche
gate: **0 MISSING GOAL / 0 FREE-TEXT / 0 UNKNOWN TYPE / 0 TYPE-CARDINALITY**
(errors = dangling only: 97 = 51 in + 46 out). Library errors 2434 → **2394**,
warnings 1973 → **1866**; structure 20/79/238/1040/1238 unchanged; suite
**57/57** (+`test_vault_mnt_processes_01_to_02_are_typed_and_goaled`). Next:
tranches `MNT-03..07` (sub-step 2) → MNT flow graph (3) → economics (4) →
roll-up (5).

### Equipment maintenance — MNT tranche 2 (sub-step 2, done 2026-10-11)

Tranche 2 converts the remaining processes — `MNT-03` (Планирование и подготовка
ТОиР; 5 subprocesses), `MNT-04` (Выполнение ТОиР; 3), `MNT-05`
(Контроль/анализ и нормирование; 3), `MNT-06` (Участие в переналадках; 2) and
`MNT-07` (Модернизация оборудования; 2) — **43 ops** — from the legacy container
form to typed `##### Операция` nodes; data `mnt_operations_2.json` via
`author_operations.py` (codes unchanged; type per cardinality matrix). With tranche
2 the whole `MNT` domain (**7 processes / 23 subprocesses / 73 operations**) is
typed (`MNT.md` carries 0 legacy containers). Gate: **0 MISSING GOAL /
0 FREE-TEXT / 0 UNKNOWN TYPE / 0 TYPE-CARDINALITY** (findings = dangling §4.2
only: 113 in the MNT-03..07 scope, closed by the domain flow pass).

Token names were chosen to honour the cross-domain seams already pinned by
PLAN/SL_MNT/MFG/SL_PLAN: `MNT-03-01-03` outputs `Заказ@Ремонт`,
`Заявка@СпецРаботы` and `ЗИП`; `MNT-03-01-02` outputs
`Протокол@Диагностики`/`Протокол@ДефектнойВедомости`; `MNT-03-02-01` outputs
`График@ППР` + `График@ППР@Годовой`; `MNT-03-04-04` outputs
`Норматив@РасходаЗИП` (plus the internal `ПараметрыЗапасов@НормыРасходаЗИП`
consumed by MNT-02-01-01); `MNT-06-02-01` outputs `Оснастка@Наличие`;
`MNT-06-02-02` inputs `Оснастка@Демонтирована`; `MNT-06-02-03` outputs
`Оснастка@Подготовлена`/`Оснастка`/`Инструмент`. Three stale PLAN pins still
need retargeting in the MNT flow pass (the T2.3 pinning put `Заказ@Ремонт` /
`Заявка@СпецРаботы` on `MNT-03-01-01`, and `Норматив@РасходаЗИП` on
`MNT-05-02-01`); two pre-existing PLAN pins against `MNT-01-*`
(`График@РаботыОборудования`, `Оборудование@Загрузка`) are equally stale. No
vocabulary bump: every `MNT` I/O resolves on `T0.3` **v0.3**. Library errors
2394 → **2295**, warnings 1866 → **1701**; structure 20/79/238/1040/1238
unchanged; identity 0; suite **58/58**
(+`test_vault_mnt_processes_03_to_07_are_typed_and_goaled`). Next: MNT flow
graph (sub-step 3) → economics (4) → roll-up (5); then `ENG`.

### Equipment maintenance — MNT flow graph (sub-step 3, done 2026-10-11)

`MNT.md` ends with a per-file «Потоки (Flow Links)» table (**177 edges**) plus
**7 boundary operations** (2 sensors + 5 actors) that close all **206 dangling
I/O** (109 in + 97 out) of the technical service. Edges are internal MNT→MNT flow
plus cross-domain seams to PLAN (`Оборудование@Доступно`, `График@ППР`,
`Заказ@Ремонт`, `Заявка@СпецРаботы`, `Норматив@РасходаЗИП`, `СтраховойЗапас`,
`Оснастка@Наличие`), MFG (`Оснастка`/`Инструмент`/`Оснастка@Подготовлена`,
`График@Переналадки`, `Отчёт@ПотериПереналадки`), SL_MNT (`СОП`/`ЗИП`/
`диагностика`/`заявка на ремонт`), SL_PLAN (`График@ППР`), SL_ANL
(`План@Мероприятий`) and INF (`АктСдачиПриёмки@ВводВЭксплуатацию`). The boundary
ops are grouped by counterparty: sensors **manufacturer/external standards (TPM,
operating manual)** and **HR (отпуска)**; actors **ERP/archive**, **HRP
(подбор)**, **IMPR (идеи улучшения)**, **management/finance (budget deviation,
project status)** and **production (completion notice, restored visualisation)**.

Cross-domain token reconciliation in the same pass: `MNT-02-03-01` input
`Заказ@НаРемонт` → `Заказ@Ремонт`; `MNT-06-01-01`/`MNT-06-02-01` input
`График@Переналадок` → `График@Переналадки` (MFG-02-01-01); `MNT-06-01-03`
input `Отчёт@Переналадки` → `Отчёт@ПотериПереналадки` (MFG-02-04-03);
`MNT-02-01-01`/`MNT-07-01-01` input `НормативЗапаса@НеснижаемыйОстатокТМЦ` →
`СтраховойЗапас` (PLAN-03-03-02); `MNT-01-05-02` input
`Заявка@НаПриобретениеПриборов` → `Заявка@НаЗакуп` (MNT-03-04-02). Two monitoring
outputs consumed by existing pins were added: `График@РаботыОборудования` on
`MNT-01-01-01` and `Оборудование@Загрузка` on `MNT-01-02-03`. Stale T2.3 pins
were retargeted in the owning files: PLAN `MNT-03-01-01`→`MNT-03-01-03`
(`Заказ@Ремонт`, `Заявка@СпецРаботы`), `MNT-05-02-01`→`MNT-03-04-04`
(`Норматив@РасходаЗИП`), `MNT-01-02-01`→`MNT-01-02-03` (`Оборудование@Загрузка`,
also in MFG). Result: MNT scope **0 errors / 0 warnings**; library errors
2295 → **2089** (−206); links 1238 → **1415**; structure 20/79/238/**1047**/1415;
identity 0; suite **59/59** (+`test_vault_mnt_flow_graph_is_closed`; the two MNT
tranche tests' op counts bumped for hosted boundary ops). New tool
`author_mnt_flows.py` (data-driven, CRLF, idempotent).

### Flow-link validation caveat (lesson, 2026-10-11)

The validator checks a link only by its **operation codes**: `src`/`dst` must be
existing OPERATION nodes, and every operation I/O token must appear in ≥1 link
(§4.2 dangling). It does **not** verify that a link's declared `Type@State` is
actually among the source operation's outputs or the target's inputs. Two
consequences when replicating a domain:

- A cross-domain link pinned by an earlier domain (`A.op.Тип → B.op.Тип`) keeps
  the token non-dangling only if `A.op` really outputs that token; a stale pin
  passes silently as a bogus edge.
- Therefore, when a later domain finds a pinned op semantically wrong (e.g. the
  stock-report token pinned on the *placement* op instead of the *journal* op),
  fix the pinning table in the owning file — a low-risk edit, since only codes
  are validated — rather than forcing incoherent I/O onto the pinned operation.
- A **mutual boundary exchange** (`A.op.tok → B.op.tok` and `B.op.tok → A.op.tok`)
  forms a 2-node §4.5 CYCLE WITHOUT EXIT. Route the reverse edge from a *different*
  op in the same subprocess (e.g. the ADR-document handover from `SL_MNT-03-01-02`
  but the `ДопускТС` permit from `SL_MNT-03-01-01`) to keep both tokens non-dangling.
- **Cadence must match the trigger, not the responding shift** (lesson SL_EMG,
  2026-10-11). An incident/exception-driven operation (`Горизонт: event`) runs on
  demand; authoring it as `shift` multiplies its reference hours by ~1095/year and
  silently inflates the domain roll-up (SL_EMG-01-02 read 1 642 ч/год instead of
  1,5 ч before the fix). Author `event` for reactive steps and sanity-check the
  roll-up magnitude against the domain's nature before finalizing.

### Technology preparation — ENG (sub-steps 1-5, done 2026-10-11)

The technology-preparation group (`ENG`, 1 process `ENG-01` / 4 subprocesses /
**15 operations** — design and approval of technological processes, change
management of the technology documentation, actualisation of the normative
reference information, and norms for incoming control) was the next domain.
Sub-step 2 converted all 15 ops from the legacy container form to typed
`##### Операция` nodes; data `eng_operations.json` via `author_operations.py`
(codes unchanged; type per cardinality matrix). Sub-step 3 added
`author_eng_flows.py` (data-driven, CRLF, idempotent): a «Потоки (Flow Links)»
table (**41 edges**) plus **4 boundary sensors** (design documentation from the
constructor/customer; the technology reference base — NSI, equipment passports,
competence matrices, regime handbooks; the measurement contour — time studies,
actual productivity, over-consumption claims; the external GOST/TU standards),
closing all **54 dangling I/O**. Cross-domain seams wire to PLAN
(`ДанныеОперативногоУчёта@Валидированы`), MNT (`Документ@КарточкаОбъектаТОиР`,
`ТехнологическаяКарта@ОбъектаТОиР`, `Документ@КорректирующиеМероприятия`), IMPR
(`Документ@Рацпредложение`), QUAL (`Протокол@Брак`) and ANLZ
(`Отчёт@АнализОтклонений`) inbound, and to ORG (`Норматив@НормыВремени`), MFG
(`ТехнологическаяКарта@Визуализация`, `ТехнологическаяКарта@Действующая`), INF
(`Документ@Аннулировано`), STRAT/ANLZ/PLAN (`Норматив@Расхода`) and QUAL
(`Норматив@ВходногоКонтроля`) outbound. The pre-existing MFG/PLAN pins on the
design outputs (`ENG-01-01-01.Чертёж`, `ENG-01-01-02.ТехнологическаяКарта` +
`@Требования`/`@Регламент`/`@КартаКонтроля`/`@Допуски`/`@Наладки`/`@Режим`/
`@Рецептура`/`@Спецификация`, `СОП`/`СОП@Сборки`) and the MFG-03-03-04 →
`ENG-01-02-02` change feed stay coherent (the design op really emits those
tokens). Sub-steps 4-5 (`eng_economics.json` + `rollup.py --scope ENG`) populate
the T0.5 economics on all **19** ops (15 typed + 4 boundary sensors;
`Стоимость = Трудоёмкость × REF_RATE 1000`; `high` for analysis/design/approval
gates, `low` for pure forwarding/boundary feeds); roll-up → **19 ops · 0,125 FTE ·
212,8 ч/год · 212 750 руб/год** (additive; `Cost = FTE × 1700 × 1000`). Result:
ENG scope **0 errors / 0 warnings**; library errors 2089 → **2006**, warnings 1701
→ **1633**; links 1415 → **1456**; structure 20 / 79 / 238 / **1051** / 1456;
identity 0; suite **63/63** (+`test_vault_eng_process_is_typed_and_goaled`,
`test_vault_eng_flow_graph_is_closed`,
`test_vault_eng_economics_complete_and_rolls_up`).

### Production efficiency analysis — ANLZ (sub-steps 1-5, done 2026-10-11)

The production-efficiency-analysis group (`ANLZ`, 1 process `ANLZ-01` / 7
subprocesses / **32 operations** — KPI calculation, efficiency meetings, budget
variance, cross-functional audit, bottleneck management, value-stream mapping and
gemba walks) was the next domain. Sub-step 2 converted all 32 ops from the legacy
container form to typed `##### Операция` nodes; data `anlz_operations.json` via
`author_operations.py` (codes unchanged; type per cardinality matrix —
Joiner/Multiplicator/Splitter/Simple). Sub-step 3 added `author_anlz_flows.py`
(data-driven, CRLF, idempotent): a «Потоки (Flow Links)» table (**80 edges**)
plus **5 boundary ops** (4 sensors + 1 actor: the ERP/BI + NSI reference contour,
the accounting actual-cost contour, the commercial/strategy contour, the ОТ/5S
standards contour; and management as consumer of the consolidated efficiency
report), closing all **105 dangling I/O** (69 in + 36 out). Cross-domain seams
wire inbound from PLAN (`ДанныеОперативногоУчёта@Валидированы`), QUAL
(`Протокол@Брак`), MFG (`РапортПроизводства`), STRAT (`Бюджет@Утверждён`,
`ПланПроизводства`), MNT (`Оборудование@Загрузка`) and IMPR
(`Отчёт@СтатусПроектов`), and outbound to ENG/MFG (pinned indicator tokens),
PLAN (`СменносуточноеЗадание@Откорректировано`), STRAT
(`Бюджет@Откорректирован`), MNT (`Документ@ПереченьУзкихМест`,
`План@РасшивкаУзкихМест`), IMPR (`Документ@ПредложениеПоУлучшению`,
`План@КорректирующихМероприятий`, VSM portfolio) and HRP
(`Отчёт@УстранениеЗамечаний`). The cross-domain pins already owned by
PLAN / ENG / MFG on `ANLZ-01-01-01` (`Отчёт@Аналитика` and `Норматив@Расхода`
inbound; `Показатель@OEE`/`@Простой`/`@Отклонение`/`@ВремяПереналадки` and
`Отчёт@АнализОтклонений` outbound) stay coherent — the reporting operation
really carries those tokens. Sub-steps 4-5 (`anlz_economics.json` +
`rollup.py --scope ANLZ`) populate the T0.5 economics on all **37** ops (32 typed
+ 5 boundary; `Стоимость = Трудоёмкость × REF_RATE 1000`; `high` for the
analysis/reporting gates — BI calculation, consolidation, audit, bottleneck
root-cause, VSM maps; `low` for pure data feeds/boundary); roll-up → **37 ops ·
1,309 FTE · 2 225,8 ч/год · 2 225 750 руб/год** (additive; `Cost = FTE × 1700 ×
1000`). Result: ANLZ scope **0 errors / 0 warnings**; library errors 2006 →
**1810**, warnings 1633 → **1469**; links 1456 → **1536**; structure 20 / 79 /
238 / **1056** / 1536; identity 0; suite **66/66**
(+`test_vault_anlz_processes_are_typed_and_goaled`,
`test_vault_anlz_flow_graph_is_closed`,
`test_vault_anlz_economics_complete_and_rolls_up`). **ANLZ fully DONE.**

### Unplanned situations — EMG (sub-steps 1-5, done 2026-10-11)

The unplanned-situation-management group (`EMG`, 3 processes / 9 subprocesses /
**34 operations** — detection and primary assessment, localisation and first
response, notification/escalation, hand-over back to normal mode; investigation
and trend analysis; scenarios/instructions, drills and induction) was the next
domain. Sub-step 2 converted all 34 ops from the legacy container form to typed
`##### Операция` nodes; data `emg_operations.json` via `author_operations.py`
(codes unchanged; type per cardinality matrix). Sub-step 3 added
`author_emg_flows.py` (data-driven, CRLF, idempotent): a «Потоки (Flow Links)»
table (**84 edges**) plus **5 boundary ops** (3 sensors + 2 actors) closing all
**110 dangling I/O** (68 in + 42 out). The perimeter: sensors **monitoring/signal
contour** (`EMG-01-01-04`), **emergency reserve + stop norms** (`EMG-01-02-05`),
**ОТ/промбезопасность standards and passports** (`EMG-03-01-05`); actors
**external emergency services** (`EMG-01-02-06`) and **management/supervisory
bodies** (`EMG-01-03-05`). Cross-domain seams wire inbound from ENG
(`ТехнологическаяКарта`), STRAT (`ПланПроизводства`), QUAL (`Протокол@Брак`) and
HRP (`Документ@СписокНовыхСотрудников`), and outbound to MNT
(`Заказ@Ремонт`), QUAL (`Документ@АктОБраке`), HRP
(`Заявка@НаРасследованиеТравмы`, `ЗаявкаНаОбучение`, `Протокол@РазбораТренировки`,
`Заявка@НаДообучение`, `Документ@ПриказОНаставничестве`), ENV
(`Заявка@ВнеплановыйМониторинг`) and IMPR (`План@КорректирующихМероприятий@
Утверждён`, `План@ПредупреждающихМероприятий`). One cycle-with-exit remains
(trend analysis ↔ risk-register actualisation), and the `EMG-03-03` ↔ HRP
adaptation mutual edge was routed to `HRP-01-05-02` to avoid a §4.5 dead cycle.
Sub-steps 4-5 (`emg_economics.json` + `rollup.py --scope EMG`) populate the T0.5
economics on all **39** ops (34 typed + 5 boundary; `Периодичность = <Горизонт>
×1`; `Стоимость = Трудоёмкость × REF_RATE 1000`; `high` for the response /
decision / investigation / analysis gates and the safety-critical training,
`low` for pure entry/forwarding/boundary/standards); roll-up → **39 ops ·
0,095 FTE · 162,0 ч/год · 162 000 руб/год** (additive; `Cost = FTE × 1700 ×
1000`). Result: EMG scope **0 errors / 0 warnings**; library errors 1810 →
**1575**, warnings 1469 → **1268**; links 1536 → **1620**; structure 20 / 79 /
238 / **1061** / 1620; identity 0; suite **69/69**
(+`test_vault_emg_processes_are_typed_and_goaled`,
`test_vault_emg_flow_graph_is_closed`,
`test_vault_emg_economics_complete_and_rolls_up`). **EMG fully DONE.**

### Environment — ENV (sub-steps 1-5, done 2026-10-11)

The environmental-management group (`ENV`, 3 processes / 7 subprocesses /
**27 operations** — waste identification/sorting/storage, waste accounting,
transfer to specialised organisations; monitoring of the environmental impact
(PEC planning, measurements, analysis and reporting); interaction with
supervisory bodies, instructions and remediation) was the next domain. Sub-step 2
converted all 27 ops from the legacy container form to typed `##### Операция`
nodes; data `env_operations.json` via `author_operations.py` (codes unchanged;
type per cardinality matrix). Sub-step 3 added `author_env_flows.py`
(data-driven, CRLF, idempotent): a «Потоки (Flow Links)» table (**52 edges**)
plus **7 boundary ops** (4 sensors + 3 actors) closing all **74 dangling I/O**
(45 in + 29 out). The perimeter: sensors **FKKO / environmental-standards**
(`ENV-01-01-05`), **permit/oversight contour** (`ENV-02-01-05`), **accredited
laboratory** (`ENV-02-01-06`) and **external recycler** (`ENV-01-03-05`); actors
**external reporting / statistics** (`ENV-01-02-05`), **finance / disposal
costs** (`ENV-01-03-06`) and the **supervisory body** (`ENV-03-02-05`).
Cross-domain seams wire inbound from ENG (`ТехнологическаяКарта`) and STRAT
(`ПланПроизводства`), and outbound to IMPR (`План@КорректирующихМероприятий`,
`План@МероприятийПоУстранению`); the five pre-existing pins owned by SL_LOG
(`Норматив@КлассификаторОтходов` → SL_LOG-01-04-02, `Отходы` →
SL_LOG-01-04-01/-02, SL_LOG-01-04-01 → `ENV-01-02-02.Протокол@ПриёмкиОтходов`,
SL_LOG-01-04-02 → `ENV-01-03-03.Отходы@Отсортированы`) and EMG
(`EMG-01-04-02` → `ENV-02-02-01.Заявка@ВнеплановыйМониторинг`) are kept
coherent — the ENV ops really emit / consume those tokens. Sub-steps 4-5
(`env_economics.json` + `rollup.py --scope ENV`) populate the T0.5 economics on
all **34** ops (27 typed + 7 boundary; `Периодичность = <Горизонт> ×1`;
`Стоимость = Трудоёмкость × REF_RATE 1000`; `high` for the identification,
reporting, PEC-programme, permit, remediation-plan and waste-transfer gates, `low`
for pure entry/forwarding/boundary); roll-up → **34 ops · 3,938 FTE · 6 695,2
ч/год · 6 695 250 руб/год** (additive; `Cost = FTE × 1700 × 1000`). Result: ENV
scope **0 errors / 0 warnings**; library errors 1575 → **1462**, warnings 1268 →
**1181**; links 1620 → **1672**; structure 20 / 79 / 238 / **1068** / 1672;
identity 0; suite **72/72** (+`test_vault_env_processes_are_typed_and_goaled`,
`test_vault_env_flow_graph_is_closed`,
`test_vault_env_economics_complete_and_rolls_up`). **ENV fully DONE.**

### Production personnel — HRP (sub-steps 1-5, done 2026-10-11)

The production-personnel-management group (`HRP`, 2 processes / 11 subprocesses /
**65 operations**) was the next domain. Sub-step 2 converted all 65 ops from the
legacy container form to typed `##### Операция` nodes; data `hrp_operations.json`
via `author_operations.py` (codes unchanged; type per cardinality matrix). One
cross-domain reconciliation: the stale SL_HRP pin `График@Аттестации` src moved
`HRP-01-03-02` → `HRP-01-01-05` (the annual training/attestation plan produces the
attestation schedule). Sub-step 3 added `author_hrp_flows.py` (data-driven, CRLF,
idempotent): a «Потоки (Flow Links)» table (**150 edges**) plus **6 boundary ops**
(3 sensors: external training-programmes market, involvement-survey/HR-analytics
contour, external ОТ/ПБ standards; 3 actors: finance, management, state labour
inspectorate) closing all HRP dangling I/O (internal HRP→HRP flow + cross-domain
seams to ENG/MNT/ANLZ/STRAT/PLAN/SL_HRP/EMG/ORG). The pre-existing pins owned by
other domains stay coherent (`HRP-01-05-01.Документ@СписокНовыхСотрудников` →
EMG, `HRP-01-03-07.Сотрудник@Квалификация` → MFG, `HRP-01-01-06.Документ@RACI`
and `HRP-01-04-02.Документ@ДолжностнаяИнструкция` → SL_HRP,
`HRP-01-05-01.Сотрудник@Ознакомлен` / `HRP-01-03-04.Сотрудник@Аттестован` ←
SL_HRP, `HRP-02-01-01.Отчёт@УстранениеЗамечаний` ← ANLZ,
`HRP-02-03-01.Заявка@НаРасследованиеТравмы` ← EMG, `HRP-01-01-01`/`-04`/`-07`
`ЗаявкаНаОбучение` ← PLAN/EMG). Sub-steps 4-5 (`hrp_economics.json` +
`rollup.py --scope HRP`) populate the T0.5 economics on all **71** ops (65 typed +
6 boundary; trigger-matched cadence — per-shift discipline checks `shift`,
repeated training `month`, reactive steps `event`; `Стоимость = Трудоёмкость ×
REF_RATE 1000`; `high` for assessment/approval/ОТ/investigation gates, `low` for
pure registration/boundary); roll-up → **71 ops · 1,214 FTE · 2 064,0 ч/год ·
2 064 000 руб/год** (additive; `Cost = FTE × 1700 × 1000`). Result: HRP scope
**0 errors / 0 warnings**; library errors 1462 → **1111**, warnings 1181 → **895**;
links 1672 → **1822**; structure 20 / 79 / 238 / **1074** / 1822; identity 0;
suite **75/75** (+`test_vault_hrp_processes_are_typed_and_goaled`,
`test_vault_hrp_flow_graph_is_closed`,
`test_vault_hrp_economics_complete_and_rolls_up`). **HRP fully DONE.**
### Continuous improvement — IMPR (sub-steps 1-5, done 2026-10-11)

The continuous-improvement group (`IMPR`, 3 processes / 10 subprocesses / **36
operations** — idea intake and expert review, author motivation, the kaizen
workshop, improvement-project execution, and internal/external benchmarking) was
the next domain. Sub-step 2 converted all 36 ops from the legacy container form
to typed `##### Операция` nodes; data `impr_operations.json` via
`author_operations.py` (codes unchanged; type per cardinality matrix —
Simple/Splitter/Joiner/Multiplicator). Sub-step 3 added `author_impr_flows.py`
(data-driven, CRLF, idempotent): a «Потоки (Flow Links)» table (**51 edges**)
plus **3 boundary operations** (2 sensors: the employee idea feed, the external
benchmarking sources; 1 actor: the corporate-media recognition channel), closing
all **94 dangling I/O**. Cross-domain seams wire inbound from PLAN
(`Отчёт@Утверждён`), QUAL (`Отчёт@Качество`) and — pinned by the earlier domains
— ANLZ (`Документ@ПредложениеПоУлучшению`, `Отчёт@УстранениеЗамечаний`,
`Отчёт@ЗакрытиеУзкогоМеста`, `Документ@ПланVSM`, `Документ@ОтчётАктуализацииVSM`),
EMG (`План@ПредупреждающихМероприятий`, `План@КорректирующихМероприятий@Утверждён`)
and ENV (`План@КорректирующихМероприятий`, `План@МероприятийПоУстранению`); the
outbound seams are `Документ@Рацпредложение` → ENG (from the intake op and the
replication op), `Отчёт@ФормаА3` → HRP (knowledge base) and `Отчёт@СтатусПроектов`
→ ANLZ. Sub-steps 4-5 (`impr_economics.json` + `rollup.py --scope IMPR`) populate
the T0.5 economics on all **39** ops (36 typed + 3 boundary; `Периодичность =
<Горизонт> ×1`; `Стоимость = Трудоёмкость × REF_RATE 1000`; `high` for the expert
review / risk assessment / decision / project gate / gap-analysis steps, `low` for
pure registration / payment / publication / boundary); roll-up → **39 ops ·
0,395 FTE · 671,2 ч/год · 671 250 руб/год** (additive; `Cost = FTE × 1700 ×
1000`). Result: IMPR scope **0 errors / 0 warnings**; library errors 1111 →
**962**, warnings 895 → **782**; links 1822 → **1873**; structure 20 / 79 / 238 /
**1077** / 1873; identity 0; suite **78/78**
(+`test_vault_impr_processes_are_typed_and_goaled`,
`test_vault_impr_flow_graph_is_closed`,
`test_vault_impr_economics_complete_and_rolls_up`). **IMPR fully DONE.**
Next domain: `ORG` / `QUAL` / `STRAT` — same five sub-steps.

### Quality management — QUAL (sub-step 2, done 2026-10-11)

The quality-management group (`QUAL`, 9 processes / 29 subprocesses / **147
operations**) was converted from the legacy container form to typed
`##### Операция` nodes; data `qual_operations.json` (QUAL-01..02, 21 ops),
`qual_operations_2.json` (QUAL-03, 34), `qual_operations_3.json` (QUAL-04..05,
40), `qual_operations_4.json` (QUAL-06..07, 30) and `qual_operations_5.json`
(QUAL-08..09, 22) via `author_operations.py` (codes unchanged; type per
cardinality matrix). Four §7.9 duplicates inside the НСП-management subprocesses
(QUAL-05-02-04 ~ -03-05, -02-05 ~ -03-06 ~ -04-08, -03-08 ~ -04-11) were
differentiated by a source-specific input (`РапортПроизводства` /
`АктСдачиПриёмки` / `Протокол@Испытаний`). The cross-domain pins owned by the
earlier domains on the exact op codes are kept coherent: QUAL-03-01-01
(`Норматив@ВходногоКонтроля` in, ENG), QUAL-03-01-04 (`Заявка@ВходнойКонтроль`
in / `Норматив@ВходногоКонтроля` out, SL_LOG), QUAL-03-01-05 (`Сырьё@Проба` in,
SL_LOG), QUAL-03-01-08 (`Протокол@Испытаний` out, SL_LOG), QUAL-03-05-02
(`Паспорт` out, MFG/SL_LOG), QUAL-03-03-04 (`Отчёт@Качество` out, IMPR),
QUAL-05-01-01 (`Протокол@Расхождений` in / `Уведомление@Несоответствие` out,
SL_LOG), QUAL-05-01-03 (`Разрешение@НаИспользованиеСырья` out, MFG),
QUAL-05-02-01 (`Документ@АктОБраке` in / `Протокол@Брак` out, EMG/ANLZ/ENG),
QUAL-05-02-06 (`Партия@Карантин` in, SL_LOG), QUAL-05-03-01
(`Протокол@ОсмотраГП` in, SL_LOG), QUAL-05-04-01 (`Уведомление@НСП` in,
SL_LOG). Sub-step-2 gate: **0 MISSING GOAL / 0 FREE-TEXT / 0 UNKNOWN TYPE /
0 TYPE-CARDINALITY / 0 POSSIBLE DUPLICATE** (dangling §4.2 stays open — 547 =
310 in + 237 out). Library errors 962 → **742**, warnings 782 → **160**;
structure 20/79/238/**1077**/1873 unchanged; identity 0; suite **79/79**
(+`test_vault_qual_processes_are_typed_and_goaled`). **Next: the QUAL flow graph
(sub-step 3)** → economics → roll-up.

### Quality management — QUAL flow graph (sub-step 3, done 2026-10-11)

`QUAL.md` ends with a per-file «Потоки (Flow Links)» table (**446 edges**) plus
**25 boundary operations** (10 sensors + 15 actors) that close all **547 dangling
I/O** (310 in + 237 out). Edges are internal QUAL→QUAL flow plus cross-domain
seams to ENG / MFG / SL_LOG / SL_QUAL / SL_PLAN / PLAN / MNT / HRP / IMPR / EMG /
SL_ANL and the STRAT forward seam. The perimeter: sensors **external
normative/legislation**, **customer/SMK initiators**, **asset/stock registry**,
**production programme**, **HRP personnel data**, **supplier source documents**,
**certification/labs reference**, **NSP sources**, **analysis inputs** and the
**QMS documentation base**; actors **finance/procurement**, **ЦСМ**, **HRP
training**, **quality-service operating documents**, **management reporting**,
**production contour**, **sales/warehouse**, **УСИС/АИЛ dispatch**, **SL_LOG
logistics**, **supplier claims**, **NSP actions**, **customer/recall**,
**investigation commission**, **audit group** and the **QMS archive**. Tokens
already consumed/provided by other domains' tables are seeded from the on-disk
links (no duplicate seam). Result: QUAL scope **0 errors / 0 warnings**; library
errors 742 → **195**, warnings **160**; links 1873 → **2319**; structure
20/79/238/**1102**/2319; identity 0; suite **80/80**
(+`test_vault_qual_flow_graph_is_closed`). New tool `author_qual_flows.py`
(data-driven, CRLF, idempotent).

### Quality management — QUAL economics and roll-up (sub-steps 4-5, done 2026-10-11)

`author_economics.py` with data `qual_economics.json` populates the T0.5
economics block on all **172** quality-management operations (the 147 converted
operations plus the 25 flow-pass boundary sensors/actors; hours authored from
each step's nature, rounded to 0,25 ч; `Критичность` `high` for the control /
analysis / approval / certification / audit gates, `low` for pure registration /
forwarding / boundary feeds; cadence `<Горизонт> ×1`, with reactive НСП /
претензия / аудит steps on `event`). No library edit beyond the attributes:
structure stays 20/79/238/**1102**/**2319**, errors **195**, warnings **160**;
QUAL scope stays **0 errors / 0 warnings**. The domain roll-up
(`rollup.py --scope QUAL --json rollup_qual.json`) yields **172 ops → 2,560 FTE ·
4 352,8 ч/год · 4 352 750 руб/год** (additive across subprocess → process →
group; identity `Cost = Hours × REF_RATE`). Suite **81/81**
(+`test_vault_qual_economics_complete_and_rolls_up`). **QUAL fully DONE. Next
domain: `ORG` / `STRAT`** — same five sub-steps.

## Tests

```powershell
cd C:\Users\evgeniy.bogdanov\Documents\Python\AntiManager\pipelines\proc-library
python -m pytest -q -p no:cacheprovider
```

81 tests: stub VALID, legacy container synthesis, typing/dangling/goal/APQC
errors, blank-line-separated attr block, cycle-without-exit, split-regression,
APQC crosswalk coverage, the T1.5 freeze gate (operation-only errors), the
T2.3 pilot (no dangling, sensors/actors), the T2.4 economics (bad/valid domain
units, full characteristics on all 66 pilot ops, roll-up sample), the T2.5
roll-up (frequency→executions, additive/reproducible matrix), the T2.6 MFG
replication (MFG-01 and MFG-02..05 typed + goaled, the MFG flow graph closed,
the MFG economics complete + domain roll-up), the T2.6 logistics tranches
(SL_LOG-01 and SL_LOG-02..04 typed + goaled, the SL_LOG flow graph closed, the
SL_LOG economics complete + domain roll-up), the T2.6 logistics-quality group
(SL_QUAL-01..06 typed + goaled, the SL_QUAL flow graph closed, the SL_QUAL
economics complete + domain roll-up), the T2.6 logistics-maintenance group
(SL_MNT-01..03 typed + goaled, the SL_MNT flow graph closed, the SL_MNT
economics complete + domain roll-up), the T2.6 logistics-personnel group
(SL_HRP-01..03 typed + goaled, the SL_HRP flow graph closed, the SL_HRP
economics complete + domain roll-up), the T2.6 logistics-emergency group
(SL_EMG-01..03 typed + goaled, the SL_EMG flow graph closed, the SL_EMG
economics complete + domain roll-up), the T2.6 logistics-analytics group
(SL_ANL-01..04 typed + goaled, the SL_ANL flow graph closed, the SL_ANL
economics complete + domain roll-up), the T2.6 infrastructure tranches
(INF-01 / INF-02..03 / INF-04..05 / INF-06..07 / INF-08..09 / INF-10..11 /
INF-12..13 / INF-14 typed + goaled, the INF flow graph closed), the T2.6
equipment-maintenance tranches (MNT-01..02 and MNT-03..07 typed + goaled, the
MNT flow graph closed), the T2.6 technology-preparation group
(`test_vault_eng_process_is_typed_and_goaled`,
`test_vault_eng_flow_graph_is_closed`,
`test_vault_eng_economics_complete_and_rolls_up`), the T2.6
production-efficiency-analysis group
(`test_vault_anlz_processes_are_typed_and_goaled`,
`test_vault_anlz_flow_graph_is_closed`,
`test_vault_anlz_economics_complete_and_rolls_up`), the T2.6
unplanned-situation-management group
(`test_vault_emg_processes_are_typed_and_goaled`,
`test_vault_emg_flow_graph_is_closed`,
`test_vault_emg_economics_complete_and_rolls_up`), the T2.6
environmental-management group
(`test_vault_env_processes_are_typed_and_goaled`,
`test_vault_env_flow_graph_is_closed`,
`test_vault_env_economics_complete_and_rolls_up`), the T2.6
production-personnel group
(`test_vault_hrp_processes_are_typed_and_goaled`,
`test_vault_hrp_flow_graph_is_closed`,
`test_vault_hrp_economics_complete_and_rolls_up`), the T2.6
continuous-improvement group
(`test_vault_impr_processes_are_typed_and_goaled`,
`test_vault_impr_flow_graph_is_closed`,
`test_vault_impr_economics_complete_and_rolls_up`), the T2.6 quality-management
group (QUAL-01..09 typed + goaled:
`test_vault_qual_processes_are_typed_and_goaled`, the QUAL flow graph closed:
`test_vault_qual_flow_graph_is_closed`, the QUAL economics complete + domain
roll-up: `test_vault_qual_economics_complete_and_rolls_up`), the
identity-token scan, plus the vault stub. Vault-dependent tests skip when the vault
is absent.
