#!/usr/bin/env python3
"""Generate the /strategy/ HTML partials from vault articles.

Converts each vault research article into an HTML partial (same rules as
pipelines/obsidian-to-site/md_to_partial.py), then:
  - rewrites Markdown links [text](url) as real <a> tags (the converter leaves
    them literal, since it only understands [[wiki]] links);
  - appends a "Читайте также" interlink block pointing at /weapons/, /genome/
    and the sibling strategy article.

Site interlinks deliberately live here, not in the .md: the vault files stay
free of site-only markup and the .md keeps its native [[wiki]] backlinks.

Idempotent: always regenerated from the vault source. Re-run after vault edits.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'pipelines' / 'obsidian-to-site'))
from md_to_partial import convert  # noqa: E402

VAULT = Path(r'C:\Users\evgeniy.bogdanov\Documents\Personal Vault')
ARTICLES = VAULT / 'Книга' / '01_Статьи'
OUT = REPO / 'site' / 'src' / 'content' / 'strategy'

ARTICLES_MAP = [
    {
        'src': ARTICLES / '40_Антихрупкая_стратегия.md',
        'dst': OUT / '40-antihrupkaya-strategiya.html',
        'comment': 'Стратегия: Антихрупкая стратегия',
        'links': [
            ('/strategy/amortizacionnaya-lovushka/',
             'Амортизационная ловушка',
             'почему инвестиции в рост разрушают стоимость: финансово-учётная механика амортизации на падающем рынке.'),
            ('/weapons/18-antikrizis/',
             'Антикризис',
             'что делать, когда падение уже началось: протокол выхода из хаоса за 6 месяцев.'),
            ('/weapons/07-dengi-v-dvizhenii/',
             'Деньги в движении',
             'себестоимость и операционный рычаг в производственной системе.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов для управленческого контура.'),
        ],
    },
    {
        'src': ARTICLES / '41_Амортизационная_ловушка.md',
        'dst': OUT / '41-amortizacionnaya-lovushka.html',
        'comment': 'Стратегия: Амортизационная ловушка',
        'links': [
            ('/strategy/antihrupkaya-strategiya/',
             'Антихрупкая стратегия',
             'общая рамка: управляемое сжатие, антихрупкий портфель и дисциплина капитала.'),
            ('/weapons/07-dengi-v-dvizhenii/',
             'Деньги в движении',
             'себестоимость и операционный рычаг в производственной системе.'),
            ('/weapons/18-antikrizis/',
             'Антикризис',
             'протокол действий при падении за 6 месяцев.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов.'),
        ],
    },
]

MD_LINK = re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)')


def links_block(items):
    lis = ''.join(
        '<li><a href="%s">%s</a> — %s</li>' % (href, label, desc)
        for href, label, desc in items
    )
    # data-toc="skip" keeps the interlinks heading out of the article TOC.
    return ('<section class="strategy-links">\n'
            '<h2 data-toc="skip">Читайте также</h2>\n'
            '<ul>' + lis + '</ul>\n'
            '</section>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for art in ARTICLES_MAP:
        md = art['src'].read_text(encoding='utf-8')
        html = convert(md)
        html = MD_LINK.sub(lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), html)
        comment = art.get('comment', '')
        header = ('<!-- %s -->\n' % comment) if comment else ''
        body = header + html.rstrip() + '\n\n' + links_block(art['links']) + '\n'
        art['dst'].write_text(body, encoding='utf-8', newline='\n')
        print('wrote', art['dst'].name, len(body), 'bytes')


if __name__ == '__main__':
    main()
