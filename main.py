import requests
import time
import urllib.parse
from datetime import date

API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"

TELEGRAM_TOKEN = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

HEADERS = {
    "x-apisports-key": API_KEY
}

favoritos = {}
alertas = []

# ------------------------
# TELEGRAM
# ------------------------

def enviar(msg):

    texto = urllib.parse.quote(msg)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"

    requests.get(url)


# ------------------------
# PEGAR FAVORITOS
# ------------------------

def buscar_favoritos():

    hoje = date.today()

    print("🔎 Buscando odds do dia...")

    url = f"https://v3.football.api-sports.io/odds?date={hoje}"

    res = requests.get(url, headers=HEADERS).json()

    jogos = res["response"]

    for jogo in jogos:

        fixture = jogo["fixture"]["id"]

        for book in jogo["bookmakers"]:

            for bet in book["bets"]:

                if bet["name"] == "Match Winner":

                    home_odd = float(bet["values"][0]["odd"])
                    draw_odd = float(bet["values"][1]["odd"])
                    away_odd = float(bet["values"][2]["odd"])

                    home = bet["values"][0]["value"]
                    away = bet["values"][2]["value"]

                    if home_odd <= 1.60:

                        favoritos[fixture] = {
                            "team": home,
                            "odd": home_odd
                        }

                    if away_odd <= 1.60:

                        favoritos[fixture] = {
                            "team": away,
                            "odd": away_odd
                        }

                    break

            break

    print("⭐ Favoritos encontrados:", len(favoritos))


# ------------------------
# MONITORAR LIVE
# ------------------------

def monitorar():

    while True:

        url = "https://v3.football.api-sports.io/fixtures?live=all"

        res = requests.get(url, headers=HEADERS).json()

        jogos = res["response"]

        print("📊 Jogos ao vivo:", len(jogos))

        for jogo in jogos:

            fixture = jogo["fixture"]["id"]

            if fixture not in favoritos:
                continue

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            gols_home = jogo["goals"]["home"] or 0
            gols_away = jogo["goals"]["away"] or 0

            minuto = jogo["fixture"]["status"]["elapsed"]

            favorito = favoritos[fixture]["team"]
            odd = favoritos[fixture]["odd"]

            if fixture in alertas:
                continue

            if favorito == home and gols_away > gols_home:

                enviar_alerta(home, away, minuto, gols_home, gols_away, favorito, odd)
                alertas.append(fixture)

            if favorito == away and gols_home > gols_away:

                enviar_alerta(home, away, minuto, gols_home, gols_away, favorito, odd)
                alertas.append(fixture)

        time.sleep(180)


# ------------------------
# ALERTA
# ------------------------

def enviar_alerta(home, away, minuto, gh, ga, favorito, odd):

    msg = f"""
🚨 FAVORITO PERDENDO

⚽ {home} vs {away}

⏱️ {minuto}'
📊 {gh}-{ga}

⭐ Favorito: {favorito}
Odd pré-jogo: {odd}

🔥 Possível pressão do favorito
"""

    enviar(msg)


# ------------------------
# EXECUTAR
# ------------------------

buscar_favoritos()
monitorar()