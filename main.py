import requests
import time

# Configurações do Telegram
TOKEN = "SEU_TOKEN_AQUI" # Certifique-se de que o token está correto
CHAT_ID = "SEU_CHAT_ID_AQUI"

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown", "disable_web_page_preview": False}
    requests.post(url, json=payload)

def buscar_jogos():
    # Aqui entra a URL da sua API de futebol
    url_api = "SUA_URL_DA_API_AQUI"
    response = requests.get(url_api).json()
    
    for jogo in response['data']:
        # Coleta de dados básicos
        home = jogo['home_name']
        away = jogo['away_name']
        tempo = jogo['minute']
        
        # Coleta de estatísticas (ajuste conforme o padrão da sua API)
        atq_perigosos = jogo['stats']['dangerous_attacks']['home'] + jogo['stats']['dangerous_attacks']['away']
        chutes_no_gol = jogo['stats']['on_target']['home'] + jogo['stats']['on_target']['away']
        chutes_fora = jogo['stats']['off_target']['home'] + jogo['stats']['off_target']['away']
        cantos = jogo['stats']['corners']['home'] + jogo['stats']['corners']['away']
        placar_h = jogo['score']['home']
        placar_a = jogo['score']['away']

        # --- LÓGICA 1: GOLS HT (FILTRO REFINADO) ---
        if 15 <= tempo <= 35 and (placar_h + placar_a == 0):
            if atq_perigosos >= 30 and chutes_no_gol >= 2 and chutes_fora >= 4:
                msg = (
                    f"🎯 **ALERTA: GOL HT (0x0)**\n\n"
                    f"⚽ {home} vs {away}\n"
                    f"🔥 Pressão Alta: {atq_perigosos} Atq. Perigosos\n"
                    f"🚀 Finalizações: {chutes_no_gol} no alvo | {chutes_fora} fora\n"
                    f"🇮🇪 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)\n"
                    f"🟢 [Bet365 Ao Vivo](https://www.bet365.com/#/IP/)"
                )
                enviar_mensagem(msg)

        # --- LÓGICA 2: ESCANTEIOS (ESTRATÉGIA DE MINUTOS FINAIS) ---
        # Exemplo: Mais de 9 cantos e jogo empatado nos minutos finais
        if tempo >= 80 and (placar_h == placar_a):
            msg = (
                f"🚩 **ALERTA: ESCANTEIO FINAL**\n\n"
                f"⚽ {home} vs {away}\n"
                f"⏰ Tempo: {tempo}'\n"
                f"📊 Total Cantos: {cantos}\n"
                f"🇮🇪 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)"
            )
            enviar_mensagem(msg)

# Loop de execução
while True:
    try:
        buscar_jogos()
    except Exception as e:
        print(f"Erro: {e}")
    time.sleep(60) # Verifica a cada 1 minuto
