import requests
import time

# --- SEUS DADOS REAIS ---
TOKEN = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0" 
CHAT_ID = "1027866106"
URL_API = "https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey=9478a34c4d9fb4cc6d18861a304bdf18&regions=eu&markets=h2h&oddsFormat=decimal" 

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown", "disable_web_page_preview": False}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def buscar_jogos():
    try:
        response = requests.get(URL_API)
        data = response.json()
        
        if isinstance(data, list):
            for jogo in data:
                home = jogo.get('home_team', 'N/A')
                away = jogo.get('away_team', 'N/A')
                
                # Simulando extração de stats (Ajuste conforme sua API de stats real)
                stats = jogo.get('stats', {})
                atq_h = stats.get('dangerous_attacks', {}).get('home', 0)
                atq_a = stats.get('dangerous_attacks', {}).get('away', 0)
                chutes_gol = stats.get('on_target', {}).get('home', 0) + stats.get('on_target', {}).get('away', 0)
                chutes_fora = stats.get('off_target', {}).get('home', 0) + stats.get('off_target', {}).get('away', 0)
                tempo = jogo.get('minute', 0)
                p_h = jogo.get('score', {}).get('home', 0)
                p_a = jogo.get('score', {}).get('away', 0)

                # --- LÓGICA GOL HT (REVISADA) ---
                # Requisito: 15-35 min, 0x0, 30+ atq perigosos, 1+ chute (gol ou fora)
                if 15 <= tempo <= 35 and (p_h + p_a == 0):
                    if (atq_h + atq_a) >= 30 and (chutes_gol >= 1 or chutes_fora >= 1):
                        msg = (f"🎯 **SINAL: GOL HT**\n⚽ {home} x {away}\n🔥 Pressão: {atq_h + atq_a} Atq\n"
                               f"🇮🇪 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)")
                        enviar_mensagem(msg)

                # --- LÓGICA CANTOS (REVISADA) ---
                # Requisito: 80+ min, Empate, Dif. de 10 ataques entre times
                dif_ataques = abs(atq_h - atq_a)
                if tempo >= 80 and (p_h == p_a) and dif_ataques >= 10:
                    msg = (f"🚩 **SINAL: ESCANTEIO FINAL**\n⚽ {home} x {away}\n⏰ {tempo}' | Dif. Atq: {dif_ataques}\n"
                           f"🇮🇪 [Bet365 Ao Vivo](https://www.bet365.com/#/IP/)")
                    enviar_mensagem(msg)
        else:
            print("Aguardando dados válidos da API...")

    except Exception as e:
        print(f"Erro na leitura da API: {e}")

print("Robô iniciado no Koyeb...")
while True:
    buscar_jogos()
    time.sleep(300) # 5 minutos para respeitar o limite da The Odds API
