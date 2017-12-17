$(function() {
    $('.log input[type="submit"]').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Request need to be sent');

        var username = $('.log input[type="text"]')[0].value; // get the entered username check validity
        console.log(username);
        window.location.replace(username);
    });
})