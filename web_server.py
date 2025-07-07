from flask import Flask, render_template, redirect, request, session, url_for, jsonify
from threading import Thread
import os
import requests
from database_setup import SessionLocal, Setting

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24) # Essencial para a sessão de login

# Carrega as variáveis de ambiente para o OAuth do Discord
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
# A URL de callback é dinâmica, baseada no domínio público da Railway
REDIRECT_URI = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', '')}/callback"
API_BASE_URL = 'https://discord.com/api/v10'

# Função para trocar o código de autorização por um token de acesso
def token_exchange(code):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    return r.json()

# Função para salvar ou atualizar uma configuração no banco de dados
def update_setting(db, key, value):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        new_setting = Setting(key=key, value=value)
        db.add(new_setting)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    # Redireciona o usuário para a página de autorização do Discord
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify guilds")

@app.route('/callback')
def callback():
    # O Discord redireciona de volta para cá com um código
    code = request.args.get('code')
    token_info = token_exchange(code)
    session['access_token'] = token_info['access_token']
    return redirect(url_for('dashboard'))


# DENTRO DE web_server.py, SUBSTITUA A FUNÇÃO INTEIRA ABAIXO
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'access_token' not in session:
        return redirect(url_for('login'))

    headers = {'Authorization': f"Bearer {session['access_token']}"}
    user_info_res = requests.get(f"{API_BASE_URL}/users/@me", headers=headers)
    if user_info_res.status_code != 200:
        session.clear()
        return redirect(url_for('login'))
    user_info = user_info_res.json()

    db = SessionLocal()
    try:
        # Se o formulário for enviado (método POST via JavaScript)
        if request.method == 'POST':
            data = request.get_json() # Pega os dados enviados como JSON

            # Itera e salva cada configuração recebida
            for key, value in data.items():
                update_setting(db, key, value)

            db.commit()
            # Responde com uma mensagem de sucesso em formato JSON
            return jsonify(success=True, message="Configurações salvas com sucesso!")

        # Pega todas as configurações atuais do banco de dados para exibir na página
        all_settings = db.query(Setting).all()
        settings_dict = {s.key: s.value for s in all_settings}
    finally:
        db.close()

    return render_template('dashboard.html', user=user_info, settings=settings_dict)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

def run():
  app.run(host='0.0.0.0', port=8080)

def start_web_server():
    server_thread = Thread(target=run)
    server_thread.start()
