import requests
import time
import urllib.parse

API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

HEADERS = {
    "x-apisports-key": API_KEY
}

jogos_alertados = set()


def enviar_telegram(msg):

    texto = urllib.parse.quote(msg)

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}"

    try:
        requests.get(url, timeout=10)
    except:
        pass


def pegar_odds(fixture_id):

    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10).json()

        bookmakers = r["response"][0]["bookmakers"]

        for b in bookmakers:

            if b["name"] == "Bet365":

                for bet in b["bets"]:

                    if bet["name"] == "Match Winner":

                        odds = bet["values"]

                        home_odd = float(odds[0]["odd"])
                        away_odd = float(odds[2]["odd"])

                        return home_odd, away_odd

    except:
        return None, None

    return None, None


print("🤖 Robô favorito perdendo iniciado")

while True:

    try:

        url = "https://v3.football.api-sports.io/fixtures?live=all"

        response = requests.get(url, headers=HEADERS, timeout=15).json()

        jogos = response.get("response", [])

        print(f"📊 {len(jogos)} jogos ao vivo")

        for jogo in jogos:

            fixture_id = jogo["fixture"]["id"]

            if fixture_id in jogos_alertados:
                continue

            minuto = jogo["fixture"]["status"]["elapsed"] or 0

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            g_home = jogo["goals"]["home"] or 0
            g_away = jogo["goals"]["away"] or 0

            liga = jogo["league"]["name"]
            pais = jogo["league"]["country"]

            home_odd, away_odd = pegar_odds(fixture_id)

            if home_odd is None:
                continue

            favorito = None

            if home_odd <= 1.60:
                favorito = "home"

            elif away_odd <= 1.60:
                favorito = "away"

            if favorito == "home" and g_home < g_away:

                msg = f"""
🚨 FAVORITO PERDENDO

🌍 {pais} | {liga}

🏟️ {home} x {away}

⏱️ {minuto}'
⚽ Placar: {g_home} x {g_away}

⭐ Favorito: {home}
Odd pré-jogo: {home_odd}

https://www.bet365.com/#/IP/
"""

                enviar_telegram(msg)

                jogos_alertados.add(fixture_id)

            if favorito == "away" and g_away < g_home:

                msg = f"""
🚨 FAVORITO PERDENDO

🌍 {pais} | {liga}

🏟️ {home} x {away}

⏱️ {minuto}'
⚽ Placar: {g_home} x {g_away}

⭐ Favorito: {away}
Odd pré-jogo: {away_odd}

https://www.bet365.com/#/IP/
"""

                enviar_telegram(msg)

                jogos_alertados.add(fixture_id)

    except Exception as e:

        print("Erro:", e)

    time.sleep(120)
