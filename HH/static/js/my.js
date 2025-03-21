// ajax
$( document ).on('click', '#ajax-btn', function(event) {
    console.log('Step 1');
    $.ajax({
                url: '/user/update-token-ajax/',
                success: function (data) {
                    // data - ответ от сервера
                    console.log('Step 3')
                    console.log(data);
                    $('#token').html(data.key);
                },
            });
});