import requests
import urllib.parse
import time

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

historico_cantos = {}
jogos_avisados_cantos = []
jogos_avisados_gols = []

def limpar_valor(valor):
    if valor is None: return 0
    try:
        return int(float(str(valor).replace('%', '').strip()))
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
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown&disable_notification=false"
    try: requests.get(url, timeout=10)
    except: pass

print("🛰️ Robô Híbrido: Gols HT (Odd 1.50+) + Cantos Limite")

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
            
            # --- ESTRATÉGIA GOLS HT (FILTRO ODD 1.50+) ---
            # O filtro de tempo (minuto >= 18) garante que a odd já subiu para perto de 1.50
            if 22 <= minuto <= 35 and g_h == 0 and g_a == 0:
                if m_id not in jogos_avisados_gols:
                    id_h = fixture['teams']['home']['id']
                    id_a = fixture['teams']['away']['id']
                    
                    perc_h = verificar_historico_ht(id_h)
                    perc_a = verificar_historico_ht(id_a)
                    
                    if perc_h >= 80 or perc_a >= 80:
                        msg = (f"⚽ *GOL HT: ODD 1.50+ ATINGIDA*\n\n"
                               f"🏟️ {fixture['teams']['home']['name']} x {fixture['teams']['away']['name']}\n"
                               f"⏱️ Tempo: {minuto}' | 🥅 0x0\n"
                               f"📊 Histórico HT: {max(perc_h, perc_a):.0f}% (Mínimo)\n"
                               f"💰 Entrada sugerida: Over 0.5 HT\n"
                               f"📲 [ABRIR BET365](https://www.bet365.com/#/IP/)")
                        enviar_telegram(msg)
                        jogos_avisados_gols.append(m_id)

      # ========== ESTRATÉGIA CANTOS (SAFE CLOUD) ==========
agora = time.time()

# controla requisição (1 a cada 150s por jogo)
if m_id not in ultimo_fetch_cantos:
    ultimo_fetch_cantos[m_id] = 0

if agora - ultimo_fetch_cantos[m_id] >= 150:
    try:
        stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
        stats_res = requests.get(stats_url, headers=HEADERS, timeout=10).json()

        response_stats = stats_res.get("response", [])
        if not response_stats:
            raise Exception("Stats vazias")

        total_cantos = 0
        for team in response_stats:
            for stat in team.get("statistics", []):
                if stat.get("type") == "Corner Kicks":
                    total_cantos += limpar_valor(stat.get("value"))

        ultimo_fetch_cantos[m_id] = agora

        if m_id not in historico_cantos:
            historico_cantos[m_id] = []

        historico_cantos[m_id].append((minuto, total_cantos))

        # mantém só últimos 7 minutos
        historico_cantos[m_id] = [
            (m, c) for m, c in historico_cantos[m_id]
            if minuto - m <= 7
        ]

        # regra de tempo
        if ((minuto >= 30 and minuto < 45) or minuto >= 75):
            if len(historico_cantos[m_id]) >= 2:
                dif = total_cantos - historico_cantos[m_id][0][1]

                if dif >= 3 and m_id not in jogos_avisados_cantos:
                    msg = (
                        f"🚩 *CANTOS – PRESSÃO*\n\n"
                        f"🏟️ {fixture['teams']['home']['name']} x {fixture['teams']['away']['name']}\n"
                        f"⏱️ {minuto}'\n"
                        f"🚩 +3 cantos nos últimos 7 minutos\n"
                        f"📲 [ABRIR BET365](https://www.bet365.com/#/IP/)"
                    )
                    enviar_telegram(msg)
                    jogos_avisados_cantos.add(m_id)

    except Exception as e:
        print(f"⚠️ Erro cantos jogo {m_id}: {e}")

    except Exception as e: print(f"⚠️ Erro: {e}")
    time.sleep(300)
