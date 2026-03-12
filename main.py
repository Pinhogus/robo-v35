import requests
import time

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

HEADERS = {
    "x-apisports-key": API_KEY
}

ALERTA_CHUTES = 3

# guarda jogos que já enviaram alerta
jogos_alertados = set()

# --- TELEGRAM ---
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    requests.post(url, data=payload)

# --- PEGAR JOGOS AO VIVO ---
def jogos_ao_vivo():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data["response"]

# --- PEGAR ESTATISTICAS ---
def estatisticas_jogo(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    shots1 = 0
    shots2 = 0

    if data["response"]:
        for team in data["response"]:
            for stat in team["statistics"]:
                if stat["type"] == "Shots on Goal":
                    if shots1 == 0:
                        shots1 = stat["value"] or 0
                    else:
                        shots2 = stat["value"] or 0

    return shots1, shots2

# --- LOOP PRINCIPAL ---
while True:
    try:
        jogos = jogos_ao_vivo()

        for jogo in jogos:

            fixture_id = jogo["fixture"]["id"]
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]
            minuto = jogo["fixture"]["status"]["elapsed"]

            shots1, shots2 = estatisticas_jogo(fixture_id)

            if (shots1 >= ALERTA_CHUTES or shots2 >= ALERTA_CHUTES) and fixture_id not in jogos_alertados:

                mensagem = (
                    f"🚨 ALERTA DE PRESSÃO\n\n"
                    f"{home} x {away}\n"
                    f"Minuto: {minuto}\n\n"
                    f"Chutes no gol:\n"
                    f"{home}: {shots1}\n"
                    f"{away}: {shots2}"
                )

                enviar_telegram(mensagem)

                jogos_alertados.add(fixture_id)

        time.sleep(30)

    except Exception as e:
        print("Erro:", e)
        time.sleep(30)