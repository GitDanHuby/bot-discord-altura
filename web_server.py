from flask import Flask, render_template, redirect, request, session, url_for
from threading import Thread
import os
import requests

app = Flask(__name__, template_folder='templates')
# Uma chave secreta é necessária para manter a "sessão" do usuário segura.
app.secret_key = os.urandom(24)

# Pega as credenciais das variáveis de ambiente
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
# A URL para onde o Discord vai redirecionar o usuário
# Certifique-se que esta é a mesma URL que você configurou no Portal de Desenvolvedores!
REDIRECT_URI = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/callback"
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

# Rota principal (página inicial)
@app.route('/')
def home():
    # Passa o CLIENT_ID para o template poder montar o link de login
    return render_template('index.html', client_id=CLIENT_ID, redirect_uri=REDIRECT_URI)

# Rota de login
@app.route('/login')
def login():
    # Redireciona o usuário para a página de autorização do Discord
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify guilds")

# Rota de callback (para onde o Discord manda o usuário de volta)
@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = token_exchange(code)
    session['access_token'] = token_info['access_token']
    return redirect(url_for('dashboard'))

# Rota do dashboard (protegida)
@app.route('/dashboard')
def dashboard():
    if 'access_token' not in session:
        return redirect(url_for('login')) # Se não estiver logado, manda para a página de login

    # Pega as informações do usuário usando o token
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    user_info_res = requests.get(f"{API_BASE_URL}/users/@me", headers=headers)
    user_info_res.raise_for_status()
    user_info = user_info_res.json()

    # Renderiza a página do dashboard com as informações do usuário
    return render_template('dashboard.html', user=user_info)

# Rota de logout
@app.route('/logout')
def logout():
    session.clear() # Limpa a sessão
    return redirect(url_for('home'))

# Função para iniciar o servidor web
def run():
  app.run(host='0.0.0.0', port=8080)

def start_web_server():
    server_thread = Thread(target=run)
    server_thread.start()
