// Vanilla JS версия - без jQuery
document.addEventListener('DOMContentLoaded', function() {
    // Ajax обновление токена
    const ajaxBtn = document.getElementById('ajax-btn');
    if (ajaxBtn) {
        ajaxBtn.addEventListener('click', function(event) {
            event.preventDefault();
            console.log('Step 1');

            fetch('/user/update-token-ajax/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Step 3');
                console.log(data);
                const tokenDiv = document.getElementById('token');
                if (tokenDiv) {
                    tokenDiv.textContent = data.key;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }

    // Копирование токена
    const copyTokenBtn = document.getElementById('copy-token-btn');
    if (copyTokenBtn) {
        copyTokenBtn.addEventListener('click', function() {
            const tokenInput = document.getElementById('apiToken');
            if (tokenInput) {
                tokenInput.select();
                document.execCommand('copy');

                // Показать уведомление
                const btn = this;
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="bi bi-check me-1"></i>Скопировано!';
                btn.classList.remove('btn-outline-secondary');
                btn.classList.add('btn-success');

                setTimeout(function() {
                    btn.innerHTML = originalText;
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-outline-secondary');
                }, 2000);
            }
        });
    }
});
