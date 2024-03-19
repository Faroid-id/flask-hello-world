from flask import Flask, render_template, request, redirect, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import json

app = Flask(__name__)


# dummy login
# Data pengguna sementara (bisa diganti dengan database)
users = {'user@email.com': 'password1', 'user2': 'password2'}

# Variabel global untuk menyimpan informasi pengguna yang telah login
logged_in_users = {}

@app.before_request
def check_logged_in():
    # Mendapatkan nama pengguna dari session
    username = request.cookies.get('username')

    # Halaman login dan static files tidak memerlukan pengecekan login
    if request.endpoint in ['login', 'static'] or username:
        return None

    # Jika pengguna tidak login dan bukan di halaman login, arahkan ke halaman login
    return redirect(url_for('login'))

# Nama file untuk menyimpan token akses
TOKEN_FILENAME = 'token.json'

FOLDER_ID = '1RxNuk2KXOGTleBP-93bQKue0DND-6NnE'

# Fungsi untuk mendapatkan kredensial
def get_credentials():
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    creds = None

    # Mencoba membaca token akses dari file
    if os.path.exists(TOKEN_FILENAME):
        with open(TOKEN_FILENAME, 'r') as token_file:
            token_data = json.load(token_file)
        creds = Credentials.from_authorized_user_info(token_data)

    # Jika tidak ada token atau token sudah tidak valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Menyimpan token akses ke file
        with open(TOKEN_FILENAME, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds

# Fungsi untuk mencari file di Google Drive berdasarkan nama
def search_files(drive_service, query):
    results = drive_service.files().list(q=f"name contains '{query}'").execute()
    files = results.get('files', [])

    return files

# Fungsi untuk mengunduh file PDF dari Google Drive
def download_file(drive_service, file_id, destination):
    request = drive_service.files().get_media(fileId=file_id)
    fh = open(destination, 'wb')
    downloader = request.execute()
    fh.write(downloader)
    fh.close()

# Route untuk menampilkan halaman pencarian
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cari')
def cari():
    return render_template('cari.html')

# Route untuk menangani pencarian dan menampilkan file PDF
@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    # Mendapatkan kredensial
    credentials = get_credentials()

    # Membuat objek service Google Drive
    drive_service = build('drive', 'v3', credentials=credentials)

    # Mencari file berdasarkan nama
    found_files = search_files(drive_service, query)
    tuples_data = [(item['name'], item['id']) for item in found_files]


    if found_files and len(found_files) >= 1:
        # Jika lebih dari satu file ditemukan, tampilkan daftar hasil
        return render_template('hasil.html', files=tuples_data)
    else:
        return render_template('result.html', error='File not found.')

# Route untuk menampilkan file PDF berdasarkan ID
@app.route('/view/<file_id>')
def view_file(file_id):
    # Mendapatkan kredensial
    credentials = get_credentials()

    # Membuat objek service Google Drive
    drive_service = build('drive', 'v3', credentials=credentials)

    # Mendapatkan file berdasarkan ID
    file_info = drive_service.files().get(fileId=file_id).execute()

    pdf_url = f"https://drive.google.com/file/d/{file_info['id']}/preview"

    return render_template('result.html', pdf_path=pdf_url)

@app.route('/folder')
def folder():
    # Memuat kredensial
    creds = get_credentials()
    # Membangun objek Drive API
    service = build('drive', 'v3', credentials=creds)
    # Mengambil daftar file dalam folder
    if request.args.get('id')!=None:
        FOLDER_ID=request.args.get('id')
    else:
        FOLDER_ID='1RxNuk2KXOGTleBP-93bQKue0DND-6NnE'
    results = service.files().list(q=f"'{FOLDER_ID}' in parents",
                                    fields="nextPageToken, files(id, name, mimeType, shortcutDetails)").execute()
    items = results.get('files', [])
    files = []
    if items:
        for item in items:
            # Menambahkan tuple (nama file, id file, tipe mime, tipe item) ke dalam list files
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                files.append((item['name'], item['id'], item['mimeType'], 'folder'))
            elif item['mimeType'] == 'application/vnd.google-apps.shortcut':
                shortcut_details = item.get('shortcutDetails', {})
                target_id = shortcut_details.get('targetId', '')
                target_type = shortcut_details.get('targetMimeType', '')
                files.append((item['name'], target_id, target_type, 'shortcut'))
            else:
                files.append((item['name'], item['id'], item['mimeType'], 'file'))
    return render_template('folder.html', files=files)





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            # Menyimpan nama pengguna ke dalam cookie sebagai tanda bahwa pengguna telah login
            response = redirect(url_for('index'))
            response.set_cookie('username', username)
            return response
        else:
            return render_template('login.html', error='Invalid username or password.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Hapus cookie yang menyimpan informasi login pengguna
    response = redirect(url_for('login'))
    response.delete_cookie('username')
    return response

@app.route('/addressbar')
def address():
    return render_template('addressbar.html')


#if __name__ == '__main__':
#    app.run(debug=True)
if __name__ == '__main__':
    app.run(host= '0.0.0.0', port=5000, debug=True)
