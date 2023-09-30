function sendmessageajax() {
    var pincode = jQuery('button#send-message-button').attr('pincode');
    var message = jQuery('input#send-message-text').val();
    if(message != '') {
        jQuery.ajax({
            url: '/chat/'+pincode+'/sendmessage',
            data: {
                'message': message
            },
            type: 'POST',
            success: function(result) {
                jQuery('input#send-message-text').val('');
            }
        });
    }
}

jQuery('button#send-message-button').on('click', function() {
    sendmessageajax();
});

jQuery("form#send-message-form").on("submit", function (e) {
    e.preventDefault();
    sendmessageajax();
});