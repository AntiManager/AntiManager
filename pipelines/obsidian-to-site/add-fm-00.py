import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Path is environment-specific: pass it as argv[1], or set VAULT_DIR.
# The vault-relative location is the same for everyone.
REL_PATH = os.path.join('Книга', '01_Статьи', '00_Маятник_управления.md')
if len(sys.argv) > 1:
    path = sys.argv[1]
elif os.environ.get('VAULT_DIR'):
    path = os.path.join(os.environ['VAULT_DIR'], REL_PATH)
else:
    print('Usage: add-fm-00.py <note.md>  (or set VAULT_DIR)')
    sys.exit(2)

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

frontmatter = """---
tags: [book, chapter, management, system-thinking]
status: review
created: 2025-11-04
updated: 2026-07-21
aliases: [Маятник управления, Management pendulum]
---

"""

# Only add if no frontmatter exists
if not text.startswith('---'):
    new_text = frontmatter + text
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    lines = new_text.split('\n')
    print('ADDED frontmatter')
    for i in range(min(10, len(lines))):
        if lines[i].strip():
            print(f'  L{i}: {lines[i][:80]}')
else:
    print('ALREADY has frontmatter')
