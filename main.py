import requests
import urllib.parse
import time

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

# Controle de histórico e alertas
historico_cantos = {} 
jogos_avisados_cantos = []
jogos_avisados_gols = []

def limpar_valor(valor):
    if valor is None: return 0
    try:
        return int(float(str(valor).replace('%', '').strip()))
    except: return 0

def verificar_historico_ht(team_id):
    """Filtro Pré-Jogo: 70% de gols no HT nos últimos 10 jogos."""
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
    # Som ativo para vibrar no Apple Watch
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown&disable_notification=false"
    try: requests.get(url, timeout=10)
    except: pass

print("✅ Robô Refinado: Gols HT (Apenas 0x0) & Pressão Cantos")

while True:
    try:
        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        
        for fixture in jogos:
            m_id = fixture['fixture']['id']
            minuto = fixture.get('fixture', {}).get('status', {}).get('elapsed') or 0
            g_h = fixture.get('goals', {}).get('home') or 0
            g_a = fixture.get('goals', {}).get('away') or 0
            
            # --- 1. ESTRATÉGIA GOLS HT (REFINADA: APENAS 0x0) ---
            # Filtra: Somente se o jogo estiver 0x0 e entre 18' e 35'
            if 18 <= minuto <= 35 and g_h == 0 and g_a == 0:
                if m_id not in jogos_avisados_gols:
                    perc_h = verificar_historico_ht(fixture['teams']['home']['id'])
                    perc_a = verificar_historico_ht(fixture['teams']['away']['id'])
                    
                    if perc_h >= 70 or perc_a >= 70:
                        msg = (f"⚽ *GOL HT: OPORTUNIDADE (0x0)*\n\n"
                               f"🏟️ {fixture['teams']['home']['name']} x {fixture['teams']['away']['name']}\n"
                               f"⏱️ Tempo: {minuto}' | 🥅 Placar: 0-0\n"
                               f"📊 Histórico HT: {max(perc_h, perc_a):.0f}%\n"
                               f"📈 Odd estimada: 1.50+\n\n"
                               f"📲 [ABRIR NA BET365](https://www.bet365.com/#/IP/)")
                        enviar_telegram(msg)
                        jogos_avisados_gols.append(m_id)

            # --- 2. ESTRATÉGIA CANTOS (2 CANTOS EM 10 MINUTOS) ---
            if (30 <= minuto <= 45) or (75 <= minuto <= 90):
                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                stats_res = requests.get(stats_url, headers=HEADERS, timeout=15).json()
                
                cantos_atual = 0
                for team_data in stats_res.get('response', []):
                    for s in team_data.get('statistics', []):
                        if s['type'] == 'Corner Kicks':
                            cantos_atual += limpar_valor(s.get('value'))
                
                if m_id in historico_cantos:
                    info_ant = historico_cantos[m_id]
                    dif_c = cantos_atual - info_ant['qtd']
                    dif_t = minuto - info_ant['min']
                    
                    # Alerta se houver 2+ cantos em um intervalo de até 10 min
                    if dif_c >= 2 and dif_t <= 10 and m_id not in jogos_avisados_cantos:
                        msg = (f"🚩 *PRESSÃO DE CANTOS (10 MIN)*\n\n"
                               f"🏟️ {fixture['teams']['home']['name']} x {fixture['teams']['away']['name']}\n"
                               f"⏱️ Tempo: {minuto}'\n"
                               f"🚩 +{dif_c} cantos desde o minuto {info_ant['min']}\n\n"
                               f"📲 [ABRIR NA BET365](https://www.bet365.com/#/IP/)")
                        enviar_telegram(msg)
                        jogos_avisados_cantos.append(m_id)
                
                historico_cantos[m_id] = {'qtd': cantos_atual, 'min': minuto}

    except Exception as e:
        print(f"⚠️ Erro: {e}")

    time.sleep(120)
