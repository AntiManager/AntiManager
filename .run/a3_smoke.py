# -*- coding: utf-8 -*-
"""Smoke-check the built /genome/documents/a3-reshenie-problem/ page."""
import io
import os
import re

PAGE = os.path.join('site', 'dist', 'genome', 'documents',
                    'a3-reshenie-problem', 'index.html')
t = io.open(PAGE, encoding='utf-8').read()
out = []
out.append('size %d' % len(t))
out.append('h1: %s' % re.findall(r'<h1[^>]*>(.*?)</h1>', t)[:2])
out.append('h2 count %d' % len(re.findall(r'<h2[ >]', t)))
out.append('toc %s' % ('article-toc' in t))
out.append('Article node %s' % ('"@type": "Article"' in t))
out.append('articleSection %s' % ('"articleSection"' in t))
out.append('breadcrumb position 4 %s' % ('"position": 4' in t))
out.append('placeholder leak %s' % ('[\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f-\u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0442\u043e\u0440]' in t
                                    or '{\u0434\u0430\u0442\u0430}' in t))
out.append('raw md links %s' % bool(re.search(r'\]\(https?:', t)))
out.append('draft tokens %s' % bool(re.search(r'\b(TODO|TBD|FIXME)\b', t)))
out.append('pdf link %s' % ('/materials/a3-reshenie-problem.pdf' in t))
out.append('docx link %s' % ('/materials/a3-reshenie-problem.docx' in t))
out.append('cta %s' % ('/contact/?pack=documents' in t))
links = re.findall(r'<section class="article-links"[\s\S]*?</section>', t)
hrefs = re.findall(r'href="(/[^"]*)"', links[0]) if links else []
out.append('interlinks %s' % hrefs)
sys_out = io.open(os.path.join('.run', 'a3_smoke.txt'), 'w', encoding='utf-8')
sys_out.write('\n'.join(out) + '\n')
sys_out.close()
print('\n'.join(out))
