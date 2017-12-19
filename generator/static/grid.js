$(function() {
    function createGrid(height, width) {
        var ratioW = Math.floor($('.grid').width() / width),
            ratioH = Math.floor($('.grid').height() / height);

        var parent = $('div.grid').attr('width', ratioW  * width).attr('height', ratioH  * height);

        for (var i = 0; i < width * height; i++) {
            $('<div />', {
                width: ratioW,
                height: ratioH
            }).appendTo(parent);

            if (Math.floor(i / width) ==  $('#agent').data().i
                && i % width == $('#agent').data().j) {
                    $('<img />', {
                        src: $('#agent').data().link
                    }).addClass('middle').appendTo(parent.children().last());
                }
        }
    }

    // Create the environment for the agent to reside on.
    createGrid(parseInt($('#dimensions').data().height), parseInt($('#dimensions').data().width));

    function move(deltai, deltaj) {
        var username = $('#username').data().username;
        var xhr = new XMLHttpRequest();
        xhr.open("POST", '/'+ username + '/move', true);

        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if(xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
                console.log(xhr.responseText);
            }
        }

        xhr.send('deltai=' + deltai + '&deltaj=' + deltaj);
    }

    function forage() {
        var username = $('#username').data().username;
        var xhr = new XMLHttpRequest();
        xhr.open("POST", '/'+ username + '/forage', true);

        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if(xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
                console.log(xhr.responseText);
            }
        }

        xhr.send();
    }

    function eat() {
        var username = $('#username').data().username;
        var xhr = new XMLHttpRequest();
        xhr.open("POST", '/'+ username + '/eat', true);

        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if(xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
                console.log(xhr.responseText);
            }
        }

        xhr.send();
    }

    $(window).keydown(function(e) {
        // console.log(e);
        var deltai = 0, deltaj = 0;
        switch(e.which) {
            case 37:
            deltai = 0, deltaj = -1;
            break;
            case 38:
            deltai = -1, deltaj = 0;
            break;
            case 39:
            deltai = 0, deltaj = 1;
            break;
            case 40:
            deltai = 1, deltaj = 0;
            break;
        }

        if (deltai !== 0 || deltaj !== 0) {
            // directionnal move has been pressed.
            move(deltai, deltaj);
        }

        switch(e.which) {
            case 69:
            eat();
            break;
            case 70:
            forage();
            break;
        }
    })

    var socket = io.connect('http://localhost:5000');
    socket.on('refresh', function(message) {
        var id = $('#dimensions').data().id;
        if (message.id == id) {
            // trigger a refresh.
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() { 
                if (xhr.readyState == 4 && xhr.status == 200) {
                    $('#environment').empty();
                    $('#environment').html(xhr.responseText);
                    createGrid(parseInt($('#dimensions').data().height), parseInt($('#dimensions').data().width));
                }
            }
            var username = $('#username').data().username;
            xhr.open("GET", '/' + username + '/refresh', true); // true for asynchronous 
            xhr.send(null);

            console.log('refresh has been signaled.');
        } else console.log('refresh was broadcasted.');
    });
})