---
description: Check and fix broken encoding in vault .md files
---

# SECURITY PROTOCOL: back up before any file change

```powershell
$backup = Join-Path $env:TEMP ("kilo\backups\" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item -Path "target\*" -Destination $backup -Recurse -Force
Write-Host "Backup: $backup"
```

Never apply an untested algorithm to production files.
Always: backup → test on a copy → apply → verify.

---

## Diagnostics: how to identify the problem

Use ONLY Python — PowerShell handles Cyrillic poorly.

**Quick check:** `python .kilo/scripts/guard_encoding.py --vault`

Three types of corruption:
1. **UTF-8 decode error** — the file does not read as UTF-8 (rare)
2. **U+FFFD replacement chars** — partial data loss when decoding with `errors='replace'`
3. **Double-encoding** — the most common: valid UTF-8, but Russian text has turned into mojibake.

Sign of double-encoding: the share of uppercase Cyrillic characters (А-Я).
- Normal text: 2-5% uppercase Cyrillic
- Headings/diagrams: 5-15%
- **Double-encoding: 50-99% uppercase Cyrillic** (reliable detection)
- 15-50% with >1000 Cyrillic chars: WARNING (possible corruption)

The guard checks all three types automatically.

---

## The only working algorithm: ftfy

The ftfy (fix text for you) library — the Mozilla algorithm, the only reliable one.

```python
from ftfy import fix_text

# Backup
import shutil, os
backup = os.path.join(os.environ['TEMP'], 'kilo', 'backups',
                      __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(backup, exist_ok=True)
shutil.copy2(path, os.path.join(backup, os.path.basename(path)))

# Read
with open(path, 'rb') as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    data = data[3:]

# Fix
text = data.decode('utf-8', errors='replace')
fixed = fix_text(text)

# Verification
cyr_new = sum(1 for c in fixed if '\u0410' <= c <= '\u042F')
ratio_new = cyr_new / len(fixed) * 100 if len(fixed) > 0 else 0
if ratio_new < 8:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print(f'OK: {ratio_new:.0f}% — clean')
else:
    print(f'FAIL: {ratio_new:.0f}% — still mojibake, revert from backup')
```

---

## Safety rules (learned the hard way)

1. Always back up. Before ANY file change.
2. Do not use PowerShell for Cyrillic. Python 3.14+ only.
3. Test on a copy. If the file is unique — copy it, test it.
4. Two passes of ftfy. If it did not help — do not improvise, hand it over to the user.
5. Verify after the fix. Check the share of uppercase Cyrillic.
6. One file at a time. Do not batch — verify — commit.
7. Files with BOM (EF BB BF) almost always require special handling.
