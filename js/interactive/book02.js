// Интерактивный конструктор карты гипотез для книги 02
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('interactive-book02');
    if (!container) return;

    // Генерируем интерфейс: форма для цели и до 3 гипотез
    container.innerHTML = `
        <div class="hypothesis-builder">
            <div class="form-group">
                <label>Стратегическая цель (SMART, измеримая)</label>
                <input type="text" id="strategicGoal" placeholder="Например: Снизить брак на сварке с 7% до 2% за 3 месяца">
            </div>
            <hr style="margin: 1rem 0;">
            <h3>Гипотеза №1</h3>
            <div class="form-group">
                <label>Если мы (действие)...</label>
                <input type="text" id="action1" placeholder="например: введём ежечасную самопроверку по чек-листу">
            </div>
            <div class="form-group">
                <label>То (субъект) изменит поведение на...</label>
                <input type="text" id="behavior1" placeholder="например: сварщик будет сверяться с эталоном">
            </div>
            <div class="form-group">
                <label>Потому что (механизм)...</label>
                <input type="text" id="because1" placeholder="например: ему не надо лезть в телефон или звать мастера">
            </div>
            <hr style="margin: 1rem 0;">
            <h3>Гипотеза №2 (опционально)</h3>
            <div class="form-group">
                <label>Если мы...</label>
                <input type="text" id="action2" placeholder="">
            </div>
            <div class="form-group">
                <label>То субъект изменит поведение на...</label>
                <input type="text" id="behavior2" placeholder="">
            </div>
            <div class="form-group">
                <label>Потому что...</label>
                <input type="text" id="because2" placeholder="">
            </div>
            <hr style="margin: 1rem 0;">
            <h3>Гипотеза №3 (опционально)</h3>
            <div class="form-group">
                <label>Если мы...</label>
                <input type="text" id="action3" placeholder="">
            </div>
            <div class="form-group">
                <label>То субъект изменит поведение на...</label>
                <input type="text" id="behavior3" placeholder="">
            </div>
            <div class="form-group">
                <label>Потому что...</label>
                <input type="text" id="because3" placeholder="">
            </div>
            <button id="buildMapBtn" class="btn-primary">Собрать карту гипотез</button>
            <button id="copyMapBtn" class="btn-outline" style="margin-left: 10px;">Копировать в буфер</button>
            <div id="hypothesisMap" class="hypothesis-result" style="margin-top: 20px;"></div>
        </div>
    `;

    const goalInput = document.getElementById('strategicGoal');
    const action1 = document.getElementById('action1');
    const behavior1 = document.getElementById('behavior1');
    const because1 = document.getElementById('because1');
    const action2 = document.getElementById('action2');
    const behavior2 = document.getElementById('behavior2');
    const because2 = document.getElementById('because2');
    const action3 = document.getElementById('action3');
    const behavior3 = document.getElementById('behavior3');
    const because3 = document.getElementById('because3');
    const buildBtn = document.getElementById('buildMapBtn');
    const copyBtn = document.getElementById('copyMapBtn');
    const mapDiv = document.getElementById('hypothesisMap');

    function buildMap() {
        const goal = goalInput.value.trim();
        if (!goal) {
            mapDiv.innerHTML = '<span style="color: #C62828;">⚠️ Укажите стратегическую цель (хотя бы кратко).</span>';
            return;
        }

        let tableHtml = `<table style="width:100%; border-collapse:collapse;"><thead><tr><th>Гипотеза</th><th>Если мы…</th><th>То поведение…</th><th>Потому что…</th></tr></thead><tbody>`;
        
        const hypotheses = [
            { action: action1.value, behavior: behavior1.value, because: because1.value, id: 1 },
            { action: action2.value, behavior: behavior2.value, because: because2.value, id: 2 },
            { action: action3.value, behavior: behavior3.value, because: because3.value, id: 3 }
        ];

        let hasAny = false;
        hypotheses.forEach(h => {
            if (h.action || h.behavior || h.because) {
                hasAny = true;
                tableHtml += `<tr>
                    <td>Гипотеза ${h.id}</td>
                    <td>${h.action || '—'}</td>
                    <td>${h.behavior || '—'}</td>
                    <td>${h.because || '—'}</td>
                </tr>`;
            }
        });

        if (!hasAny) {
            mapDiv.innerHTML = '<span style="color: #C62828;">⚠️ Заполните хотя бы одну гипотезу.</span>';
            return;
        }

        tableHtml += `</tbody></table>`;
        const fullOutput = `<strong>Стратегическая цель:</strong> ${goal}<br><br><strong>Карта гипотез:</strong><br>${tableHtml}`;
        mapDiv.innerHTML = fullOutput;
    }

    function copyToClipboard() {
        const text = mapDiv.innerText;
        if (text && text !== '') {
            navigator.clipboard.writeText(text).then(() => {
                alert('Карта гипотез скопирована в буфер обмена');
            }).catch(() => {
                alert('Не удалось скопировать, скопируйте вручную');
            });
        } else {
            alert('Сначала сгенерируйте карту гипотез');
        }
    }

    buildBtn.addEventListener('click', buildMap);
    copyBtn.addEventListener('click', copyToClipboard);
});