from flask import Flask, render_template, redirect, request, session, url_for
from threading import Thread
import os
import requests
# Importa as ferramentas do nosso novo arquivo de banco de dados
from database_setup import SessionLocal, Setting

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
# A variável RAILWAY_PUBLIC_DOMAIN é fornecida automaticamente pela Railway
REDIRECT_URI = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', '')}/callback"
API_BASE_URL = 'https://discord.com/api/v10'

def token_exchange(code):
    data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    return r.json()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify guilds")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = token_exchange(code)
    session['access_token'] = token_info['access_token']
    return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'access_token' not in session:
        return redirect(url_for('login'))

    headers = {'Authorization': f"Bearer {session['access_token']}"}
    user_info_res = requests.get(f"{API_BASE_URL}/users/@me", headers=headers)
    user_info_res.raise_for_status()
    user_info = user_info_res.json()

    db = SessionLocal()
    try:
        # Se o formulário for enviado (método POST)
        if request.method == 'POST':
            new_message = request.form['welcome_message']
            setting = db.query(Setting).filter(Setting.key == 'welcome_message').first()
            if setting:
                setting.value = new_message
            else:
                setting = Setting(key='welcome_message', value=new_message)
                db.add(setting)
            db.commit()

        # Pega a mensagem atual do banco de dados para exibir
        current_setting = db.query(Setting).filter(Setting.key == 'welcome_message').first()
        current_message = current_setting.value if current_setting else "Mensagem padrão de boas-vindas!"

    finally:
        db.close()

    return render_template('dashboard.html', user=user_info, current_welcome_message=current_message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

def run():
  app.run(host='0.0.0.0', port=8080)

def start_web_server():
    server_thread = Thread(target=run)
    server_thread.start()
