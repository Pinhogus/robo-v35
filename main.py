import requests
import urllib.parse
import time
import datetime

# ===============================
# CONFIGURAÇÕES
# ===============================

API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

HEADERS = {'x-apisports-key': API_KEY}

jogos_avisados_gols = []
jogos_avisados_cantos = []
cache_times = {}
jogos_reprovados = {}

# ===============================
# MODO INTELIGENTE (SEMANA / FDS)
# ===============================

hoje = datetime.datetime.now().weekday()

if hoje >= 5:
    print("🛑 MODO FIM DE SEMANA")
    TEMPO_CACHE_TIMES = 10800
    TEMPO_BLOQUEIO_JOGO = 2400
    INTERVALO_LOOP = 420
else:
    print("🚀 MODO SEMANA")
    TEMPO_CACHE_TIMES = 3600
    TEMPO_BLOQUEIO_JOGO = 900
    INTERVALO_LOOP = 120

# ===============================
# TELEGRAM
# ===============================

def enviar_telegram(msg):
    texto = urllib.parse.quote(msg)
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    try:
        requests.get(url, timeout=10)
    except:
        pass

# ===============================
# CACHE TIMES
# ===============================

def verificar_mandante_ht(team_id):
    agora = time.time()

    if team_id in cache_times:
        if agora - cache_times[team_id]["timestamp"] < TEMPO_CACHE_TIMES:
            return cache_times[team_id]["marca_ht"]

    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        jogos = res.get('response', [])
        jogos_casa = [j for j in jogos if j['teams']['home']['id'] == team_id]

        if not jogos_casa:
            return 0

        marcou = sum(1 for j in jogos_casa if (j.get('score', {}).get('halftime', {}).get('home') or 0) > 0)
        perc = (marcou / len(jogos_casa)) * 100

        cache_times[team_id] = {
            "marca_ht": perc,
            "timestamp": agora
        }

        return perc
    except:
        return 0


def verificar_visitante_sofre_ht(team_id):
    agora = time.time()

    if team_id in cache_times:
        if agora - cache_times[team_id]["timestamp"] < TEMPO_CACHE_TIMES:
            return cache_times[team_id].get("sofre_ht", 0)

    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS).json()
        jogos = res.get('response', [])
        jogos_fora = [j for j in jogos if j['teams']['away']['id'] == team_id]

        if not jogos_fora:
            return 0

        sofreu = sum(1 for j in jogos_fora if (j.get('score', {}).get('halftime', {}).get('home') or 0) > 0)
        perc = (sofreu / len(jogos_fora)) * 100

        if team_id not in cache_times:
            cache_times[team_id] = {}

        cache_times[team_id]["sofre_ht"] = perc
        cache_times[team_id]["timestamp"] = agora

        return perc
    except:
        return 0

# ===============================
# LINKS BOOKMAKERS
# ===============================

def gerar_links(home, away):
    busca = urllib.parse.quote(f"{home} vs {away}")
    bet365 = f"https://www.bet365.com/#/AX/K{busca}"
    onex = f"https://1xbet.com/en/search?q={busca}"
    paddypower = f"https://www.paddypower.com/search?search={busca}"
    return bet365, onex, paddypower

# ===============================
# LOOP PRINCIPAL
# ===============================

print("🛰️ ROBÔ INICIADO")

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
            pais = fixture['league']['country']

            # ===============================
            # BLOQUEIO TEMPORÁRIO
            # ===============================
            if m_id in jogos_reprovados:
                if time.time() - jogos_reprovados[m_id] < TEMPO_BLOQUEIO_JOGO:
                    continue
                else:
                    del jogos_reprovados[m_id]

            # ===============================
            # GOL HT
            # ===============================

            if 20 <= minuto <= 35 and g_h == 0 and g_a == 0:

                if m_id not in jogos_avisados_gols:

                    id_h = fixture['teams']['home']['id']
                    id_a = fixture['teams']['away']['id']

                    perc_marca = verificar_mandante_ht(id_h)
                    perc_sofre = verificar_visitante_sofre_ht(id_a)

                    if perc_marca >= 60 and perc_sofre >= 60:

                        bet365, onex, paddypower = gerar_links(home, away)

                        msg = (f"⚽ *GOL HT*\n\n"
                               f"🌍 {pais} - {liga}\n"
                               f"🏟️ {home} x {away}\n"
                               f"⏱️ {minuto}' | 0x0\n\n"
                               f"📊 Casa marca HT: {perc_marca:.0f}%\n"
                               f"📊 Visitante sofre HT: {perc_sofre:.0f}%\n\n"
                               f"💰 Entrada: Over 0.5 HT\n\n"
                               f"🔗 Bet365: {bet365}\n"
                               f"🔗 1xBet: {onex}\n"
                               f"🔗 PaddyPower: {paddypower}")

                        enviar_telegram(msg)
                        jogos_avisados_gols.append(m_id)

                    else:
                        jogos_reprovados[m_id] = time.time()

            # ===============================
            # ESCANTEIOS POR EQUIPE
            # ===============================

            if m_id not in jogos_avisados_cantos:

                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                stats_res = requests.get(stats_url, headers=HEADERS).json()

                cantos_home = 0
                cantos_away = 0

                for team in stats_res.get('response', []):
                    team_id_stat = team['team']['id']

                    for s in team.get('statistics', []):
                        if s['type'] == 'Corner Kicks':
                            if team_id_stat == fixture['teams']['home']['id']:
                                cantos_home = int(s['value'] or 0)
                            elif team_id_stat == fixture['teams']['away']['id']:
                                cantos_away = int(s['value'] or 0)

                # 5+ HT
                if 1 <= minuto <= 42:
                    if cantos_home >= 5 or cantos_away >= 5:

                        equipe = home if cantos_home >= 5 else away
                        total = cantos_home if cantos_home >= 5 else cantos_away

                        enviar_telegram(
                            f"🚩 *ESCANTEIOS HT*\n\n"
                            f"🌍 {pais} - {liga}\n"
                            f"🏟️ {home} x {away}\n"
                            f"⏱️ {minuto}'\n\n"
                            f"🔥 {equipe} tem {total} escanteios\n"
                            f"💰 Entrada: Over cantos HT"
                        )

                        jogos_avisados_cantos.append(m_id)

                # 10+ 2ºT
                elif minuto >= 46:
                    if cantos_home >= 10 or cantos_away >= 10:

                        equipe = home if cantos_home >= 10 else away
                        total = cantos_home if cantos_home >= 10 else cantos_away

                        enviar_telegram(
                            f"🚩 *ESCANTEIOS 2º TEMPO*\n\n"
                            f"🌍 {pais} - {liga}\n"
                            f"🏟️ {home} x {away}\n"
                            f"⏱️ {minuto}'\n\n"
                            f"🔥 {equipe} tem {total} escanteios\n"
                            f"💰 Entrada: Over cantos FT"
                        )

                        jogos_avisados_cantos.append(m_id)

    except Exception as e:
        print("Erro:", e)

    time.sleep(INTERVALO_LOOP)
