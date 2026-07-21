---
description: Проверить и исправить битую кодировку в .md файлах vault
---

# ПРОТОКОЛ БЕЗОПАСНОСТИ: перед любым изменением файлов — бекап

`powershell
 = "C:\Users\EVGENI~1.BOG\AppData\Local\Temp\kilo\backups\20260721_174058"
New-Item -ItemType Directory -Path  -Force | Out-Null
Copy-Item -Path "target\*" -Destination  -Recurse -Force
Write-Host "Backup: "
`

Никогда не применять неоттестированный алгоритм к production-файлам.
Всегда: бекап → тест на копии → применение → верификация.

---

## Диагностика: как определить проблему

Использовать ТОЛЬКО Python — PowerShell криво работает с кириллицей.

**Быстрая проверка:** `python .kilo/scripts/guard_encoding.py --vault`

Три типа повреждений:
1. **UTF-8 decode error** — файл не читается как UTF-8 (редко)
2. **U+FFFD replacement chars** — частичная потеря данных при decode c `errors='replace'`
3. **Double-encoding** — самый частый: валидный UTF-8, но русский текст стал кракозяброй.

Признак double-encoding: доля заглавных кириллических символов (А-Я).
- Нормальный текст: 2-5% заглавной кириллицы
- Заголовки/диаграммы: 5-15%
- **Double-encoding: 50-99% заглавной кириллицы** (надёжный детект)
- 15-50% при >1000 Cyrillic chars: WARNING (возможна порча)

Гард проверяет все три типа автоматически.

---

## Единственный рабочий алгоритм: ftfy

Библиотека ftfy (fix text for you) — Mozilla-алгоритм, единственный надёжный.

`python
from ftfy import fix_text

# Бекап
import shutil, os
backup = os.path.join(os.environ['TEMP'], 'kilo', 'backups',
                      __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(backup, exist_ok=True)
shutil.copy2(path, os.path.join(backup, os.path.basename(path)))

# Чтение
with open(path, 'rb') as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    data = data[3:]

# Фикс
text = data.decode('utf-8', errors='replace')
fixed = fix_text(text)

# Верификация
cyr_new = sum(1 for c in fixed if '\u0410' <= c <= '\u042F')
ratio_new = cyr_new / len(fixed) * 100 if len(fixed) > 0 else 0
if ratio_new < 8:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print(f'OK: {ratio_new:.0f}% — clean')
else:
    print(f'FAIL: {ratio_new:.0f}% — still mojibake, revert from backup')
`

---

## Правила безопасности (learned the hard way)

1. Бекап всегда. Перед ЛЮБЫМ изменением файлов.
2. Не использовать PowerShell для кириллицы. Только Python 3.14+.
3. Тест на копии. Если файл уникальный — скопировать, потестить.
4. Два прохода ftfy. Если не помогло — не изобретать, передать пользователю.
5. Верификация после фикса. Проверить долю заглавной кириллицы.
6. По одному файлу. Не трогать пачкой — проверить — закоммитить.
7. Файлы с BOM (EF BB BF) почти всегда требуют специальной обработки.
