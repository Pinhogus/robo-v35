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


# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def limpar_valor(valor):
    if valor is None:
        return 0
    try:
        return int(float(str(valor).replace('%', '').strip()))
    except:
        return 0


def verificar_historico_ht(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = res.get("response", [])
        if not jogos:
            return 0

        gols_ht = 0
        for j in jogos:
            h_ht = j.get("score", {}).get("halftime", {}).get("home") or 0
            a_ht = j.get("score", {}).get("halftime", {}).get("away") or 0
            if (h_ht + a_ht) > 0:
                gols_ht += 1

        return (gols_ht / len(jogos)) * 100

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


print("🛰️ Robô Híbrido Avançado: Gols HT + Estatísticas + Cantos")

while True:
    try:
        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get("response", [])

        print(f"📊 Varredura: {len(jogos)} jogos | {time.strftime('%H:%M:%S')}")

        for fixture in jogos:

            m_id = fixture["fixture"]["id"]
            minuto = fixture.get("fixture", {}).get("status", {}).get("elapsed") or 0
            g_h = fixture.get("goals", {}).get("home") or 0
            g_a = fixture.get("goals", {}).get("away") or 0

            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]

            liga = fixture["league"]["name"]
            pais = fixture["league"]["country"]

            # =====================================================
            # 🔥 1️⃣ ESTRATÉGIA GOL HT + ESTATÍSTICAS AO VIVO
            # =====================================================

            if 22 <= minuto <= 35 and g_h == 0 and g_a == 0:
                if m_id not in jogos_avisados_gols:

                    id_h = fixture["teams"]["home"]["id"]
                    id_a = fixture["teams"]["away"]["id"]

                    perc_h = verificar_historico_ht(id_h)
                    perc_a = verificar_historico_ht(id_a)

                    if perc_h >= 80 or perc_a >= 80:

                        # Buscar estatísticas ao vivo
                        stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                        stats_res = requests.get(stats_url, headers=HEADERS, timeout=10).json()
                        stats = stats_res.get("response", [])

                        if len(stats) >= 2:

                            def get_stat(stat_name):
                                h = next((s["value"] for s in stats[0]["statistics"] if s["type"] == stat_name), 0)
                                a = next((s["value"] for s in stats[1]["statistics"] if s["type"] == stat_name), 0)
                                return limpar_valor(h) + limpar_valor(a)

                            shots_on = get_stat("Shots on Goal")
                            shots_total = get_stat("Total Shots")
                            ataques_perigosos = get_stat("Dangerous Attacks")

                            # FILTRO INTELIGENTE
                            if shots_on >= 3 and shots_total >= 8 and ataques_perigosos >= 20:

                                msg = (
                                    f"🔥 *GOL HT FORTE*\n\n"
                                    f"🌍 {pais} | {liga}\n"
                                    f"🏟️ {home} x {away}\n"
                                    f"⏱️ {minuto}' | 🥅 0x0\n"
                                    f"📊 Histórico HT: {max(perc_h, perc_a):.0f}%\n\n"
                                    f"🎯 Chutes no alvo: {shots_on}\n"
                                    f"🥅 Finalizações: {shots_total}\n"
                                    f"⚡ Ataques perigosos: {ataques_perigosos}\n\n"
                                    f"📊 SofaScore:\n"
                                    f"https://www.sofascore.com/\n\n"
                                    f"📲 Bet365 AO VIVO:\n"
                                    f"https://www.bet365.com/#/IP/"
                                )

                                enviar_telegram(msg)
                                jogos_avisados_gols.append(m_id)

            # =====================================================
            # 🚩 2️⃣ ESTRATÉGIA CANTOS 5 / 10 (MANTIDA)
            # =====================================================

            if m_id not in jogos_avisados_cantos:

                try:
                    stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                    stats_res = requests.get(stats_url, headers=HEADERS, timeout=10).json()
                    stats = stats_res.get("response", [])

                    if len(stats) >= 2:

                        def get_stat(stat_name):
                            h = next((s["value"] for s in stats[0]["statistics"] if s["type"] == stat_name), 0)
                            a = next((s["value"] for s in stats[1]["statistics"] if s["type"] == stat_name), 0)
                            return limpar_valor(h), limpar_valor(a)

                        c_h, c_a = get_stat("Corner Kicks")

                        alerta = False

                        if minuto <= 45:
                            if c_h >= 5 or c_a >= 5:
                                alerta = True
                        else:
                            if c_h >= 10 or c_a >= 10:
                                alerta = True

                        if alerta:
                            msg = (
                                f"🚩 *ALERTA CANTOS 5/10*\n\n"
                                f"🌍 {pais} | {liga}\n"
                                f"🏟️ {home} {g_h}x{g_a} {away}\n"
                                f"⏱️ {minuto}'\n"
                                f"🚩 Cantos: {c_h} x {c_a}\n\n"
                                f"📲 Bet365 AO VIVO:\n"
                                f"https://www.bet365.com/#/IP/"
                            )

                            enviar_telegram(msg)
                            jogos_avisados_cantos.append(m_id)

                except Exception as e:
                    print("Erro Cantos:", e)

    except Exception as e:
        print(f"⚠️ Erro Geral: {e}")

    time.sleep(120)
