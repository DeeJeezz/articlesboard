// $(document).ready(function() {
//     $.ajaxSetup({ cache: false });
//     var get_data = function() {
//         var count = 0;
//         $.get('/accounts/profile/notifyuser', function(data) {
//             // console.log('get data');
//             var notifications = $.parseJSON(data.notifications);
//             if (notifications){
//                 $('#notificationsList').html('');
//             }
//             $.each($.parseJSON(data.notifications), function(index, element) {
//                 if (!element.viewed) {
//                     $('#notificationsList').append('<li><a class="btn btn-info ntf " href="' + element.sender + '"><font color="white">' + element.n_type + '</font></a><div style="display:none" class="row">' + element.content + '</div></li>')
//                     count++;
//                 }
//             });
//         }).done(function() {
//             // console.log('done');
//             if (count > 0){
//                 if ($('.notification').css('display') == 'none'){

//                 }
//                 $('.notification').css('display', 'block');
//                 $('.notification').html(count);
//             }
//             else {
//                 $('.notification').css('display', 'none');
//                 $('#notificationsList').html('<h6 class="dropdown-item" style="cursor: default;">У вас нет новых оповещений</h6>');
//             }
//         }).fail(function() {
//             // console.log('fail');
//         });
//     }
//     get_data();
//     window.setInterval(get_data, 5000);
//     $('#navbarDropdownMenuLink').on('click', function() {
//         $.get('/accounts/profile/setnotificationviewed', function (data) {
//             console.log(data);
//         });
//         $('.notification').css('display', 'none');
//         $('.ntf').addClass('viewed');
//     });
// });

var socket_url = 'ws://' + window.location.host;
var socket = new WebSocket(socket_url);

socket.onopen = function(event) {
    console.log('socket opened', event);
}
socket.onerror = function(error) {
    console.log(error);
}