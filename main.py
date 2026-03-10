import requests
import urllib.parse
import time

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

HEADERS = {
    "x-apisports-key": API_KEY
}

jogos_avisados_cantos = []
jogos_avisados_gols = []


def verificar_visitante_sofre_fora(team_id):

    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = res.get("response", [])

        jogos_fora = []
        sofreu = 0

        for j in jogos:

            away_id = j["teams"]["away"]["id"]

            if away_id == team_id:
                jogos_fora.append(j)

            if len(jogos_fora) == 5:
                break

        if len(jogos_fora) < 5:
            return 0

        for j in jogos_fora:

            gols_sofridos = j.get("goals", {}).get("home") or 0

            if gols_sofridos > 0:
                sofreu += 1

        return (sofreu / 5) * 100

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


print("🛰️ Robô rodando: Gols HT + Cantos")


while True:

    try:

        url_live = "https://v3.football.api-sports.io/fixtures?live=all"

        response = requests.get(url_live, headers=HEADERS, timeout=15).json()

        jogos = response.get("response", [])

        print(f"📊 Jogos ao vivo: {len(jogos)} | {time.strftime('%H:%M:%S')}")

        for fixture in jogos:

            m_id = fixture["fixture"]["id"]

            minuto = fixture.get("fixture", {}).get("status", {}).get("elapsed") or 0

            g_h = fixture.get("goals", {}).get("home") or 0
            g_a = fixture.get("goals", {}).get("away") or 0

            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]

            liga = fixture["league"]["name"]
            pais = fixture["league"]["country"]

            # LINKS
            link_bet365 = "https://www.bet365.com/#/IP/"

            home_slug = home.lower().replace(" ", "-")
            away_slug = away.lower().replace(" ", "-")

            link_sofascore = f"https://www.sofascore.com/{home_slug}-{away_slug}"

            # ===============================
            # GOL HT
            # ===============================

            if 22 <= minuto <= 35 and g_h == 0 and g_a == 0:

                if m_id not in jogos_avisados_gols:

                    id_visitante = fixture["teams"]["away"]["id"]

                    perc = verificar_visitante_sofre_fora(id_visitante)

                    if perc >= 80:

                        msg = (
                            f"⚽ *ALERTA GOL HT*\n\n"
                            f"🌍 {pais} | {liga}\n"
                            f"🏟️ {home} x {away}\n"
                            f"⏱️ {minuto}' | 🥅 0x0\n"
                            f"📊 Visitante sofre fora: {perc:.0f}%\n\n"
                            f"📊 Mapa de pressão\n{link_sofascore}\n\n"
                            f"📲 Bet365\n{link_bet365}"
                        )

                        enviar_telegram(msg)

                        jogos_avisados_gols.append(m_id)

            # ===============================
            # CANTOS
            # ===============================

            if m_id not in jogos_avisados_cantos:

                try:

                    stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"

                    stats_res = requests.get(stats_url, headers=HEADERS, timeout=10).json()

                    stats = stats_res.get("response", [])

                    if len(stats) >= 2:

                        c_h = next(
                            (s["value"] for s in stats[0]["statistics"] if s["type"] == "Corner Kicks"),
                            0
                        ) or 0

                        c_a = next(
                            (s["value"] for s in stats[1]["statistics"] if s["type"] == "Corner Kicks"),
                            0
                        ) or 0

                        alerta = False

                        if minuto <= 45:
                            if c_h >= 5 or c_a >= 5:
                                alerta = True

                        elif minuto > 45:
                            if c_h >= 10 or c_a >= 10:
                                alerta = True

                        if alerta:

                            msg = (
                                f"🚩 *ALERTA CANTOS*\n\n"
                                f"🌍 {pais} | {liga}\n"
                                f"🏟️ {home} {g_h}x{g_a} {away}\n"
                                f"⏱️ {minuto}'\n"
                                f"🚩 Cantos: {c_h} x {c_a}\n\n"
                                f"📊 Mapa de pressão\n{link_sofascore}\n\n"
                                f"📲 Bet365\n{link_bet365}"
                            )

                            enviar_telegram(msg)

                            jogos_avisados_cantos.append(m_id)

                except Exception as e:
                    print("Erro Cantos:", e)

    except Exception as e:
        print("Erro geral:", e)

    time.sleep(120)
