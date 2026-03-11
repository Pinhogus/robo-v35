import requests
import time

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

ALERTA_CHUTES = 3  # número de chutes para disparar alerta
JOGO_ID = 1403774  # fixture ID do jogo que quer monitorar

HEADERS = {
    "x-apisports-key": API_KEY
}

# --- FUNÇÕES ---

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }
    requests.post(url, data=payload)

def get_shots_on_goal(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    shots_team1 = 0
    shots_team2 = 0
    team1_name = ""
    team2_name = ""

    if "response" in data and len(data["response"]) > 0:
        team1 = data["response"][0]["team"]
        team2 = data["response"][1]["team"]
        team1_name = team1["name"]
        team2_name = team2["name"]

        for team_stats in data["response"]:
            for stat in team_stats["statistics"]:
                if stat["type"] == "Shots on Goal":
                    if team_stats["team"]["id"] == team1["id"]:
                        shots_team1 = stat["value"]
                    else:
                        shots_team2 = stat["value"]

    return shots_team1, shots_team2, team1_name, team2_name

def monitor_game(fixture_id):
    while True:
        shots1, shots2, team1_name, team2_name = get_shots_on_goal(fixture_id)
        print(f"{team1_name}: {shots1} | {team2_name}: {shots2}")

        if shots1 >= ALERTA_CHUTES or shots2 >= ALERTA_CHUTES:
            mensagem = f"⚠️ ALERTA: {team1_name} ({shots1}) x {team2_name} ({shots2}) - {ALERTA_CHUTES} ou mais chutes a gol!"
            enviar_telegram(mensagem)
            break  # remove se quiser continuar monitorando

        time.sleep(30)  # verifica a cada 30 segundos

# --- RODAR MONITORAMENTO ---
monitor_game(JOGO_ID)