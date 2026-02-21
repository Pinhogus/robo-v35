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

jogos_avisados_cantos = set()
jogos_avisados_gols = set()
cache_historico = {}

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
    if team_id in cache_historico:
        return cache_historico[team_id]

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

        percentual = (gols_ht / len(jogos)) * 100
        cache_historico[team_id] = percentual
        return percentual

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


print("🛰️ Robô Híbrido OTIMIZADO")

# =====================================================
# LOOP PRINCIPAL
# =====================================================

while True:

    try:
        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()

        if response.get("errors"):
            print("⚠️ Erro API:", response.get("errors"))
            time.sleep(180)
            continue

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
            # ⚽ GOL HT (20–35 min)
            # =====================================================

            if 20 <= minuto <= 35 and g_h == 0 and g_a == 0:

                if m_id not in jogos_avisados_gols:

                    id_h = fixture["teams"]["home"]["id"]
                    id_a = fixture["teams"]["away"]["id"]

                    perc_h = verificar_historico_ht(id_h)
                    perc_a = verificar_historico_ht(id_a)

                    if perc_h >= 80 or perc_a >= 80:

                        msg = (
                            f"⚽ *GOL HT 1.50+*\n\n"
                            f"🌍 {pais} | {liga}\n"
                            f"🏟️ {home} x {away}\n"
                            f"⏱️ {minuto}' | 0x0\n"
                            f"📊 Histórico HT: {max(perc_h, perc_a):.0f}%"
                        )

                        enviar_telegram(msg)
                        jogos_avisados_gols.add(m_id)

            # =====================================================
            # 🚩 CANTOS (Só busca estatística se minuto relevante)
            # =====================================================

            if m_id not in jogos_avisados_cantos:

                # Só vale buscar estatística se:
                # 1º tempo até 45
                # ou 2º tempo após 60 (evita gastar à toa)

                if minuto <= 45 or minuto >= 60:

                    try:
                        stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                        stats_res = requests.get(stats_url, headers=HEADERS, timeout=10).json()
                        stats = stats_res.get("response", [])

                        if len(stats) >= 2:

                            c_h = next(
                                (s["value"] for s in stats[0]["statistics"] if s["type"] == "Corner Kicks"),
                                0
                            )

                            c_a = next(
                                (s["value"] for s in stats[1]["statistics"] if s["type"] == "Corner Kicks"),
                                0
                            )

                            c_h = limpar_valor(c_h)
                            c_a = limpar_valor(c_a)

                            alerta = False

                            if minuto <= 45:
                                if c_h >= 5 or c_a >= 5:
                                    alerta = True
                            elif minuto >= 60:
                                if c_h >= 10 or c_a >= 10:
                                    alerta = True

                            if alerta:

                                msg = (
                                    f"🚩 *ALERTA CANTOS 5/10*\n\n"
                                    f"🌍 {pais} | {liga}\n"
                                    f"🏟️ {home} {g_h}x{g_a} {away}\n"
                                    f"⏱️ {minuto}'\n"
                                    f"🚩 Cantos: {c_h} x {c_a}"
                                )

                                enviar_telegram(msg)
                                jogos_avisados_cantos.add(m_id)

                    except Exception as e:
                        print("Erro Cantos:", e)

    except Exception as e:
        print("⚠️ Erro Geral:", e)

    # 🔥 Intervalo mais eficiente
    time.sleep(120)
