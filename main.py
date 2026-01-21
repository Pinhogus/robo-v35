import requests
import time

# --- SEUS DADOS REAIS CONFIGURADOS ---
TOKEN = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0" 
CHAT_ID = "1027866106"
# URL correta para a sua chave
URL_API = "https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey=9478a34c4d9fb4cc6d18861a304bdf18&regions=eu&markets=h2h&oddsFormat=decimal" 

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": texto, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def buscar_jogos():
    try:
        response = requests.get(URL_API)
        data = response.json()
        
        # A The Odds API retorna uma LISTA direta de jogos
        if isinstance(data, list):
            for jogo in data:
                home = jogo.get('home_team', 'N/A')
                away = jogo.get('away_team', 'N/A')
                liga = jogo.get('sport_title', 'Futebol')

                msg = (
                    f"🚀 **JOGO IDENTIFICADO**\n\n"
                    f"⚽ **{home} vs {away}**\n"
                    f"🏆 {liga}\n\n"
                    f"🇮🇪 **APOSTAR NA IRLANDA:**\n"
                    f"🟢 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)\n"
                    f"🟢 [Bet365 Ao Vivo](https://www.bet365.com/#/IP/)"
                )
                enviar_mensagem(msg)
                # Pausa pequena entre mensagens para não dar erro no Telegram
                time.sleep(2) 
        else:
            print("Formato de dados inesperado")

    except Exception as e:
        print(f"Erro na leitura da API: {e}")

print("Robô iniciado no Koyeb...")
while True:
    buscar_jogos()
    # Espera 10 minutos para não estourar seu limite de créditos da API
    time.sleep(600) 
