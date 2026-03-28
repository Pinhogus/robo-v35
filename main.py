import requests
import asyncio
import os
from datetime import date
from telegram import Bot

TOKEN = os.environ.get(“TOKEN”, “”)
CHAT_ID = os.environ.get(“CHAT_ID”, “”)
FOOTBALL_API_KEY = os.environ.get(“FOOTBALL_API_KEY”, “”)

def pegar_jogos():
hoje = date.today().strftime(”%Y-%m-%d”)
url = “https://api.football-data.org/v4/matches?dateFrom=” + hoje + “&dateTo=” + hoje
headers = {“X-Auth-Token”: FOOTBALL_API_KEY}

```
try:
    response = requests.get(url, headers=headers, timeout=15)
except Exception as e:
    print("Erro de conexao: " + str(e))
    return []

if response.status_code != 200:
    print("Erro HTTP " + str(response.status_code))
    return []

dados = response.json()
jogos = []

for partida in dados.get("matches", []):
    try:
        liga_nome = partida["competition"]["name"]
        liga_code = partida["competition"]["code"]
        home = partida["homeTeam"].get("shortName") or partida["homeTeam"].get("name", "")
        away = partida["awayTeam"].get("shortName") or partida["awayTeam"].get("name", "")
        if not home or not away:
            continue
        jogos.append({
            "liga": liga_nome,
            "liga_code": liga_code,
            "home": home,
            "away": away,
        })
    except Exception:
        continue

print("Jogos encontrados: " + str(len(jogos)))
return jogos
```

def adicionar_stats(jogos):
for j in jogos:
j[“media_gols”] = 2.5
j[“over25”] = 55
j[“under25”] = 55
j[“media_ultimos5”] = 2.5
return jogos

def score_under(j):
score = 0
if j.get(“media_gols”, 99) <= 2.2:
score += 3
elif j.get(“media_gols”, 99) <= 2.5:
score += 1
if j.get(“under25”, 0) >= 65:
score += 3
elif j.get(“under25”, 0) >= 55:
score += 1
if j.get(“media_ultimos5”, 99) <= 2.0:
score += 2
elif j.get(“media_ultimos5”, 99) <= 2.5:
score += 1
return max(score, 0)

def score_over(j):
score = 0
if j.get(“media_gols”, 0) >= 3.0:
score += 3
elif j.get(“media_gols”, 0) >= 2.7:
score += 1
if j.get(“over25”, 0) >= 65:
score += 3
elif j.get(“over25”, 0) >= 55:
score += 1
if j.get(“media_ultimos5”, 0) >= 3.0:
score += 2
elif j.get(“media_ultimos5”, 0) >= 2.5:
score += 1
return max(score, 0)

def rankear(jogos):
for j in jogos:
j[“score_under”] = score_under(j)
j[“score_over”] = score_over(j)

```
top_under = sorted(
    [j for j in jogos if j["score_under"] > 0],
    key=lambda x: x["score_under"],
    reverse=True
)[:10]

top_over = sorted(
    [j for j in jogos if j["score_over"] > 0],
    key=lambda x: x["score_over"],
    reverse=True
)[:10]

return top_under, top_over
```

def montar_mensagem(top_under, top_over):
if not top_under and not top_over:
return “Nenhum jogo encontrado hoje.”

```
msg = "PRE-LISTA DO DIA\n"
msg += "--------------------\n\n"
msg += "TOP UNDER 2.5\n"

if top_under:
    for i, j in enumerate(top_under, 1):
        msg += str(i) + ". " + j["home"] + " x " + j["away"] + "\n"
        msg += "   Score: " + str(j["score_under"]) + "\n"
else:
    msg += "Nenhum jogo qualificado.\n"

msg += "\nTOP OVER 2.5\n"
if top_over:
    for i, j in enumerate(top_over, 1):
        msg += str(i) + ". " + j["home"] + " x " + j["away"] + "\n"
        msg += "   Score: " + str(j["score_over"]) + "\n"
else:
    msg += "Nenhum jogo qualificado.\n"

msg += "\n--------------------\n"
msg += "Use como referencia, nao como garantia."
return msg
```

async def enviar_async(msg):
try:
async with Bot(token=TOKEN) as bot:
await bot.send_message(chat_id=CHAT_ID, text=msg)
print(“Mensagem enviada!”)
except Exception as e:
print(“Erro ao enviar: “ + str(e))

def enviar(msg):
asyncio.run(enviar_async(msg))

def main():
print(“Buscando jogos…”)
jogos = pegar_jogos()

```
if not jogos:
    enviar("Nao encontrei jogos hoje.")
    return

jogos = adicionar_stats(jogos)
top_under, top_over = rankear(jogos)
msg = montar_mensagem(top_under, top_over)
print(msg)
enviar(msg)
```

if **name** == “**main**”:
main()
