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
                
                # Dados Live (Ajuste conforme o que sua API entrega no campo stats)
                stats = jogo.get('stats', {})
                tempo = jogo.get('minute', 0)
                p_h = jogo.get('score', {}).get('home', 0)
                p_a = jogo.get('score', {}).get('away', 0)
                
                atq_h = stats.get('dangerous_attacks', {}).get('home', 0)
                atq_a = stats.get('dangerous_attacks', {}).get('away', 0)
                chutes_total = (stats.get('on_target', {}).get('home', 0) + stats.get('on_target', {}).get('away', 0) +
                                stats.get('off_target', {}).get('home', 0) + stats.get('off_target', {}).get('away', 0))

                # Probabilidades HT (Histórico de 70% para AMBOS)
                # Nota: Verifique se sua API envia 'ht_prob' ou similar
                prob_h = jogo.get('home_stats', {}).get('ht_goal_prob', 0)
                prob_a = jogo.get('away_stats', {}).get('ht_goal_prob', 0)

                # --- 1. LÓGICA GOLS HT (REVISADA) ---
                # Requisitos: 22min+ | 0x0 | 2+ Finalizações | 70% HT em AMBOS
                if 22 <= tempo <= 38 and (p_h + p_a == 0):
                    if chutes_total >= 2 and prob_h >= 70 and prob_a >= 70:
                        msg = (f"🎯 **GOL HT (MUITO ALTA PROB)**\n⚽ {home} x {away}\n"
                               f"⏱ {tempo}' | 🚀 Chutes: {chutes_total}\n"
                               f"📊 Prob HT: {home} {prob_h}% | {away} {prob_a}%\n"
                               f"🇮🇪 [Paddy Power](https://www.paddypower.com/in-play/football)")
                        enviar_mensagem(msg)

                # --- 2. LÓGICA ESCANTEIOS (COMO ESTAVA) ---
                # Requisitos: 80min+ | Empate | Diferença de 10 ataques perigosos
                dif_ataques = abs(atq_h - atq_a)
                if tempo >= 80 and (p_h == p_a) and dif_ataques >= 10:
                    msg = (f"🚩 **ESCANTEIO FINAL**\n⚽ {home} x {away}\n"
                           f"⏰ {tempo}' | Dif. Ataques: {dif_ataques}\n"
                           f"🇮🇪 [Bet365](https://www.bet365.com/#/IP/)")
                    enviar_mensagem(msg)

        else:
            print("Monitorando jogos e aguardando filtros...")

    except Exception as e:
        print(f"Erro na leitura: {e}")

print("Robô Multi-Estratégia Iniciado no Koyeb...")
while True:
    buscar_oportunidades()
    time.sleep(300) # 5 minutos para respeitar a cota da API
