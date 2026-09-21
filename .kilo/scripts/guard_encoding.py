"""
Encoding guard: verify UTF-8 integrity + content health of vault/book files.

Detects THREE corruption types:
  1. UTF-8 decode errors (invalid byte sequences)
  2. U+FFFD replacement characters (lossy decode)
  3. Double-encoding: valid UTF-8 but garbage Cyrillic (>50% uppercase = definite, 15-50% + >1000 Cyrillic chars = possible)

Usage:
  python guard_encoding.py <file>          -- check a single file
  python guard_encoding.py --vault         -- check all vault .md files (requires VAULT_DIR; prints a hint and exits 0 if unset)
  python guard_encoding.py --project       -- check project .md files
  python guard_encoding.py --backup <file> -- backup then check
  python guard_encoding.py --fix <file>    -- fix double-encoding with ftfy

Exit codes:
  0 = file is healthy (or the requested scan was skipped, e.g. --vault without VAULT_DIR)
  1 = file has encoding issues
  2 = usage error
"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Project root is derived from this script's location: <root>/.kilo/scripts/guard_encoding.py
PROJECT = str(Path(__file__).resolve().parents[2])
# Vault path is environment-specific; set VAULT_DIR to enable --vault.
VAULT = os.environ.get('VAULT_DIR')
BACKUP_DIR = os.path.join(os.environ.get('TEMP', r'C:\Windows\Temp'), 'kilo', 'backups')

def check_file(filepath):
    """Check if file has healthy UTF-8 Cyrillic content.
    
    Returns (is_valid, message, stats_dict)
    
    Three checks:
    1. Valid UTF-8 byte sequences
    2. No U+FFFD replacement characters  
    3. Double-encoding detection via uppercase Cyrillic ratio
       Normal Russian text: 2-5% uppercase (А-Я)
       Double-encoded mojibake: 20-99% uppercase
       Threshold: >8% = corrupted (per fix-encoding.md spec)
    """
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
    except Exception as e:
        return False, f"READ ERROR: {e}", {}
    
    if len(raw) == 0:
        return True, "empty file", {'size': 0}
    
    stats = {'size': len(raw), 'has_bom': raw[:3] == b'\xef\xbb\xbf'}
    
    # Check 1: valid UTF-8 decode
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return False, f"UTF-8 DECODE ERROR at byte {e.start} (reason: {e.reason})", stats
    
    # Check 2: no replacement characters
    repl_count = text.count('\ufffd')
    stats['replacement_chars'] = repl_count
    if repl_count > 0:
        return False, f"U+FFFD REPLACEMENT CHARACTERS: {repl_count}", stats
    
    # Check 3: double-encoding via uppercase Cyrillic ratio
    # REAL double-encoding: 87-99% uppercase (files 02,13,20 were 99%)
    # Normal Russian prose:   2-5%  uppercase
    # Headers + acronyms:     5-12% uppercase  
    # Small diagram files:    up to 25% uppercase (false positive risk)
    # Thresholds:
    #   > 50%: CORRUPT (definite double-encoding)
    #   15-50% + >1000 Cyrillic: WARNING
    #   < 15% or < 500 Cyrillic: OK
    upper = sum(1 for c in text if '\u0410' <= c <= '\u042F')  # А-Я
    lower = sum(1 for c in text if '\u0430' <= c <= '\u044F')  # а-я
    total_cyr = upper + lower
    stats['cyr_upper'] = upper
    stats['cyr_lower'] = lower
    stats['cyr_total'] = total_cyr
    
    if total_cyr > 200 and upper > 0:
        ratio = upper / total_cyr * 100
        stats['uppercase_pct'] = round(ratio, 1)
        
        if ratio > 50:
            # Definitely double-encoded
            return False, f"DOUBLE-ENCODING (definite): {ratio:.1f}% uppercase Cyrillic (expected <5%, got {upper}/{total_cyr})", stats
        elif ratio > 15 and total_cyr > 1000:
            # Warning: could be double-encoding or just header-heavy content
            return False, f"DOUBLE-ENCODING (possible): {ratio:.1f}% uppercase Cyrillic (threshold 15%, got {upper}/{total_cyr} chars)", stats
    
    return True, "OK", stats

def backup_file(filepath):
    """Create a timestamped backup of the file."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname = os.path.basename(filepath)
    backup_path = os.path.join(BACKUP_DIR, f"{ts}_{fname}")
    shutil.copy2(filepath, backup_path)
    return backup_path

