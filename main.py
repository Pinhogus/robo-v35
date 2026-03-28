import requests
import asyncio
from datetime import date
from telegram import Bot
from telegram.constants import ParseMode

# =========================

# CONFIG - preencha aqui

# =========================

TOKEN = "8418160843:AAGnbicIYPV-MxZQvZcF-HbpOTmJcrx-qLE"
CHAT_ID = "1027866106"

# Cadastro GRATUITO em: https://www.football-data.org/client/register

# Sua chave aparece no dashboard logo apos o cadastro (email + senha)

FOOTBALL_API_KEY = "d7381d52cb3b4063b5192623a0c6720d"

# =========================

# 1. PEGAR JOGOS (API football-data.org)

# =========================

# Ligas disponíveis no plano GRATUITO:

# PL=Premier League, PD=La Liga, BL1=Bundesliga, SA=Serie A,

# FL1=Ligue 1, DED=Eredivisie, BSA=Brasileirao, PPL=Primeira Liga

LIGAS_GRATIS = [“PL”, “PD”, “BL1”, “SA”, “FL1”, “DED”, “BSA”, “PPL”]

def pegar_jogos():
“””
Busca jogos do dia via API football-data.org (plano gratuito).
Retorna lista de dicts com liga, home, away e stats reais.
“””
hoje = date.today().strftime(”%Y-%m-%d”)
url = f”https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}”
headers = {“X-Auth-Token”: FOOTBALL_API_KEY}

```
try:
    response = requests.get(url, headers=headers, timeout=15)
except requests.RequestException as e:
    print(f"Erro de conexao: {e}")
    return []

if response.status_code == 403:
    print("Chave de API invalida ou sem permissao. Verifique FOOTBALL_API_KEY.")
    return []

if response.status_code != 200:
    print(f"Erro HTTP {response.status_code}: {response.text[:200]}")
    return []

dados = response.json()
jogos = []

for partida in dados.get("matches", []):
    try:
        liga_code = partida["competition"]["code"]
        liga_nome = partida["competition"]["name"]
        home = partida["homeTeam"]["shortName"] or partida["homeTeam"]["name"]
        away = partida["awayTeam"]["shortName"] or partida["awayTeam"]["name"]

        if not home or not away:
            continue

        jogos.append({
            "liga": liga_nome,
            "liga_code": liga_code,
            "home": home,
            "away": away,
        })
    except (KeyError, TypeError):
        continue

print(f"  → {len(jogos)} jogos encontrados para hoje ({hoje})")
return jogos
```

# =========================

# 2. BUSCAR STATS REAIS (API-Football via RapidAPI)

# =========================

# OPCIONAL: se você tiver chave RapidAPI, descomente e preencha

# RAPIDAPI_KEY = “SUA_CHAVE_AQUI”

def buscar_stats_reais(home: str, away: str) -> dict:
“””
Placeholder para integração com API real.
Substitua pelo endpoint da sua API de stats.
Atualmente retorna valores neutros fixos como base.
“””
# Exemplo de chamada real (requer RapidAPI):
# url = “https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics”
# …
return {
“media_gols”: 2.5,
“over25”: 55,
“under25”: 55,
“media_ultimos5”: 2.5,
“fonte”: “base_neutra”
}

# =========================

# 3. ADICIONAR MÉTRICAS

# =========================

def adicionar_stats(jogos: list) -> list:
“””
Adiciona métricas a cada jogo.
Tenta buscar stats reais; usa base neutra se falhar.
“””
for j in jogos:
try:
stats = buscar_stats_reais(j[“home”], j[“away”])
j.update(stats)
except Exception as e:
print(f”  ⚠ Erro ao buscar stats de {j[‘home’]} x {j[‘away’]}: {e}”)
j[“media_gols”] = 2.5
j[“over25”] = 55
j[“under25”] = 55
j[“media_ultimos5”] = 2.5
j[“fonte”] = “fallback”

```
return jogos
```

# =========================

# 4. SCORING

# =========================

def score_under(j: dict) -> int:
“”“Pontua jogos com perfil UNDER 2.5.”””
score = 0

