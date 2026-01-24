import requests
import time

# --- CONFIGURAÇÕES ---
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

def buscar_oportunidades():
    try:
        response = requests.get(URL_API)
        data = response.json()
        
        if isinstance(data, list):
            for jogo in data:
                home = jogo.get('home_team', 'N/A')
                away = jogo.get('away_team', 'N/A')
                
                # Dados Live (Essenciais para o filtro funcionar)
                stats = jogo.get('stats', {})
                tempo = jogo.get('minute', 0)
                p_h = jogo.get('score', {}).get('home', 0)
                p_a = jogo.get('score', {}).get('away', 0)
                
                # --- 1. LÓGICA GOLS HT (22 MIN + 70% AMBOS) ---
                # Requisito: A partir de 22min, 0x0, e histórico de 70% para os DOIS times
                prob_h = jogo.get('home_stats', {}).get('ht_goal_prob', 0)
                prob_a = jogo.get('away_stats', {}).get('ht_goal_prob', 0)

                if 22 <= tempo <= 38 and (p_h + p_a == 0):
                    if prob_h >= 70 and prob_a >= 70:
                        msg = (f"🎯 **GOL HT (ESTRATÉGIA 70% DUPLO)**\n⚽ {home} x {away}\n"
                               f"⏱ Minuto: {tempo}'\n"
                               f"📊 Prob HT: {home} {prob_h}% | {away} {prob_a}%\n"
                               f"🇮🇪 [Paddy Power](https://www.paddypower.com/in-play/football)")
                        enviar_mensagem(msg)

                # --- 2. LÓGICA ESCANTEIOS (DIFERENÇA DE 10 ATAQUES) ---
                atq_h = stats.get('dangerous_attacks', {}).get('home', 0)
                atq_a = stats.get('dangerous_attacks', {}).get('away', 0)
                dif_ataques = abs(atq_h - atq_a)

                if tempo >= 80 and (p_h == p_a) and dif_ataques >= 10:
                    msg = (f"🚩 **ESCANTEIO FINAL**\n⚽ {home} x {away}\n"
                           f"⏰ {tempo}' | Dif. Ataques: {dif_ataques}\n"
                           f"🇮🇪 [Bet365](https://www.bet365.com/#/IP/)")
                    enviar_mensagem(msg)

                # --- 3. FAVORITO PERDENDO (ODD < 1.80) ---
                # Pega odds da primeira bookmaker disponível
                bookmakers = jogo.get('bookmakers', [])
                if bookmakers:
                    outcomes = bookmakers[0].get('markets', [])[0].get('outcomes', [])
                    odd_h = next((o['price'] for o in outcomes if o['name'] == home), 10)
                    odd_a = next((o['price'] for o in outcomes if o['name'] == away), 10)

                    if (odd_h <= 1.80 and p_a > p_h) or (odd_a <= 1.80 and p_h > p_a):
                        msg = (f"🚨 **FAVORITO PERDENDO**\n⚽ {home} x {away}\n"
                               f"📈 Odd Inicial: {min(odd_h, odd_a)}\n"
                               f"🏆 Placar: {p_h}x{p_a}\n"
                               f"🇮🇪 [Betfair](https://www.betfair.com/sport/inplay)")
                        enviar_mensagem(msg)
        else:
            print("Monitorando jogos e buscando padrões...")

    except Exception as e:
        print(f"Erro na leitura: {e}")

print("Robô Multi-Estratégia Avançado Iniciado!")
while True:
    buscar_oportunidades()
    time.sleep(60) 
