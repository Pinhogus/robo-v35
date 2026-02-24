import requests
import urllib.parse
import time
from collections import defaultdict

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

jogos_avisados_gols = []
jogos_avisados_cantos = []
ranking_ligas = {}

# ===============================
# TELEGRAM
# ===============================

def enviar_telegram(mensagem):
    texto = urllib.parse.quote(mensagem)
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    try:
        requests.get(url, timeout=10)
    except:
        pass

# ===============================
# RANKING DE LIGAS HT
# ===============================

def calcular_ranking_ligas():
    print("🔎 Calculando ranking das ligas HT...")
    ligas_stats = defaultdict(list)

    url = "https://v3.football.api-sports.io/fixtures?last=500"
    res = requests.get(url, headers=HEADERS, timeout=15).json()
    jogos = res.get("response", [])

    for j in jogos:
        liga = j['league']['name']
        h_ht = j.get('score', {}).get('halftime', {}).get('home') or 0
        a_ht = j.get('score', {}).get('halftime', {}).get('away') or 0
        
        if (h_ht + a_ht) > 0:
            ligas_stats[liga].append(1)
        else:
            ligas_stats[liga].append(0)

    ranking = {}
    for liga, resultados in ligas_stats.items():
        if len(resultados) >= 20:
            ranking[liga] = (sum(resultados) / len(resultados)) * 100

    top30 = dict(sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:30])
    print("🏆 TOP 30 ligas HT carregadas")
    return top30

# ===============================
# FILTRO CASA x FORA
# ===============================

def verificar_mandante_ht(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        jogos = res.get('response', [])
        jogos_casa = [j for j in jogos if j['teams']['home']['id'] == team_id]

        if not jogos_casa:
            return 0

        marcou = sum(1 for j in jogos_casa if (j.get('score', {}).get('halftime', {}).get('home') or 0) > 0)
        return (marcou / len(jogos_casa)) * 100
    except:
        return 0

def verificar_visitante_sofre_ht(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        jogos = res.get('response', [])
        jogos_fora = [j for j in jogos if j['teams']['away']['id'] == team_id]

        if not jogos_fora:
            return 0

        sofreu = sum(1 for j in jogos_fora if (j.get('score', {}).get('halftime', {}).get('home') or 0) > 0)
        return (sofreu / len(jogos_fora)) * 100
    except:
        return 0

# ===============================
# LINKS BOOKMAKERS
# ===============================

def gerar_links(home, away):
    busca = urllib.parse.quote(f"{home} vs {away}")
    bet365 = f"https://www.bet365.com/#/AX/K{busca}"
    paddypower = f"https://www.paddypower.com/search?search={busca}"
    onex = f"https://1xbet.com/en/search?q={busca}"
    return bet365, paddypower, onex

# ===============================
# INICIALIZAÇÃO
# ===============================

ranking_ligas = calcular_ranking_ligas()

print("🛰️ Robô Híbrido 4.0 Iniciado")

while True:
    try:
        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])

        print(f"📊 {len(jogos)} jogos ao vivo | {time.strftime('%H:%M:%S')}")

        for fixture in jogos:
            m_id = fixture['fixture']['id']
            minuto = fixture['fixture']['status']['elapsed'] or 0
            g_h = fixture['goals']['home'] or 0
            g_a = fixture['goals']['away'] or 0

            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            liga = fixture['league']['name']

            # ===============================
            # GOL HT ESTRUTURAL
            # ===============================
            if liga in ranking_ligas:

                if 20 <= minuto <= 35 and g_h == 0 and g_a == 0:
                    if m_id not in jogos_avisados_gols:

                        id_h = fixture['teams']['home']['id']
                        id_a = fixture['teams']['away']['id']

                        perc_marca = verificar_mandante_ht(id_h)
                        perc_sofre = verificar_visitante_sofre_ht(id_a)

                        if perc_marca >= 70 and perc_sofre >= 70:

                            bet365, paddypower, onex = gerar_links(home, away)

                            msg = (f"⚽ *GOL HT TOP LIGA*\n\n"
                                   f"🏆 Liga: {liga} ({ranking_ligas[liga]:.1f}% HT)\n"
                                   f"🏟️ {home} x {away}\n"
                                   f"⏱️ {minuto}' | 0x0\n\n"
                                   f"📊 Casa marca HT: {perc_marca:.0f}%\n"
                                   f"📊 Visitante sofre HT: {perc_sofre:.0f}%\n\n"
                                   f"💰 Entrada: Over 0.5 HT\n\n"
                                   f"🔗 Bet365: {bet365}\n"
                                   f"🔗 PaddyPower: {paddypower}\n"
                                   f"🔗 1xBet: {onex}")

                            enviar_telegram(msg)
                            jogos_avisados_gols.append(m_id)

            # ===============================
            # CANTOS FIXOS
            # ===============================
            if m_id not in jogos_avisados_cantos:

                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                stats_res = requests.get(stats_url, headers=HEADERS).json()

                cantos = 0
                for team in stats_res.get('response', []):
                    for s in team.get('statistics', []):
                        if s['type'] == 'Corner Kicks':
                            cantos += int(s['value'] or 0)

                if 30 <= minuto <= 45 and cantos >= 5:
                    enviar_telegram(f"🚩 OVER 5 CANTOS HT\n🏆 {liga}\n🏟️ {home} x {away}\n⏱️ {minuto}'")
                    jogos_avisados_cantos.append(m_id)

                if minuto >= 75 and cantos >= 10:
                    enviar_telegram(f"🚩 OVER 10 CANTOS FT\n🏆 {liga}\n🏟️ {home} x {away}\n⏱️ {minuto}'")
                    jogos_avisados_cantos.append(m_id)

    except Exception as e:
        print("Erro:", e)

    time.sleep(240)
