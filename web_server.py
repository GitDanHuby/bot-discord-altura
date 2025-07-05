from flask import Flask, render_template
from threading import Thread
from samp_client.client import SampClient

app = Flask(__name__, template_folder='templates')

# --- Configurações do Servidor SAMP ---
IP_DO_SERVIDOR = "179.127.16.157"
PORTA_DO_SERVIDOR = 29015

@app.route('/')
def status_page():
    try:
        with SampClient(address=IP_DO_SERVIDOR, port=PORTA_DO_SERVIDOR, timeout=2) as samp_client:
            info = samp_client.get_server_info()
            ping_ms = samp_client.ping()

            # Prepara os dados para o site
            context = {
                "status": "Online",
                "hostname": info.hostname,
                "players": info.players,
                "max_players": info.max_players,
                "ping": ping_ms,
                "ip": IP_DO_SERVIDOR,
                "port": PORTA_DO_SERVIDOR
            }
    except Exception as e:
        print(f"WEB: Erro ao checar status do servidor: {e}")
        context = {"status": "Offline"}

    # Renderiza a página HTML com os dados
    return render_template('index.html', **context)

def run():
  app.run(host='0.0.0.0', port=8080)

def start_web_server():
    server_thread = Thread(target=run)
    server_thread.start()