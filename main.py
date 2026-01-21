import requests
import time

# --- SEUS DADOS REAIS CONFIGURADOS ---
TOKEN = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0" 
CHAT_ID = "1027866106"
# URL montada com a sua chave da API
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
        print(f"Erro ao enviar Telegram: {e}")

def buscar_jogos():
    try:
        response = requests.get(URL_API).json()
        # Nota: O formato da resposta pode variar dependendo do plano da sua API
        for jogo in response:
            home = jogo.get('home_team')
            away = jogo.get('away_team')
            
            # Como essa API foca em ODDS, para estatísticas em tempo real (ataques/chutes)
            # você precisa garantir que seu plano contratado fornece dados 'live'
            # Aqui aplicamos a lógica de links para a Irlanda que você pediu
            
            msg = (
                f"🚀 **JOGO IDENTIFICADO**\n\n"
                f"⚽ **{home} vs {away}**\n\n"
                f"🇮🇪 **APOSTAR NA IRLANDA:**\n"
                f"🟢 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)\n"
                f"🟢 [Bet365 Ao Vivo](https://www.bet365.com/#/IP/)\n"
                f"🟢 [Betfair Ao Vivo](https://www.betfair.com/sport/inplay)"
            )
            # Exemplo de envio (ajuste os filtros conforme os dados da sua API)
            enviar_mensagem(msg)
            break # Remova o break para processar todos os jogos

    except Exception as e:
        print(f"Erro na leitura da API: {e}")

print("Robô iniciado no Koyeb...")
while True:
    buscar_jogos()
    time.sleep(300) # Verifica a cada 5 minutos para economizar requisições da sua API
