import requests
import time

# ===== CONFIGURAÇÕES =====
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TELEGRAM_TOKEN = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106I"

HEADERS = {
    "x-apisports-key": API_KEY
}

jogos_enviados = set()

# ===== TELEGRAM =====
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# ===== BUSCAR JOGOS AO VIVO =====
def buscar_jogos_ao_vivo():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    response = requests.get(url, headers=HEADERS)
    return response.json()["response"]

# ===== BUSCAR ESTATÍSTICAS =====
def buscar_estatisticas(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()["response"]

def extrair(stat_list, tipo):
    for s in stat_list:
        if s["type"] == tipo:
            return int(s["value"] or 0)
    return 0

# ===== LÓGICA =====
def analisar_jogos():
    jogos = buscar_jogos_ao_vivo()

    for jogo in jogos:
        fixture_id = jogo["fixture"]["id"]

        if fixture_id in jogos_enviados:
            continue

        minuto = jogo["fixture"]["status"]["elapsed"]
        tempo = jogo["fixture"]["status"]["short"]
        gols_casa = jogo["goals"]["home"]
        gols_fora = jogo["goals"]["away"]

        if tempo == "1H" and 15 <= minuto <= 28 and gols_casa == 0 and gols_fora == 0:

            stats = buscar_estatisticas(fixture_id)
            if len(stats) < 2:
                continue

            time1 = stats[0]
            time2 = stats[1]

            ataques1 = extrair(time1["statistics"], "Dangerous Attacks")
            final1 = extrair(time1["statistics"], "Shots on Goal")
            esc1 = extrair(time1["statistics"], "Corner Kicks")

            ataques2 = extrair(time2["statistics"], "Dangerous Attacks")
            final2 = extrair(time2["statistics"], "Shots on Goal")
            esc2 = extrair(time2["statistics"], "Corner Kicks")

            total_ataques = ataques1 + ataques2

            # CRITÉRIO VOLUME
            condicao = (
                (ataques1 >= 6 and final1 >= 1 and esc1 >= 1) or
                (ataques2 >= 6 and final2 >= 1 and esc2 >= 1) or
                (total_ataques >= 12)
            )

            if condicao:

                liga = jogo["league"]["name"]
                pais = jogo["league"]["country"]
                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]

                mensagem = f"""
🚨 <b>OVER 0.5 HT - VOLUME</b>

🏆 {liga} - {pais}
⚔️ {time_casa} x {time_fora}
⏱️ {minuto}'

🔥 Ataques: {ataques1} x {ataques2}
🎯 Finalizações: {final1} x {final2}
🚩 Escanteios: {esc1} x {esc2}

📈 Entrada sugerida: Over 0.5 HT
                """

                enviar_telegram(mensagem)
                jogos_enviados.add(fixture_id)
                print("Sinal enviado!")

# ===== LOOP =====
while True:
    try:
        analisar_jogos()
        time.sleep(18caf0)
    except Exception as e:
        print("Erro:", e)
        time.sleep(180)
