import requests
import urllib.parse
import time

# ================== CONFIGURAÇÕES ==================

API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0"
CHAT_ID = "1027866106"

HEADERS = {"x-apisports-key": API_KEY}

# ================== VARIÁVEIS ==================

historico_cantos = {}
historico_tempo = {}
avisados = []

# ================== FUNÇÕES ==================

def enviar_telegram(msg):
    texto = urllib.parse.quote(msg)
    url = (
        f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        f"?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    )
    try:
        requests.get(url, timeout=10)
    except:
        pass

def limpar(valor):
    try:
        return int(valor)
    except:
        return 0

def historico_ht(team_id):
    try:
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = r.get("response", [])
        if not jogos:
            return 0

        gols = 0
        for j in jogos:
            h = j["score"]["halftime"]["home"] or 0
            a = j["score"]["halftime"]["away"] or 0
            if h + a > 0:
                gols += 1

        return (gols / len(jogos)) * 100
    except:
        return 0

def stats_jogo(fixture_id):
    cantos = 0
    chutes_gol = 0
    try:
        url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        for team in r.get("response", []):
            for s in team.get("statistics", []):
                if s["type"] == "Corner Kicks":
                    cantos += limpar(s["value"])
                if s["type"] == "Shots on Goal":
                    chutes_gol += limpar(s["value"])
    except:
        pass

    return cantos, chutes_gol

# ================== ROBÔ ==================

print("🤖 ROBÔ GOL HT + CANTOS COM SCORE | ATIVO")

while True:
    try:
        live_url = "https://v3.football.api-sports.io/fixtures?live=all"
        live = requests.get(live_url, headers=HEADERS, timeout=15).json().get("response", [])

        print(f"🔍 {len(live)} jogos ao vivo | {time.strftime('%H:%M:%S')}")

        for f in live:
            m_id = f["fixture"]["id"]
            minuto = f["fixture"]["status"]["elapsed"] or 0
            g_h = f["goals"]["home"] or 0
            g_a = f["goals"]["away"] or 0

            cantos, chutes = stats_jogo(m_id)

            score = 0

            # -------- SCORE CHUTES NO GOL --------
            if chutes >= 2:
                score += 2
            if chutes >= 4:
                score += 4

            # -------- SCORE TEMPO + PLACAR --------
            if 18 <= minuto <= 35 and g_h == 0 and g_a == 0:
                score += 2

            # -------- SCORE HISTÓRICO HT --------
            h_id = f["teams"]["home"]["id"]
            a_id = f["teams"]["away"]["id"]
            hist = max(historico_ht(h_id), historico_ht(a_id))
            if hist >= 70:
                score += 2

            # -------- SCORE CANTOS DINÂMICOS --------
            if 25 <= minuto <= 45:
                if m_id not in historico_cantos:
                    historico_cantos[m_id] = cantos
                    historico_tempo[m_id] = minuto
                else:
                    dif = cantos - historico_cantos[m_id]
                    tempo = minuto - historico_tempo[m_id]

                    if dif >= 2 and tempo <= 10:
                        score += 3
                    if dif >= 4:
                        score += 5

                    historico_cantos[m_id] = cantos
                    historico_tempo[m_id] = minuto

            # -------- DISPARO FINAL --------
            if score >= 8 and m_id not in avisados:
                msg = (
                    f"🔥 *PRESSÃO ALTA ({score} pts)*\n\n"
                    f"🏟 {f['teams']['home']['name']} x {f['teams']['away']['name']}\n"
                    f"⏱ {minuto}' | {g_h}x{g_a}\n"
                    f"🎯 Chutes no gol: {chutes}\n"
                    f"🚩 Cantos: {cantos}\n"
                    f"📊 Histórico HT: {hist:.0f}%\n\n"
                    f"💰 Mercados:\n"
                    f"- Over 0.5 HT\n"
                    f"- Cantos ao vivo\n\n"
                    f"🔗 Bet365:\nhttps://www.bet365.com/#/IP/\n\n"
                    f"🔗 Alternativas (🇮🇪):\n"
                    f"Betfair | Paddy Power | BoyleSports"
                )
                enviar_telegram(msg)
                avisados.append(m_id)

    except Exception as e:
        print("⚠️ Erro:", e)

    time.sleep(120)
