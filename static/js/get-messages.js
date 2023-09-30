function getrandomcolor() {
    const randomInt = (min, max) => {
      return Math.floor(Math.random() * (max - min + 1)) + min;
    };
  
    var h = randomInt(0, 360);
    var s = randomInt(42, 98);
    var l = randomInt(40, 90);
    return `hsl(${h},${s}%,${l}%)`;
  }

const usercolors = new Map();
var user_color = usercolors.get(jQuery('.chat-user-nickname').text());
if(!user_color) {
    usercolors.set(jQuery('.chat-user-nickname').text(),getrandomcolor());
    var user_color = usercolors.get(jQuery('.chat-user-nickname').text());
}
jQuery('.chat-user-nickname').css('color', user_color);

function getmessages() {
    var pincode = jQuery('input#pincode').val();
    jQuery.ajax({
        url: '/chat/'+pincode+'/getmessages',
        data: {
            'pincode': pincode
        },
        type: 'POST',
        success: function(result) {
            result_json = JSON.parse(result)
            result_json.forEach(function(element) {
                author_color = usercolors.get(element['author']);
                if(!author_color) {
                    usercolors.set(element['author'],getrandomcolor());
                    author_color = usercolors.get(element['author']);
                }
                let message = '<div class="chat_line" messageid="'+element['id']+'"><span style="color: '+author_color+'">'+element['author']+':</span> <span class="chat_message">'+element['text']+'</span></div>';
                showmessage(message);
            });
            scrollbottom();
        }
    });
}

let permission = Notification.requestPermission();
function sendPushNotification(title, body) {
    Notification.requestPermission().then(perm => {
        if (perm === "granted") {
            const pushnotification = new Notification(title, {
                body: body
            })
        }
    })
}

function getlastmessage() {
    var pincode = jQuery('input#pincode').val();
    jQuery.ajax({
        url: '/chat/'+pincode+'/getlastmessage',
        data: {
            'pincode': pincode
        },
        type: 'POST',
        success: function(result) {
            if(result) {
                result_json = JSON.parse(result)
                if(result_json['message']) {
                    if(result_json['message']['id'] != jQuery('.chat_line').last().attr('messageid')) {
                        author_color = usercolors.get(result_json['message']['author']);
                        if(!author_color) {
                            usercolors.set(result_json['message']['author'],getrandomcolor());
                            author_color = usercolors.get(result_json['message']['author']);
                        }
                        let message = '<div class="chat_line" messageid="'+result_json['message']['id']+'"><span style="color: '+author_color+'">'+result_json['message']['author']+':</span> <span class="chat_message">'+result_json['message']['text']+'</span></div>';
                        
                        showmessage(message);
                        scrollbottom();
                        sendPushNotification(result_json['message']['author'], result_json['message']['text'])
                    }
                }
                
                if(result_json['chat_lifetime'] > 0) {
                    let lifetime_minutes = Math.floor(result_json['chat_lifetime']/60);
                    if(lifetime_minutes < 10) {
                        lifetime_minutes = '0' + lifetime_minutes
                    }
                    let lifetime_seconds = result_json['chat_lifetime']%60;
                    if(lifetime_seconds < 10) {
                        lifetime_seconds = '0' + lifetime_seconds
                    }
                                    
                    jQuery('lifetime').text(lifetime_minutes + ':' + lifetime_seconds);
                }
                else {
                    window.location.reload();
                }
                
            }
        }
    });
}

function showmessage(message) {
    var textarea = jQuery('div#chatmessages');
    textarea.html(textarea.html() + "\n" + message);
}

function scrollbottom() {
    var textarea = jQuery('div#chatmessages');
    var messages = jQuery('div.chat_line');
    var chatheight = 0;
    messages.each(function(i, element) {
        chatheight += jQuery(element).outerHeight();
    });
    textarea.scrollTop(chatheight);
}

window.setInterval(function() {
    getlastmessage();
  }, 1000);

getmessages();