import requests
import urllib.parse
import time

# ================= CONFIGURAÇÕES =================
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0"
CHAT_ID = "1027866106"

HEADERS = {'x-apisports-key': API_KEY}

historico_cantos = {}
jogos_avisados_cantos = []
jogos_avisados_gols = []

# ================= FUNÇÕES =================
def limpar_valor(valor):
    if valor is None:
        return 0
    try:
        return int(float(str(valor).replace('%', '').strip()))
    except:
        return 0


def enviar_telegram(mensagem):
    texto = urllib.parse.quote(mensagem)
    url = (
        f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        f"?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    )
    try:
        requests.get(url, timeout=10)
    except:
        pass


def verificar_historico_ht(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = res.get('response', [])
        if not jogos:
            return 0

        gols_ht = 0
        for j in jogos:
            h = j.get('score', {}).get('halftime', {}).get('home') or 0
            a = j.get('score', {}).get('halftime', {}).get('away') or 0
            if (h + a) > 0:
                gols_ht += 1

        return (gols_ht / len(jogos)) * 100
    except:
        return 0


print("🛰️ Robô ATIVO | GOL HT + CANTOS")

# ================= LOOP PRINCIPAL =================
while True:
    try:
        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])

        print(f"📊 Jogos ao vivo: {len(jogos)} | {time.strftime('%H:%M:%S')}")

        for fixture in jogos:
            m_id = fixture['fixture']['id']
            minuto = fixture['fixture']['status']['elapsed'] or 0

            g_h = fixture['goals']['home'] or 0
            g_a = fixture['goals']['away'] or 0

            home = fixture['teams']['home']
            away = fixture['teams']['away']
            liga = fixture['league']['name']
            pais = fixture['league']['country']

            # ================= GOL HT =================
            if 22 <= minuto <= 35 and g_h == 0 and g_a == 0:
                if m_id not in jogos_avisados_gols:
                    perc_h = verificar_historico_ht(home['id'])
                    perc_a = verificar_historico_ht(away['id'])

                    if perc_h >= 80 or perc_a >= 80:
                        msg = (
                            f"⚽ *GOL HT – ODD 1.50+*\n\n"
                            f"🏟️ {home['name']} x {away['name']}\n"
                            f"🌍 {pais} – {liga}\n"
                            f"⏱️ {minuto}' | 🥅 0x0\n"
                            f"📊 Histórico HT: {max(perc_h, perc_a):.0f}%\n\n"
                            f"💰 Over 0.5 HT\n"
                            f"📲 [ABRIR BET365](https://www.bet365.com/#/IP/)"
                        )
                        enviar_telegram(msg)
                        jogos_avisados_gols.append(m_id)

            # ================= CANTOS =================
            if (33 <= minuto <= 42) or (80 <= minuto <= 88):

                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                stats = requests.get(stats_url, headers=HEADERS, timeout=10).json()

                cantos_home = 0
                cantos_away = 0

                for team in stats.get('response', []):
                    for s in team.get('statistics', []):
                        if s['type'] == 'Corner Kicks':
                            if team['team']['id'] == home['id']:
                                cantos_home = limpar_valor(s['value'])
                            if team['team']['id'] == away['id']:
                                cantos_away = limpar_valor(s['value'])

                if m_id not in historico_cantos:
                    historico_cantos[m_id] = []

                historico_cantos[m_id].append({
                    "min": minuto,
                    "home": cantos_home,
                    "away": cantos_away
                })

                historico_cantos[m_id] = [
                    h for h in historico_cantos[m_id]
                    if minuto - h["min"] <= 12
                ]

                if len(historico_cantos[m_id]) >= 2 and m_id not in jogos_avisados_cantos:
                    antigo = historico_cantos[m_id][0]

                    dif_home = cantos_home - antigo["home"]
                    dif_away = cantos_away - antigo["away"]

                    sinal = None

                    if g_h <= g_a and dif_home >= 3:
                        sinal = home['name']
                    elif g_a <= g_h and dif_away >= 3:
                        sinal = away['name']

                    if sinal:
                        msg = (
                            f"🚩 *CANTOS – PRESSÃO*\n\n"
                            f"🏟️ {home['name']} x {away['name']}\n"
                            f"🌍 {pais} – {liga}\n"
                            f"⏱️ {minuto}'\n"
                            f"📊 {sinal} → +3 cantos últimos 10'\n\n"
                            f"📲 [ABRIR BET365](https://www.bet365.com/#/IP/)"
                        )
                        enviar_telegram(msg)
                        jogos_avisados_cantos.append(m_id)

    except Exception as e:
        print(f"⚠️ Erro: {e}")

    time.sleep(60)
