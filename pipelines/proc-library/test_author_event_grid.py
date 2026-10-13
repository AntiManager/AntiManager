"""Tests for author_event_grid.py (event-grid derivation, plan 1791810263662).

Regression guards for the Phase-D review findings (session 6):
- de-identification must not shatter `### 8.N.` headings into `### .`;
- the H6 «Регламент 8.x» phrase must lose the client wording but keep its number;
- owner/participant override and short display names behave as specified.

Run:  python -m pytest -q -p no:cacheprovider   (from pipelines/proc-library)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import author_event_grid as aeg  # noqa: E402


def test_section_heading_number_is_preserved():
    # a bare `8.x` must never be stripped (kills `### 8.1.` -> `### .`)
    assert aeg.clean("### 8.1. Tier 1–3 (ежедневные операционные совещания)") == \
        "### 8.1. Tier 1–3 (ежедневные операционные совещания)"
    assert aeg.clean("### 8.10. Анализ портфеля проектов улучшений") == \
        "### 8.10. Анализ портфеля проектов улучшений"


def test_reglament_phrase_loses_client_wording_keeps_number():
    out = aeg.clean("Регламент 8.2 (Tier 4), 8.8 (Обзор проектов)")
    assert "Регламент" not in out            # H6 stop-word must be gone
    assert "8.2" in out and "8.8" in out     # numbers stay traceable


def test_render_body_keeps_subsection_heading():
    sec = {"num": "8", "title": "Регламенты проведения ключевых событий",
           "body": ["### 8.1. Tier 1–3 (ежедневные операционные совещания)",
                    "", "- текст"]}
    body = "\n".join(aeg.render_body(sec))
    assert "### 8.1. Tier 1–3" in body
    assert "### ." not in body


def test_short_name_drops_domain_qualifier():
    assert aeg.short_name("Главный механик (техслужба)") == "Главный механик"
    assert aeg.short_name("Руководитель склада (логистика)") == "Руководитель склада"
    assert aeg.short_name("Начальник смены / Мастер") == "Начальник смены / Мастер"


def test_override_resolves_only_unresolvable_labels():
    reg = aeg.check_artifacts.load_registry()
    # registry-resolvable labels stay registry-authoritative (primary code)
    assert aeg.owner_code(reg, "Диспетчер / учётчик") == "РП"
    # genuinely unresolvable label falls through to the override table
    assert aeg.owner_code(reg, "Специалист по развитию ПС") == "ГТ"
    # participant mapping uses the same fallback
    assert "ГТ" in aeg.participant_codes(reg, "Специалист по развитию ПС")
