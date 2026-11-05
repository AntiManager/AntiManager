# -*- coding: utf-8 -*-
"""Check sitemap, hub card and the A3 backlinks in the built dist/."""
import io
import os

SITE = os.path.join('site', 'dist')


def read(*parts):
    return io.open(os.path.join(SITE, *parts), encoding='utf-8').read()


out = []
sm = read('sitemap.xml')
out.append('a3 in sitemap: %s' % ('/genome/documents/a3-reshenie-problem/' in sm))
out.append('total urls: %d' % sm.count('<loc>'))

hub = read('genome', 'documents', 'index.html')
out.append('hub card: %s | tiles: %d' % ('a3-reshenie-problem' in hub,
                                         hub.count('class="doc-tile"')))
out.append('flow step 05: %s' % ('05' in hub))

for slug in ('ritm-soveshchaniy', 'gemba-obhod', 'snu-kontur-uluchsheniy'):
    page = read('genome', 'documents', slug, 'index.html')
    out.append('%s -> a3 backlink: %s' % (slug, 'a3-reshenie-problem' in page))

print('\n'.join(out))
