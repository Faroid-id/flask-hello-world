from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# MySQL database configuration
DB_CONFIG = {
    'host': '89.213.211.250',
    'user': 'wargalab_admin',
    'password': 'P4sswordsql',
    'database': 'wargalab_cm'
}

def init_db():
    # Connect to the MySQL server and create the table if it doesn't exist
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INT AUTO_INCREMENT PRIMARY KEY, 
                        content TEXT NOT NULL, 
                        category VARCHAR(255) NOT NULL)''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    categories = ['praktikum', 'faroid', 'akmal', 'dani']
    return render_template('index.html', categories=categories)

@socketio.on('send_message')
def handle_send_message(json):
    message = json['message']
    category = json['category']
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (content, category) VALUES (%s, %s)', (message, category))
    conn.commit()
    cursor.close()
    conn.close()
    
    emit('receive_message', {'message': message, 'category': category}, broadcast=True)

@app.route('/messages', methods=['GET'])
def get_messages():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('SELECT content, category FROM messages')
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    
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
