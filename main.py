import requests
import time

# --- CONFIGURAÇÕES ---
TOKEN = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0"
CHAT_ID = "1027866106"
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18" # Sua chave da API-Football
HEADERS = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def buscar_pressao_cantos():
    try:
        # Busca jogos ao vivo
        url = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url, headers=HEADERS).json()
        
        for jogo in response.get('response', []):
            fixture_id = jogo['fixture']['id']
            tempo = jogo['fixture']['status']['elapsed']
            home = jogo['teams']['home']['name']
            away = jogo['teams']['away']['name']
            gols_h = jogo['goals']['home']
            gols_a = jogo['goals']['away']

            # Busca estatísticas detalhadas do jogo
            url_stats = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
            stats_data = requests.get(url_stats, headers=HEADERS).json()
            
            if not stats_data.get('response'): continue

            # Extração de Cantos
            stats_h = stats_data['response'][0]['statistics']
            stats_a = stats_data['response'][1]['statistics']
            cantos_h = next((s['value'] for s in stats_h if s['type'] == 'Corner Kicks'), 0) or 0
            cantos_a = next((s['value'] for s in stats_a if s['type'] == 'Corner Kicks'), 0) or 0

            disparar = False
            motivo = ""

            # LÓGICA 1: Perdendo com 5+ cantos até os 40min (1º Tempo)
            if tempo <= 40:
                if gols_h < gols_a and cantos_h >= 5:
                    disparar, motivo = True, f"🔥 {home} perdendo com {cantos_h} cantos!"
                elif gols_a < gols_h and cantos_a >= 5:
                    disparar, motivo = True, f"🔥 {away} perdendo com {cantos_a} cantos!"

            # LÓGICA 2: Perdendo com 10+ cantos até os 85min (2º Tempo)
            elif 45 < tempo <= 85:
                if gols_h < gols_a and cantos_h >= 10:
                    disparar, motivo = True, f"🚀 {home} perdendo com {cantos_h} cantos!"
                elif gols_a < gols_h and cantos_a >= 10:
                    disparar, motivo = True, f"🚀 {away} perdendo com {cantos_a} cantos!"

            if disparar:
                msg = (f"🚩 **SINAL DE CANTOS**\n\n"
                       f"⚽ {home} {gols_h} x {gols_a} {away}\n"
                       f"⏰ Tempo: {tempo}'\n"
                       f"📊 {motivo}\n\n"
                       f"🇮🇪 [Paddy Power Ao Vivo](https://www.paddypower.com/in-play/football)")
                enviar_telegram(msg)
                
    except Exception as e:
        print(f"Erro: {e}")

print("Robô de Cantos (API-Football) Iniciado...")
while True:
    buscar_pressao_cantos()
    time.sleep(180) # Verifica a cada 2 minutos
