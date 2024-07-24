from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

DATABASE = 'messages.db'

def init_db():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                content TEXT NOT NULL, 
                                category TEXT NOT NULL)''')
            conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    categories = ['praktikum', 'faroid', 'akmal', 'dani']
    return render_template('index.html', categories=categories)

@socketio.on('send_message')
def handle_send_message(json):
    message = json['message']
    category = json['category']
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (content, category) VALUES (?, ?)', (message, category))
        conn.commit()
    emit('receive_message', {'message': message, 'category': category}, broadcast=True)

@app.route('/messages', methods=['GET'])
def get_messages():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT content, category FROM messages')
        messages = cursor.fetchall()
    return jsonify(messages)

@app.route('/responses', methods=['GET'])
def responses():
    return render_template('responses.html')

@app.route('/messages_by_emotions', methods=['GET'])
def messages_by_emotions():
    return render_template('messages_by_emotions.html')

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
