import requests
import urllib.parse
import time

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

jogos_avisados_cantos = []
jogos_avisados_gols = []

def limpar_valor(valor):
    if valor is None: return 0
    try: return int(float(str(valor).replace('%', '').strip()))
    except: return 0

def verificar_historico_ht(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = res.get('response', [])
        if not jogos: return 0
        gols_ht = 0
        for j in jogos:
            h_ht = j.get('score', {}).get('halftime', {}).get('home') or 0
            a_ht = j.get('score', {}).get('halftime', {}).get('away') or 0
            if (h_ht + a_ht) > 0: gols_ht += 1
        return (gols_ht / len(jogos)) * 100
    except: return 0

def enviar_telegram(mensagem):
    texto = urllib.parse.quote(mensagem)
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    try: requests.get(url, timeout=10)
    except: pass

print("🛰️ Robô Híbrido: Gols HT + Cantos Pressão (Perdedor)")

while True:
    try:
        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        
        print(f"📊 Varredura: {len(jogos)} jogos | {time.strftime('%H:%M:%S')}")

        for fixture in jogos:
            m_id = fixture['fixture']['id']
            minuto = fixture.get('fixture', {}).get('status', {}).get('elapsed') or 0
            g_h = fixture.get('goals', {}).get('home') or 0
            g_a = fixture.get('goals', {}).get('away') or 0
            home_n = fixture['teams']['home']['name']
            away_n = fixture['teams']['away']['name']
            
            # --- 1. ESTRATÉGIA GOLS HT ---
            if 20 <= minuto <= 26 and g_h == 0 and g_a == 0:
                if m_id not in jogos_avisados_gols:
                    perc_h = verificar_historico_ht(fixture['teams']['home']['id'])
                    perc_a = verificar_historico_ht(fixture['teams']['away']['id'])
                    
                    if perc_h >= 80 or perc_a >= 80:
                        msg = (f"⚽ *GOL HT: ODD ALTA*\n\n🏟️ {home_n} x {away_n}\n"
                               f"⏱️ {minuto}' | 🥅 0x0\n📊 Histórico: {max(perc_h, perc_a):.0f}%\n"
                               f"📲 [BET365](https://www.bet365.com/#/IP/)")
                        enviar_telegram(msg)
                        jogos_avisados_gols.append(m_id)

            # --- 2. ESTRATÉGIA CANTOS (EQUIPE PERDENDO) ---
            if m_id not in jogos_avisados_cantos:
                # Só busca estatísticas se o critério de tempo e placar for atingido
                if (minuto <= 37 and (g_h != g_a)) or (45 < minuto <= 83 and (g_h != g_a)):
                    try:
                        stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                        stats_res = requests.get(stats_url, headers=HEADERS, timeout=10).json()
                        st_resp = stats_res.get("response", [])
                        
                        if len(st_resp) >= 2:
                            c_h = next((s['value'] for s in st_resp[0]['statistics'] if s['type'] == 'Corner Kicks'), 0) or 0
                            c_a = next((s['value'] for s in st_resp[1]['statistics'] if s['type'] == 'Corner Kicks'), 0) or 0
                            
                            alerta = False
                            # Lógica 1º Tempo (5+ cantos)
                            if minuto <= 40:
                                if (g_h < g_a and c_h >= 5) or (g_a < g_h and c_a >= 5): alerta = True
                            # Lógica 2º Tempo (10+ cantos)
                            elif 45 < minuto <= 85:
                                if (g_h < g_a and c_h >= 10) or (g_a < g_h and c_a >= 10): alerta = True
                            
                            if alerta:
                                msg = (f"🚩 *CANTOS: PRESSÃO DO PERDEDOR*\n\n"
                                       f"🏟️ {home_n} {g_h}x{g_a} {away_n}\n"
                                       f"⏱️ {minuto}' | 🚩 Cantos: {c_h}x{c_a}\n"
                                       f"🚨 Equipe perdendo está pressionando!\n"
                                       f"📲 [BET365](https://www.bet365.com/#/IP/)")
                                enviar_telegram(msg)
                                jogos_avisados_cantos.append(m_id)
                    except: pass

    except Exception as e: print(f"⚠️ Erro Geral: {e}")
    time.sleep(480) # Evita bloqueio de IP/Excesso de chamadas
