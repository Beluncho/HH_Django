/* Индикатор работы для форм тренажёра.
 *
 * Прогрессивное улучшение: без этого файла приложение работает как прежде —
 * кнопки остаются обычными submit-кнопками. Скрипт лишь показывает, что запрос
 * ушёл, а система не повисла: анализ вакансий, построение embeddings и вызовы
 * LLM идут синхронно, и до ответа страница не меняется. Раньше единственным
 * признаком жизни была родная крутилка браузера во вкладке.
 */
(function () {
    "use strict";

    var BUSY_TIMEOUT_MS = 90000;
    var HINT_TEXT = "Ответа нет больше 90 секунд. Вероятно, внешний сервис не отвечает — попробуйте ещё раз.";
    var busy = null;

    function progressStrip() {
        return document.getElementById("progress-strip");
    }

    function submitButton(form, submitter) {
        if (submitter && submitter.type === "submit") {
            return submitter;
        }
        return form.querySelector('button[type="submit"], input[type="submit"]');
    }

    function showHint(form) {
        var hint = document.createElement("p");
        hint.className = "busy-hint";
        hint.setAttribute("role", "status");
        hint.textContent = HINT_TEXT;
        form.appendChild(hint);
        return hint;
    }

    /* Снимает состояние «идёт работа»: возвращает подпись кнопки, снимает
     * aria-состояния и прячет полосу. Нужен и после таймаута, и при возврате
     * на страницу из кэша браузера, где кнопка осталась заблокированной. */
    function reset() {
        if (!busy) {
            return;
        }

        window.clearTimeout(busy.timer);
        busy.form.removeAttribute("aria-busy");
        busy.form.removeAttribute("data-submitting");

        if (busy.button) {
            busy.button.disabled = false;
            busy.button.removeAttribute("aria-busy");
            busy.button.removeAttribute("aria-disabled");
            if (busy.idleMarkup !== null) {
                busy.button.innerHTML = busy.idleMarkup;
            }
        }

        if (busy.hint) {
            busy.hint.remove();
        }

        var strip = progressStrip();
        if (strip) {
            strip.hidden = true;
        }

        busy = null;
    }

    function markBusy(form, button) {
        busy = {
            form: form,
            button: button,
            idleMarkup: button ? button.innerHTML : null,
            hint: null,
            timer: 0
        };

        if (button) {
            var busyLabel = button.dataset.busy;
            if (busyLabel) {
                button.innerHTML = "";
                var spinner = document.createElement("span");
                spinner.className = "spinner-border spinner-border-sm";
                spinner.setAttribute("aria-hidden", "true");
                button.appendChild(spinner);
                button.appendChild(document.createTextNode(busyLabel));
            }
            button.setAttribute("aria-busy", "true");
            button.setAttribute("aria-disabled", "true");
        }

        form.setAttribute("aria-busy", "true");
        form.setAttribute("data-submitting", "1");

        var strip = progressStrip();
        if (strip) {
            strip.hidden = false;
        }

        /* Отключаем кнопку следующим тактом: браузер собирает данные формы
         * после обработки события submit, и отключённый элемент в них уже не
         * попадёт. Повторную отправку до этого момента отсекает атрибут
         * data-submitting — сюда мы больше не вернёмся. */
        window.setTimeout(function () {
            if (busy && busy.form === form && busy.button === button && button) {
                button.disabled = true;
            }
        }, 0);

        busy.timer = window.setTimeout(function () {
            var form_ = busy.form;
            reset();
            if (form_.isConnected) {
                busy = { form: form_, button: null, idleMarkup: null, hint: showHint(form_), timer: 0 };
            }
        }, BUSY_TIMEOUT_MS);
    }

    document.addEventListener("submit", function (event) {
        /* Форма может отменить отправку (валидация, перехват) — тогда
         * показывать «идёт работа» нечего. */
        if (event.defaultPrevented) {
            return;
        }

        var form = event.target;
        if (!form || form.tagName !== "FORM" || form.dataset.submitting) {
            return;
        }

        markBusy(form, submitButton(form, event.submitter));
    });

    /* Возврат по «Назад» восстанавливает страницу из кэша вместе с
     * заблокированной кнопкой — состояние нужно снять. */
    window.addEventListener("pageshow", reset);
})();