def check_vault():
    """Check all .md files in the vault."""
    issues = []
    total = 0
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fn in files:
            if not fn.endswith('.md'):
                continue
            total += 1
            fp = os.path.join(root, fn)
            ok, msg, stats = check_file(fp)
            if not ok:
                rel = os.path.relpath(fp, VAULT)
                issues.append((rel, msg, stats))
    
    print(f"Vault scan: {total} files checked")
    if issues:
        print(f"\n{'='*60}")
        print(f"ISSUES FOUND: {len(issues)} files")
        print(f"{'='*60}")
        for path, msg, stats in issues:
            print(f"\n  {path}")
            print(f"    {msg}")
            print(f"    stats: {stats}")
        return 1
    else:
        print("All files OK.")
        return 0

def check_project():
    """Check project text files."""
    issues = []
    for root, dirs, files in os.walk(PROJECT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('.git', 'node_modules', 'site')]
        for fn in files:
            ext = os.path.splitext(fn)[1]
            if ext not in ('.md', '.html', '.json', '.css', '.js', '.txt'):
                continue
            fp = os.path.join(root, fn)
            ok, msg, stats = check_file(fp)
            if not ok:
                rel = os.path.relpath(fp, PROJECT)
                issues.append((rel, msg, stats))
    
    print(f"Project scan: {len(issues)} issues")
    for path, msg, stats in issues:
        print(f"  {path}: {msg}")
    return 0 if not issues else 1

def fix_file(filepath):
    """Fix double-encoded file using ftfy."""
    try:
        import site
        import sys as _sys
        _sys.path.insert(0, site.getusersitepackages())
        from ftfy import fix_text
    except ImportError:
        print("ERROR: ftfy not installed. Run: pip install ftfy")
        return 1
    
    print(f"Fixing: {filepath}")
    
    # Backup first
    bp = backup_file(filepath)
    print(f"Backup: {bp}")
    
    # Read
    with open(filepath, 'rb') as f:
        raw = f.read()
    has_bom = raw[:3] == b'\xef\xbb\xbf'
    if has_bom:
        raw = raw[3:]
    
    # Check before
    text = raw.decode('utf-8', errors='replace')
    upper_before = sum(1 for c in text if '\u0410' <= c <= '\u042F')
    lower_before = sum(1 for c in text if '\u0430' <= c <= '\u044F')
    total_before = upper_before + lower_before
    ratio_before = upper_before / total_before * 100 if total_before > 0 else 0
    print(f"Before: {ratio_before:.1f}% uppercase ({upper_before}/{total_before})")
    
    if ratio_before < 8:
        print("SKIP: already healthy")
        return 0
    
    # Fix
    fixed = fix_text(text)
    
    # Check after
    upper_after = sum(1 for c in fixed if '\u0410' <= c <= '\u042F')
    lower_after = sum(1 for c in fixed if '\u0430' <= c <= '\u044F')
    total_after = upper_after + lower_after
    ratio_after = upper_after / total_after * 100 if total_after > 0 else 0
    print(f"After:  {ratio_after:.1f}% uppercase ({upper_after}/{total_after})")
    
    if ratio_after > 10:
        print(f"FAILED: ftfy did not fix (ratio still {ratio_after:.1f}%)")
        print(f"Restore backup: {bp}")
        return 1
    
    # Write
    output = fixed.encode('utf-8')
    if has_bom:
        output = b'\xef\xbb\xbf' + output
    with open(filepath, 'wb') as f:
        f.write(output)
    
    print("FIXED successfully")
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    
    cmd = sys.argv[1]
    
    if cmd == '--vault':
        if not VAULT:
            print("VAULT_DIR is not set; skipping vault scan. "
                  "Set the VAULT_DIR environment variable to the vault path.")
            return 0
        return check_vault()
    elif cmd == '--project':
        return check_project()
    elif cmd == '--backup':
        if len(sys.argv) < 3:
            print("Usage: guard_encoding.py --backup <file>")
            return 2
        fp = sys.argv[2]
        bp = backup_file(fp)
        print(f"Backup: {bp}")
        ok, msg, stats = check_file(fp)
        print(f"Check: {msg}")
        return 0 if ok else 1
    elif cmd == '--fix':
        if len(sys.argv) < 3:
            print("Usage: guard_encoding.py --fix <file>")
            return 2
        return fix_file(sys.argv[2])
    else:
        # Treat as file path
        fp = cmd
        if not os.path.exists(fp):
            print(f"ERROR: file not found: {fp}")
            return 2
        ok, msg, stats = check_file(fp)
        print(f"{'OK' if ok else 'CORRUPT'}: {msg}")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
