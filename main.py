import requests
import time

# ===== CONFIGURAÇÕES =====
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TELEGRAM_TOKEN = "8418160843:AAElU7KJsdQ0MtzhP8"
CHAT_ID = "1027866106"

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

# ===== EXTRAÇÃO FLEXÍVEL =====
def extrair(stat_list, palavra_chave):
    for s in stat_list:
        if palavra_chave.lower() in s["type"].lower():
            return int(s["value"] or 0)
    return 0

# ===== LÓGICA PRINCIPAL =====
def analisar_jogos():
    jogos = buscar_jogos_ao_vivo()

    print(f"\nJogos ao vivo encontrados: {len(jogos)}")

    for jogo in jogos:
        fixture_id = jogo["fixture"]["id"]

        if fixture_id in jogos_enviados:
            continue

        minuto = jogo["fixture"]["status"]["elapsed"]
        tempo = jogo["fixture"]["status"]["short"]
        gols_casa = jogo["goals"]["home"]
        gols_fora = jogo["goals"]["away"]

        print(f"\nAnalisando jogo ID {fixture_id} | Minuto: {minuto} | Tempo: {tempo} | Placar: {gols_casa}x{gols_fora}")

        if tempo == "1H" and minuto is not None and 15 <= minuto <= 25 and gols_casa == 0 and gols_fora == 0:

            print(">> Passou no filtro principal")

            stats = buscar_estatisticas(fixture_id)

            if len(stats) < 2:
                print(">> Estatísticas insuficientes")
                continue

            time1 = stats[0]
            time2 = stats[1]

            print("Tipos de estatísticas disponíveis:")
            print([s["type"] for s in time1["statistics"]])

            ataques1 = extrair(time1["statistics"], "danger")
            final1 = extrair(time1["statistics"], "shot on")
            esc1 = extrair(time1["statistics"], "corner")

            ataques2 = extrair(time2["statistics"], "danger")
            final2 = extrair(time2["statistics"], "shot on")
            esc2 = extrair(time2["statistics"], "corner")

            total_ataques = ataques1 + ataques2
            total_final = final1 + final2

            print(f"Ataques: {ataques1} x {ataques2}")
            print(f"Finalizações no gol: {final1} x {final2}")
            print(f"Escanteios: {esc1} x {esc2}")

            # CRITÉRIO SUPER LEVE PARA TESTE
            condicao = (
                ataques1 >= 8 or
                ataques2 >= 8 or
                total_ataques >= 15 or
                total_final >= 1
            )

            print("Condição:", condicao)

            if condicao:

                liga = jogo["league"]["name"]
                pais = jogo["league"]["country"]
                time_casa = jogo["teams"]["home"]["name"]
                time_fora = jogo["teams"]["away"]["name"]

                mensagem = f"""
🚨 <b>OVER 0.5 HT - DEBUG TESTE</b>

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
                print("🚨 SINAL ENVIADO!")

# ===== LOOP =====
while True:
    try:
        analisar_jogos()
        time.sleep(60)
    except Exception as e:
        print("Erro:", e)
        time.sleep(60)