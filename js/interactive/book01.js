document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('complexity-diagnostic');
    if (!container) return;

    const questions = [
        "Насколько часто ваши решения приводят к неожиданным последствиям?",
        "Насколько сильно небольшое изменение вызывает лавинообразные эффекты?",
        "Меняется ли поведение системы само собой, без ваших действий?",
        "Приходится ли принимать решения в условиях неполной информации?",
        "Есть ли заметная задержка (дни/недели) между действием и результатом?",
        "Сталкиваетесь ли с тем, что у разных подразделений свои цели?",
        "Часто ли процессы ведут себя непредсказуемо, несмотря на инструкции?"
    ];

    const levelDescriptions = {
        1: "Уровень 1 (Объект) — базовые операции. Инструменты: чек-листы, 5S, визуальные инструкции.",
        2: "Уровень 2 (Проект) — логистика ресурсов. Инструменты: Канбан, ежедневные летучки.",
        3: "Уровень 3 (Программа) — координация групп. Инструменты: сквозные OKR, кросс-функциональные воркшопы.",
        4: "Уровень 4 (Стратегия) — выбор направления. Инструменты: стратегические сессии, принципы вместо правил.",
        5: "Уровень 5 (Политика) — формирование правил игры. Инструменты: система мотивации, публичные ценности.",
        6: "Уровень 6 (Принципы) — мета-правила. Инструменты: кодекс лидера, политика «открытой двери».",
        7: "Уровень 7 (Смыслы) — высший контекст. Инструменты: миссия, история бренда, диалог о будущем."
    };

    let html = `<div class="diagnostic-level"><h3>📊 Пройдите диагностику сложности</h3>`;
    questions.forEach((q, idx) => {
        html += `
            <div class="question-row">
                <label>${q}</label>
                <select id="q${idx}" class="complexity-select">
                    <option value="1">1 — Никогда</option>
                    <option value="2">2 — Редко</option>
                    <option value="3" selected>3 — Иногда</option>
                    <option value="4">4 — Часто</option>
                    <option value="5">5 — Постоянно</option>
                </select>
            </div>
        `;
    });
    html += `<button id="calcComplexity" class="btn-primary">Рассчитать уровень</button>
             <div id="complexityResult"></div>
             <button id="resetComplexity" class="btn-outline" style="display:none; margin-top:10px;">Пройти заново</button>
             </div>`;
    container.innerHTML = html;

    const calcBtn = document.getElementById('calcComplexity');
    const resetBtn = document.getElementById('resetComplexity');
    const resultDiv = document.getElementById('complexityResult');

    calcBtn.addEventListener('click', () => {
        let total = 0;
        for (let i = 0; i < questions.length; i++) {
            total += parseInt(document.getElementById(`q${i}`).value);
        }
        let avg = total / questions.length;
        let level;
        if (avg <= 1.5) level = 1;
        else if (avg <= 2.2) level = 2;
        else if (avg <= 2.9) level = 3;
        else if (avg <= 3.6) level = 4;
        else if (avg <= 4.3) level = 5;
        else level = (avg <= 4.8) ? 6 : 7;

        resultDiv.innerHTML = `
            <div class="result-card">
                <strong>Ваш средний балл:</strong> ${avg.toFixed(1)}<br>
                <strong>Уровень сложности:</strong> ${level}<br>
                ${levelDescriptions[level]}<br>
                <em>Рекомендация:</em> обратитесь к соответствующей главе книги и используйте инструменты из раздела 5.
            </div>
        `;
        calcBtn.style.display = 'none';
        resetBtn.style.display = 'inline-block';
    });

    resetBtn.addEventListener('click', () => {
        for (let i = 0; i < questions.length; i++) {
            document.getElementById(`q${i}`).value = '3';
        }
        resultDiv.innerHTML = '';
        calcBtn.style.display = 'inline-block';
        resetBtn.style.display = 'none';
    });
});

// Второй виджет – диагностика симптомов
document.addEventListener('DOMContentLoaded', function() {
    const symptomContainer = document.getElementById('symptom-diagnostic');
    if (!symptomContainer) return;

    const symptoms = [
        { phrase: "«Сотрудники не думают, ждут каждой команды»", level: 2, question: "Какой главный приоритет у отдела на этот квартал? Известен ли он каждому?" },
        { phrase: "«Постоянные авралы, всё горит»", level: 3, question: "У нас есть общий и понятный всем план на месяц? Все отделы видят свою часть?" },
        { phrase: "«Отделы работают как слепые котята»", level: 4, question: "Есть ли 3 главные цели компании на год? Понимает ли каждый отдел, как его работа к ним ведёт?" },
        { phrase: "«Мы постоянно опаздываем с продуктами, конкуренты обходят»", level: 4, question: "Наша стратегия реактивна или проактивна? Как мы отслеживаем рынок?" },
        { phrase: "«Люди саботируют, токсичная атмосфера»", level: 5, question: "За что у нас реально хвалят и ругают? Это совпадает с ценностями на стенде?" },
        { phrase: "«Таланты уходят, все работают только за деньги»", level: 7, question: "Зачем мы существуем кроме заработка? Какую проблему клиентов мы решаем?" }
    ];

    let selectHtml = `<select id="symptomSelect" class="symptom-selector">
                        <option value="">-- Выберите фразу, которую слышите чаще всего --</option>`;
    symptoms.forEach((s, idx) => {
        selectHtml += `<option value="${idx}">${s.phrase}</option>`;
    });
    selectHtml += `</select><div id="symptomResult" class="symptom-result" style="display:none;"></div>`;

    symptomContainer.innerHTML = `<div class="symptom-diagnostic"><h3>🔍 Диагностика по симптомам</h3>${selectHtml}</div>`;
    const selectEl = document.getElementById('symptomSelect');
    const resultDiv = document.getElementById('symptomResult');

    selectEl.addEventListener('change', () => {
        const idx = selectEl.value;
        if (idx === "") {
            resultDiv.style.display = 'none';
            return;
        }
        const s = symptoms[idx];
        resultDiv.innerHTML = `<strong>Вероятный уровень проблемы:</strong> ${s.level}<br>
                               <strong>Вопрос для самоанализа:</strong> ${s.question}<br>
                               <em>Рекомендуем обратиться к части 3 книги и выполнить алгоритм «Сверху вниз».</em>`;
        resultDiv.style.display = 'block';
    });
});