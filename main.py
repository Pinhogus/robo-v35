import requests
import time

API_KEY = "SUA_API_KEY_AQUI"

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# ===============================
# LOOP PRINCIPAL
# ===============================

while True:
    print("\n==============================")
    print("🔄 INICIANDO VARREDURA...")
    print("==============================")

    try:
        # ===============================
        # BUSCAR JOGOS AO VIVO
        # ===============================
        url_live = f"{BASE_URL}/fixtures?live=all"

        res = requests.get(url_live, headers=HEADERS, timeout=15)

        print("STATUS CODE LIVE:", res.status_code)

        if res.status_code != 200:
            print("❌ ERRO NA API LIVE:", res.text)

        response = res.json()

        if "errors" in response and response["errors"]:
            print("🚨 ERRO DETECTADO:", response["errors"])

        jogos = response.get("response", [])

        print(f"📊 Varredura LIVE: {len(jogos)} jogos encontrados")

        # ===============================
        # LOOP DOS JOGOS
        # ===============================
        for jogo in jogos:

            fixture_id = jogo["fixture"]["id"]
            minuto = jogo["fixture"]["status"]["elapsed"]

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            gols_home = jogo["goals"]["home"]
            gols_away = jogo["goals"]["away"]

            print(f"\n⚽ {home} {gols_home} x {gols_away} {away} | {minuto} min")

            # ===============================
            # BUSCAR ODDS PRÉ LIVE
            # ===============================
            try:
                url_odds = f"{BASE_URL}/odds?fixture={fixture_id}"
                res_odds = requests.get(url_odds, headers=HEADERS, timeout=15)

                if res_odds.status_code != 200:
                    print("❌ ERRO ODDS:", res_odds.text)
                    continue

                odds_data = res_odds.json()
                bookmakers = odds_data.get("response", [])

                if not bookmakers:
                    continue

                markets = bookmakers[0]["bookmakers"][0]["bets"]

                favorito = None
                odd_favorito = None

                for market in markets:
                    if market["name"] == "Match Winner":
                        for odd in market["values"]:
                            if odd["odd"] is not None:
                                if odd_favorito is None or float(odd["odd"]) < odd_favorito:
                                    favorito = odd["value"]
                                    odd_favorito = float(odd["odd"])

                if not favorito or not odd_favorito:
                    continue

                print(f"⭐ Favorito: {favorito} @ {odd_favorito}")

            except Exception as e:
                print("🚨 ERRO AO BUSCAR ODDS:", e)
                continue

            # ===============================
            # ESTRATÉGIA FAVORITO PERDENDO
            # ===============================
            try:
                if odd_favorito <= 1.40:

                    if favorito == home and gols_home < gols_away:
                        print("🚨 ALERTA: FAVORITO PERDENDO (HOME)")
                    
                    elif favorito == away and gols_away < gols_home:
                        print("🚨 ALERTA: FAVORITO PERDENDO (AWAY)")

                    elif gols_home == gols_away:
                        print("⚠️ FAVORITO EMPATANDO")

            except Exception as e:
                print("🚨 ERRO NA ESTRATÉGIA:", e)

    except Exception as e:
        print("🚨 ERRO GERAL NA VARREDURA:", e)

    print("\n⏳ Aguardando 300 segundos...")
    time.sleep(300)
