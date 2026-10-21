#!/usr/bin/env python3
"""Generate the /articles/ HTML partials from vault articles.

Converts each vault research article into an HTML partial (same rules as
pipelines/obsidian-to-site/md_to_partial.py), then:
  - rewrites Markdown links [text](url) as real <a> tags (the converter leaves
    them literal, since it only understands [[wiki]] links);
  - appends a "Читайте также" interlink block pointing at sibling articles,
    /weapons/ and /genome/.

Site interlinks deliberately live here, not in the .md: the vault files stay
free of site-only markup and the .md keeps its native [[wiki]] backlinks.

Idempotent: always regenerated from the vault source. Re-run after vault edits.
Entries whose vault source does not exist yet are skipped.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'pipelines' / 'obsidian-to-site'))
from md_to_partial import convert  # noqa: E402

VAULT = Path(r'C:\Users\evgeniy.bogdanov\Documents\Personal Vault')
ARTICLES = VAULT / 'Книга' / '01_Статьи'
OUT = REPO / 'site' / 'src' / 'content' / 'articles'

ARTICLES_MAP = [
    {
        'src': ARTICLES / '40_Антихрупкая_стратегия.md',
        'dst': OUT / '40-antihrupkaya-strategiya.html',
        'comment': 'Статьи: Антихрупкая стратегия',
        'links': [
            ('/articles/strategy/amortizacionnaya-lovushka/',
             'Амортизационная ловушка',
             'почему инвестиции в рост разрушают стоимость: финансово-учётная механика амортизации на падающем рынке.'),
            ('/weapons/antikrizis/',
             'Антикризис',
             'что делать, когда падение уже началось: протокол выхода из хаоса за 6 месяцев.'),
            ('/weapons/dengi-v-dvizhenii/',
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
        'comment': 'Статьи: Амортизационная ловушка',
        'links': [
            ('/articles/strategy/antihrupkaya-strategiya/',
             'Антихрупкая стратегия',
             'общая рамка: управляемое сжатие, антихрупкий портфель и дисциплина капитала.'),
            ('/weapons/dengi-v-dvizhenii/',
             'Деньги в движении',
             'себестоимость и операционный рычаг в производственной системе.'),
            ('/weapons/antikrizis/',
             'Антикризис',
             'протокол действий при падении за 6 месяцев.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов.'),
        ],
    },
    {
        'src': ARTICLES / '50_Оптимизация_развитие_антикризис.md',
        'dst': OUT / '50-optimizaciya-razvitie-antikrizis.html',
        'comment': 'Статьи: Почему компании увольняют оптимизаторов',
        'links': [
            ('/articles/economics/sebestoimost-i-realnost/',
             'Себестоимость и реальность',
             'почему средняя себестоимость ошибается и как считать экономику заказа в часах узкого места.'),
            ('/weapons/antikrizis/',
             'Антикризис',
             'протокол вывода завода из кризиса, когда поток ликвидности уже разорван.'),
            ('/weapons/dva-tipa-upravleniya/',
             'Два типа управления',
             'текущая стабильность и способность системы меняться — разные мандаты.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов для управленческого контура.'),
        ],
    },
    {
        'src': ARTICLES / '51_Себестоимость_и_реальность.md',
        'dst': OUT / '51-sebestoimost-i-realnost.html',
        'comment': 'Статьи: Себестоимость и реальность',
        'links': [
            ('/articles/economics/ne-tolko-proekty/',
             'Не только проекты',
             'почему инвестиции в качество управления не проходят инвесткомитет и что с этим делать.'),
            ('/articles/strategy/amortizacionnaya-lovushka/',
             'Амортизационная ловушка',
             'как постоянные затраты давят на себестоимость при падении загрузки.'),
            ('/weapons/dengi-v-dvizhenii/',
             'Деньги в движении',
             'себестоимость и операционный рычаг в производственной системе.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов.'),
        ],
    },
    {
        'src': ARTICLES / '52_Не_только_проекты.md',
        'dst': OUT / '52-ne-tolko-proekty.html',
        'comment': 'Статьи: Правило, которое вы установили',
        'links': [
            ('/articles/management/optimizaciya-razvitie-antikrizis/',
             'Почему компании увольняют оптимизаторов',
             'структурная ловушка, запас устойчивости и онтология развития.'),
            ('/articles/strategy/antihrupkaya-strategiya/',
             'Антихрупкая стратегия',
             'управляемое сжатие и дисциплина капитала на падающем рынке.'),
            ('/weapons/antikrizis/',
             'Антикризис',
             'протокол действий при падении за 6 месяцев.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов.'),
        ],
    },
    {
        'src': ARTICLES / '53_Цифровизация_1.0.md',
        'dst': OUT / '53-cifrovizaciya-1-0.html',
        'comment': 'Статьи: Цифровизация 1.0',
        'links': [
            ('/articles/digital/cifrovizaciya-2-0/',
             'Цифровизация 2.0',
             'гипотеза описания системы через объект, роли и события.'),
            ('/articles/digital/ii-zoopark/',
             'ИИ-зоопарк',
             'что происходит, когда ИИ-инструменты появляются вне общего контура.'),
            ('/weapons/cifrovoy-dvoynik/',
             'Цифровой двойник',
             'объектное мышление для руководителя производства.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов.'),
        ],
    },
    {
        'src': ARTICLES / '54_Цифровизация_2.0.md',
        'dst': OUT / '54-cifrovizaciya-2-0.html',
        'comment': 'Статьи: Цифровизация 2.0',
        'links': [
            ('/articles/digital/cifrovizaciya-1-0/',
             'Цифровизация 1.0',
             'атлас 22 стыков классического промышленного ИТ.'),
            ('/articles/digital/ii-zoopark/',
             'ИИ-зоопарк',
             'теневой ИИ и три модели организации функции.'),
            ('/weapons/nervnaya-sistema/',
             'Нервная система компании',
             'информационные потоки и обратная связь на производстве.'),
            ('/genome/',
             'Геном завода',
             'типизированная библиотека процессов.'),
        ],
    },
    {
        'src': ARTICLES / '55_ИИ-зоопарк.md',
        'dst': OUT / '55-ii-zoopark.html',
        'comment': 'Статьи: ИИ-зоопарк',
        'links': [
            ('/articles/digital/cifrovizaciya-1-0/',
             'Цифровизация 1.0',
             'почему единый источник правды — иллюзия и как читать стыки систем.'),
            ('/articles/digital/cifrovizaciya-2-0/',
             'Цифровизация 2.0',
             'гипотеза описания системы через объект, роли и события.'),
            ('/weapons/neizbezhnoe-ispolnenie/',
             'Неизбежное исполнение',
             '12 рычагов Медоуз: от слабых к сильным.'),
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
    return ('<section class="article-links">\n'
            '<h2 data-toc="skip">Читайте также</h2>\n'
            '<ul>' + lis + '</ul>\n'
            '</section>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for art in ARTICLES_MAP:
        if not art['src'].exists():
            print('skip (missing source):', art['src'].name)
            continue
        md = art['src'].read_text(encoding='utf-8')
        html = convert(md)
        html = MD_LINK.sub(lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), html)
        comment = art.get('comment', '')
        header = ('<!-- %s -->\n' % comment) if comment else ''
        body = header + html.rstrip() + '\n\n' + links_block(art['links']) + '\n'
        art['dst'].write_text(body, encoding='utf-8', newline='\n')
        written += 1
        print('wrote', art['dst'].name, len(body), 'bytes')
    print('partials written:', written)


if __name__ == '__main__':
    main()
