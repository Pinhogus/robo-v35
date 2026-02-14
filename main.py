import requests
import time
from datetime import datetime, timedelta

# =========================
# 🔑 CONFIGURAÇÕES
# =========================

API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

# =========================
# ⚽ TIMES MONITORADOS (seus times fortes)
# =========================
STRONG_TEAMS = [
    "Manchester City","Arsenal","Liverpool","Manchester United","Chelsea","Tottenham",
    "Paris Saint-Germain","Lyon","Lens",
    "Inter","Juventus","AC Milan","Napoli","Atalanta","Roma","Como",
    "Bayern Munich","Borussia Dortmund","RB Leipzig","Bayer Leverkusen",
    "Real Madrid","Barcelona","Atletico Madrid",
    "Benfica","Porto","Sporting",
    "Union Saint-Gilloise",
    "Flamengo","Palmeiras","Atletico Mineiro","Sao Paulo","Corinthians",
    "Fluminense","Gremio","Internacional",
    "River Plate","Boca Juniors","Racing",
    "Al-Hilal","Al-Nassr","Al-Ittihad","Al-Ahli"
]

# =========================
# 📊 CACHE DE HISTÓRICO
# =========================
TEAM_HISTORY = {}  # Estatísticas históricas
ALERTED = {}      # Jogos já notificados

# =========================
# 📩 TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# =========================
# 📊 HISTÓRICO DE 15 JOGOS
# =========================
def get_team_history(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=15"
    r = requests.get(url, headers=HEADERS)
    games = r.json().get("response", [])

    lost_first = 0
    reacted = 0
    wins = 0
    draws = 0

    for g in games:
        home = g["teams"]["home"]["id"] == team_id
        goals_for = g["goals"]["home"] if home else g["goals"]["away"]
        goals_against = g["goals"]["away"] if home else g["goals"]["home"]

        halftime = g["score"]["halftime"]
        ht_for = halftime["home"] if home else halftime["away"]
        ht_against = halftime["away"] if home else halftime["home"]

        if ht_for < ht_against:
            lost_first += 1
            if goals_for >= goals_against:
                reacted += 1
                if goals_for > goals_against:
                    wins += 1
                else:
                    draws += 1

    rate = round((reacted / lost_first) * 100, 1) if lost_first > 0 else 0
    return lost_first, reacted, wins, draws, rate

# =========================
# 🟢🟡🔴 CLASSIFICAÇÃO DE CONFIANÇA
# =========================
def classify(rate):
    if rate >= 65: return "ALTA 🟢"
    if rate >= 40: return "MÉDIA 🟡"
    return "BAIXA 🔴"

# =========================
# 🌐 PRÉ-LIVE: FAVORITOS COM ODDS ≤ 1,40 HOJE E SÁBADO
# =========================
def get_pre_live_games():
    games_to_check = []
    today = datetime.utcnow().date()
    saturday = today + timedelta((5 - today.weekday()) % 7)  # Próximo sábado

    for day in [today, saturday]:
        date_str = day.strftime("%Y-%m-%d")
        url = f"https://v3.football.api-sports.io/fixtures?date={date_str}"
        r = requests.get(url, headers=HEADERS)
        fixtures = r.json().get("response", [])
        for f in fixtures:
            for side in ["home", "away"]:
                team = f["teams"][side]["name"]
                team_id = f["teams"][side]["id"]
                if team not in STRONG_TEAMS:
                    # aqui incluímos **favoritos de ligas importantes**
                    continue
                # Odds pré-live
                odds = f.get("odds", [])
                for o in odds:
                    if o["bookmaker"]["name"].lower() == "bet365":  # exemplo
                        odd_value = o["bets"][0]["values"][0]["odd"]
                        if odd_value <= 1.40:
                            games_to_check.append(f)
    return games_to_check

# =========================
# ⚽ JOGOS AO VIVO
# =========================
def get_live_games():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    r = requests.get(url, headers=HEADERS)
    return r.json().get("response", [])

# =========================
# 🧠 PROCESSAR JOGO AO VIVO
# =========================
def process_game(game):
    fixture_id = game["fixture"]["id"]
    minute = game["fixture"]["status"]["elapsed"]

    for side in ["home", "away"]:
        team = game["teams"][side]["name"]
        team_id = game["teams"][side]["id"]

        if team not in STRONG_TEAMS:
            continue

        goals_for = game["goals"][side]
        goals_against = game["goals"]["away" if side == "home" else "home"]

        if minute is None or minute < 20:
            continue

        losing = goals_for < goals_against
        draw_after_goal = goals_for == goals_against and goals_for > 0 and minute >= 46
        zero_zero_alert = goals_for == 0 and goals_against == 0 and minute <= 65 and minute >= 46

        if not (losing or draw_after_goal or zero_zero_alert):
            continue

        # Histórico
        if team_id not in TEAM_HISTORY:
            TEAM_HISTORY[team_id] = get_team_history(team_id)
        lost_first, reacted, wins, draws, rate = TEAM_HISTORY[team_id]
        confidence = classify(rate)

        # Níveis L1/L2/L3
        stats = {s.get("type"): s.get("value") for s in game.get("statistics", [{}])[0].get("statistics", [])}
        shots = int(stats.get("Shots on Goal", 0) or 0)
        possession = stats.get("Ball Possession", "0%").replace("%","")
        possession = int(possession) if possession.isdigit() else 0

        level = ""
        if possession >= 55 and shots >= 3: level = "🟡 L1"
        if possession >= 60 and shots >= 5: level = "🟠 L2"
        if shots >= 7 and minute < 75: level = "🔴 L3"

        key = f"{fixture_id}_{team}_{minute}"
        if key in ALERTED:
            continue
        ALERTED[key] = True

        send_telegram(
            f"{level} ALERTA DE FAVORITO\n\n"
            f"{team}\n"
            f"Placar: {goals_for}-{goals_against}\n"
            f"Minuto: {minute}\n\n"
            f"📊 Histórico (últimos 15 jogos):\n"
            f"Saiu perdendo: {lost_first}x\n"
            f"Reagiu: {reacted}x\n"
            f"Viradas: {wins} | Empates: {draws}\n"
            f"Taxa de reação: {rate}%\n"
            f"Confiança: {confidence}"
        )

# =========================
# ▶️ LOOP PRINCIPAL
# =========================
def run():
    send_telegram("🤖 Bot Favoritos Completo Pré-Live + Ao Vivo ATIVO")
    while True:
        try:
            live_games = get_live_games()
            for g in live_games:
                process_game(g)
        except Exception as e:
            print("Erro:", e)
        time.sleep(30)

run()
