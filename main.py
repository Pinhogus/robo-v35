import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
from telegram import Bot

# =========================
# CONFIG
# =========================
TOKEN = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

# =========================
# 1. PEGAR JOGOS (SoccerStats)
# =========================
def pegar_jogos():
    url = "https://www.soccerstats.com/matches.asp"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    jogos = []

    tabela = soup.find("table", {"id": "btable"})

    if not tabela:
        print("Erro ao encontrar tabela")
        return jogos

    for row in tabela.find_all("tr"):
        cols = row.find_all("td")

        if len(cols) > 5:
            try:
                liga = cols[0].text.strip()
                time1 = cols[2].text.strip()
                time2 = cols[4].text.strip()

                # filtro simples (evita lixo)
                if time1 and time2:
                    jogos.append({
                        "liga": liga,
                        "home": time1,
                        "away": time2
                    })
            except:
                continue

    return jogos

# =========================
# 2. ADICIONAR MÉTRICAS (FASE 1)
# =========================
def adicionar_stats(jogos):
    for j in jogos:
        j["media_gols"] = round(random.uniform(2.0, 3.2), 2)
        j["over25"] = random.randint(45, 80)
        j["under25"] = random.randint(45, 80)
        j["media_ultimos5"] = round(random.uniform(1.5, 3.5), 2)
    return jogos

# =========================
# 3. SCORING
# =========================
def score_under(j):
    score = 0

    if j["media_gols"] <= 2.2:
        score += 2
    if j["under25"] >= 60:
        score += 2
    if j["media_ultimos5"] <= 2.0:
        score += 2

    return score


def score_over(j):
    score = 0

    if j["media_gols"] >= 2.8:
        score += 2
    if j["over25"] >= 65:
        score += 2
    if j["media_ultimos5"] >= 3.0:
        score += 2

    return score

# =========================
# 4. RANKING
# =========================
def rankear(jogos):
    for j in jogos:
        j["score_under"] = score_under(j)
        j["score_over"] = score_over(j)

    top_under = sorted(jogos, key=lambda x: x["score_under"], reverse=True)[:10]
    top_over = sorted(jogos, key=lambda x: x["score_over"], reverse=True)[:10]

    return top_under, top_over

# =========================
# 5. MENSAGEM
# =========================
def montar_mensagem(top_under, top_over):
    msg = "📊 PRÉ-LISTA DO DIA (AMANHÃ)\n\n"

    msg += "🔵 TOP 10 UNDER:\n"
    for j in top_under:
        msg += f"{j['home']} x {j['away']} | Score: {j['score_under']}\n"

    msg += "\n🔴 TOP 10 OVER:\n"
    for j in top_over:
        msg += f"{j['home']} x {j['away']} | Score: {j['score_over']}\n"

    return msg

# =========================
# 6. TELEGRAM
# =========================
def enviar(msg):
    bot = Bot(token=TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# MAIN
# =========================
def main():
    print("Buscando jogos...")
    jogos = pegar_jogos()

    print(f"{len(jogos)} jogos encontrados")

    jogos = adicionar_stats(jogos)

    top_under, top_over = rankear(jogos)

    msg = montar_mensagem(top_under, top_over)

    enviar(msg)

    print("Mensagem enviada!")

if __name__ == "__main__":
    main()
