from flask import Flask, render_template, make_response, request, redirect, url_for
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os, re, sqlite3, hashlib, random, json, time, atexit

# Options
const_chat_lifetime_minutes = 60

# Create App
app = Flask(__name__)

# Scheduler - Delete old chats
def search_delete_old_chats():
    dead_time = datetime.now() - timedelta(minutes = const_chat_lifetime_minutes)
    db_conn = get_db_connection()
    all_chats = db_conn.execute(f'SELECT chat_id FROM messages')
    all_chats = all_chats.fetchall()
    for chat_id in all_chats:
        if len(db_conn.execute(f'SELECT id FROM chats WHERE id = {chat_id[0]}').fetchall()) == 0:
            db_conn.execute(f'DELETE FROM messages WHERE chat_id = {chat_id[0]}')
            db_conn.commit()
    db_conn.execute(f'DELETE FROM chats WHERE created_at < "{dead_time}"')
    db_conn.commit()
    db_conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=search_delete_old_chats, trigger="interval", seconds=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# DB connection
def get_db_connection():
    conn = sqlite3.connect('./db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Get new random pincode
def get_new_pincode():
    db_conn = get_db_connection()
    new_pincode = 0
    while True:
        try_pincode = random.randint(100000,999999)
        new_pincode_check_db_result = db_conn.execute(f'SELECT pincode FROM chats WHERE pincode = {try_pincode}')
        if new_pincode_check_db_result.fetchone() == None:
            new_pincode = try_pincode
            break
    db_conn.close()
    return new_pincode

# Get new random UniqID
def get_uniqid(nickname, pincode, datetime):
    uniqid = hashlib.md5(str(nickname).encode('utf-8') + str(pincode).encode('utf-8') + str(datetime).encode('utf-8'))
    return uniqid.hexdigest()

# ROUTES
@app.route('/chat/', methods=['GET'])
@app.route('/chat/<pincode>', methods=['GET'])
@app.route('/chat/<int:pincode>', methods=['GET'])
def chat(pincode=None):
    nickname = request.cookies.get('nickname')
    if nickname != None:
        if pincode != None and isinstance(pincode, int):
            db_conn = get_db_connection()
            chat = db_conn.execute(f'SELECT id, created_at FROM chats WHERE pincode = {pincode} LIMIT 1')
            chat = chat.fetchone()
            db_conn.close()

            if chat != None:
                return render_template('chat.html', pincode=pincode, nickname=nickname, createdat=chat['created_at'])
            else:
                return render_template('pinornew.html', nickname=nickname, alert='No chats with that pincode or chat lifetime is expired')
        else:
            return render_template('pinornew.html', nickname=nickname, alert='Wrong chat pincode format')
    else:
        if pincode != None and isinstance(pincode, int):
            resp = make_response(redirect(url_for('main')))
            resp.set_cookie('pincode', str(pincode))
            return resp
        else:
            return redirect(url_for('main'))
    
@app.route('/chat/<int:pincode>/sendmessage', methods=['POST'])
def send_message(pincode = None):
    message = request.form.get('message')
    nickname = request.cookies.get('nickname')
    db_conn = get_db_connection()
    chat = db_conn.execute(f'SELECT id FROM chats WHERE pincode = {pincode} LIMIT 1')
    chat_id = chat.fetchone()[0]
    if isinstance(chat_id, int):
        db_conn.execute(f'INSERT INTO messages (chat_id, author, text) VALUES ({chat_id}, "{nickname}", "{message}")')
        db_conn.commit()
    db_conn.close()
    return 'success'

@app.route('/chat/<int:pincode>/getmessages', methods=['POST'])
def get_messages(pincode = None):
    db_conn = get_db_connection()
    chat = db_conn.execute(f'SELECT id FROM chats WHERE pincode = {pincode} LIMIT 1')
    chat_id = chat.fetchone()[0]
    messages = ''
    if isinstance(chat_id, int):
        messages = db_conn.execute(f'SELECT id, author, text FROM messages WHERE chat_id = {chat_id}')
        messages = messages.fetchall()
        result_list = []
        if messages:
            for message in messages:
                message_dict = {
                    'id' : message[0],
                    'author' : message[1],
                    'text' : message[2]
                }
                result_list.append(message_dict)
        result_json = json.dumps(result_list)
    db_conn.close()
    return result_json

@app.route('/chat/<int:pincode>/getlastmessage', methods=['POST'])
def get_last_message(pincode = None):
    db_conn = get_db_connection()
    chat = db_conn.execute(f'SELECT id, created_at FROM chats WHERE pincode = {pincode} LIMIT 1')
    chat = chat.fetchone()
    
    if chat:
        chat_id = chat[0]
        chat_createdat = chat[1]
        chat_lifetime = datetime.now() - datetime.strptime(chat_createdat, '%Y-%m-%d %H:%M:%S.%f')
        
        if isinstance(chat_id, int):
            message = db_conn.execute(f'SELECT id, author, text FROM messages WHERE chat_id = {chat_id} ORDER BY id DESC LIMIT 1')
            message = message.fetchone()
            if message:
                message_dict = {
                    'message': {
                        'id' : message[0],
                        'author' : message[1],
                        'text' : message[2]
                    },
                    'chat_lifetime': str((const_chat_lifetime_minutes*60) - chat_lifetime.seconds)                 
                }
            else:
                message_dict = {
                    'chat_lifetime': str((const_chat_lifetime_minutes*60) - chat_lifetime.seconds)
                }
    else:
        message_dict = {}
    result_json = json.dumps(message_dict)
    db_conn.close()
    return result_json

@app.route('/', methods=['GET', 'POST'])
@app.route('/<path:action>')
def main(action=None):

    # URL = /change-nickname :: Change nickname
    if action == 'change-nickname':
        resp = make_response(redirect(url_for('main')))
        resp.set_cookie('nickname', '', expires=0)
        return resp
    
    # URL = /create-chat :: Create chat
    if action == 'create-chat':
        nickname = request.cookies.get('nickname')
        if len(nickname) != 0:
                regex = r'^[а-яА-Яa-zA-Z0-9]+$'
                if re.match(regex, nickname):
                    new_pincode = get_new_pincode()

                    new_created_at = datetime.now()
                    new_uniqid = get_uniqid(nickname, new_pincode, new_created_at)

                    db_conn = get_db_connection()
                    db_conn.execute(f'INSERT INTO chats (nickname, pincode, uniqid, created_at) VALUES ("{nickname}", {new_pincode}, "{new_uniqid}", "{new_created_at}")')
                    db_conn.commit()
                    db_conn.close()

                    return redirect(url_for('chat', pincode=new_pincode))
                else:
                    return redirect(url_for('main'))

    # URL = '/'
    if action == None:
        if request.method == 'POST':

            # Set nickname
            nickname = request.form.get('nickname')

            if nickname != None and len(nickname) != 0:
                regex = r'^[а-яА-Яa-zA-Z0-9]+$'
                if re.match(regex, nickname):
                    resp = make_response(redirect(url_for('main')))
                    resp.set_cookie('nickname', nickname)
                    return resp
                else:
                    return render_template('nickname.html', alert='Nickname must contain letter and digits only!')
            else:
                return render_template('nickname.html', alert='Nickname field is empty!')

        else:
            nickname = request.cookies.get('nickname')
            if nickname == None:
                return render_template('nickname.html')
            else:
                pincode = request.cookies.get('pincode')
                if pincode == None:
                    pincode = ''
                return render_template('pinornew.html', nickname=nickname, pincode=pincode)