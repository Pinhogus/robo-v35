import requests
import time

# --- COLOQUE SEUS DADOS AQUI ---
TOKEN = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0" 
CHAT_ID = "CHAT_ID = "1027866106"
URL_API = "https://v3.football.api-sports.io/fixtures?team={team_id}&last=10" 

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
        # O caminho 'data' depende da sua API, ajuste se necessário
        jogos = response.get('data', [])
        
        for jogo in jogos:
            home = jogo.get('home_name')
            away = jogo.get('away_name')
            tempo = jogo.get('minute')
            
            # Coleta de Estatísticas
            stats = jogo.get('stats', {})
            atq_p_h = stats.get('dangerous_attacks', {}).get('home', 0)
            atq_p_a = stats.get('dangerous_attacks', {}).get('away', 0)
            atq_perigosos = atq_p_h + atq_p_a
            
            chutes_h = stats.get('on_target', {}).get('home', 0)
            chutes_a = stats.get('on_target', {}).get('away', 0)
            chutes_no_gol = chutes_h + chutes_a

            fora_h = stats.get('off_target', {}).get('home', 0)
            fora_a = stats.get('off_target', {}).get('away', 0)
            chutes_fora = fora_h + fora_a
            
            cantos_h = stats.get('corners', {}).get('home', 0)
            cantos_a = stats.get('corners', {}).get('away', 0)
            total_cantos = cantos_h + cantos_a

            placar_h = jogo.get('score', {}).get('home', 0)
            placar_a = jogo.get('score', {}).get('away', 0)

            # --- LÓGICA 1: GOLS HT (FILTRO DE 30 ATAQUES) ---
            if 15 <= tempo <= 35 and (placar_h + placar_a == 0):
                if atq_perigosos >= 30 and chutes_no_gol >= 2 and chutes_fora >= 4:
                    msg = (
                        f"🎯 **ALERTA: GOL HT (0x0)**\n\n"
                        f"⚽ **{home} vs {away}**\n"
                        f"🔥 Pressão: {atq_perigosos} Atq. Perigosos\n"
                        f"🚀 Chutes: {chutes_no_gol} no alvo | {chutes_fora} fora\n\n"
                        f"🇮🇪 **APOSTAR NA IRLANDA:**\n"
                        f"🟢 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)\n"
                        f"🟢 [Bet365 Ao Vivo](https://www.bet365.com/#/IP/)"
                    )
                    enviar_mensagem(msg)

            # --- LÓGICA 2: ESCANTEIOS (ESTRATÉGIA FINAL) ---
            if tempo >= 80 and (placar_h == placar_a):
                msg = (
                    f"🚩 **ALERTA: ESCANTEIO FINAL**\n\n"
                    f"⚽ **{home} vs {away}**\n"
                    f"⏰ Tempo: {tempo}' | Cantos: {total_cantos}\n\n"
                    f"🇮🇪 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)\n"
                    f"🟢 [Bet Betfair](https://www.betfair.com/sport/inplay)"
                )
                enviar_mensagem(msg)

    except Exception as e:
        print(f"Erro na leitura da API: {e}")

# Loop principal
print("Robô iniciado no Koyeb...")
while True:
    buscar_jogos()
    time.sleep(60)