```
if j.get("media_gols", 99) <= 2.2:
    score += 3  # FIX: peso maior para métrica principal
elif j.get("media_gols", 99) <= 2.5:
    score += 1

if j.get("under25", 0) >= 65:
    score += 3
elif j.get("under25", 0) >= 55:
    score += 1

if j.get("media_ultimos5", 99) <= 2.0:
    score += 2
elif j.get("media_ultimos5", 99) <= 2.5:
    score += 1

return max(score, 0)  # FIX: nunca negativo
```

def score_over(j: dict) -> int:
“”“Pontua jogos com perfil OVER 2.5.”””
score = 0

```
if j.get("media_gols", 0) >= 3.0:
    score += 3
elif j.get("media_gols", 0) >= 2.7:
    score += 1

if j.get("over25", 0) >= 65:
    score += 3
elif j.get("over25", 0) >= 55:
    score += 1

if j.get("media_ultimos5", 0) >= 3.0:
    score += 2
elif j.get("media_ultimos5", 0) >= 2.5:
    score += 1

return max(score, 0)  # FIX: nunca negativo
```

# =========================

# 5. RANKING

# =========================

def rankear(jogos: list) -> tuple:
“””
Calcula scores e retorna top 10 under e top 10 over.
FIX: filtra jogos sem score mínimo (score > 0).
“””
for j in jogos:
j[“score_under”] = score_under(j)
j[“score_over”] = score_over(j)

```
# FIX: só inclui jogos com algum sinal
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

# =========================

# 6. MONTAR MENSAGEM

# =========================

def montar_mensagem(top_under: list, top_over: list) -> str:
“”“Monta a mensagem formatada para o Telegram.”””

```
if not top_under and not top_over:
    return "❌ Nenhum jogo encontrado ou com score válido hoje."

msg = "📊 *PRÉ-LISTA DO DIA*\n"
msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

# UNDER
msg += "🔵 *TOP UNDER 2.5*\n"
if top_under:
    for i, j in enumerate(top_under, 1):
        estrelas = "⭐" * min(j["score_under"], 5)  # máximo 5 estrelas visual
        msg += (
            f"{i}. {j['home']} x {j['away']}\n"
            f"   Score: {j['score_under']} {estrelas}\n"
        )
else:
    msg += "Nenhum jogo qualificado.\n"

msg += "\n🔴 *TOP OVER 2.5*\n"
if top_over:
    for i, j in enumerate(top_over, 1):
        estrelas = "⭐" * min(j["score_over"], 5)
        msg += (
            f"{i}. {j['home']} x {j['away']}\n"
            f"   Score: {j['score_over']} {estrelas}\n"
        )
else:
    msg += "Nenhum jogo qualificado.\n"

msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
msg += "⚠️ _Use como referência, não como garantia._"

return msg
```

# =========================

# 7. ENVIAR TELEGRAM - FIX: async/await correto

# =========================

async def enviar_async(msg: str):
“””
FIX PRINCIPAL: python-telegram-bot v20+ é 100% assíncrono.
A versão antiga usava bot.send_message() direto (síncrono),
o que causa RuntimeError nas versões novas.
“””
try:
async with Bot(token=TOKEN) as bot:
await bot.send_message(
chat_id=CHAT_ID,
text=msg,
parse_mode=ParseMode.MARKDOWN
)
print(“✅ Mensagem enviada com sucesso!”)
except Exception as e:
print(f”❌ Erro ao enviar para o Telegram: {e}”)

def enviar(msg: str):
“”“Wrapper síncrono para chamar a função async.”””
asyncio.run(enviar_async(msg))

# =========================

# MAIN

# =========================

def main():
print(“🔍 Buscando jogos…”)
jogos = pegar_jogos()
print(f”📋 {len(jogos)} jogos encontrados”)

```
if not jogos:
    enviar("❌ Não consegui encontrar jogos hoje. Verifique o scraping.")
    return

print("📈 Adicionando estatísticas...")
jogos = adicionar_stats(jogos)

print("🏆 Rankeando jogos...")
top_under, top_over = rankear(jogos)

print(f"  → Under: {len(top_under)} | Over: {len(top_over)}")

msg = montar_mensagem(top_under, top_over)
print("\n--- PRÉVIA DA MENSAGEM ---")
print(msg)
print("--------------------------\n")

enviar(msg)
```

if **name** == “**main**”:
main()
