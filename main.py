import requests
from bs4 import BeautifulSoup
import asyncio
import re
from urllib.parse import unquote
from telegram import Bot
from telegram.constants import ParseMode

# =========================

# CONFIG - preencha aqui

# =========================

TOKEN = "8418160843:AAGnbicIYPV-MxZQvZcF-HbpOTmJcrx-qLE"
CHAT_ID = “1027866106”

# =========================

# 1. HELPERS DE LIMPEZA

# =========================

# Palavras que NUNCA aparecem em nomes de times de futebol

PALAVRAS_LIXO = {
“home”, “away”, “team”, “match”, “date”, “score”, “stats”, “goals”,
“played”, “points”, “league”, “scope”, “blog”, “today”, “per”, “game”,
“cookie”, “usage”, “options”, “mobile”, “app”, “privacy”, “policy”,
“settings”, “accept”, “decline”, “and”, “the”, “for”, “with”, “this”,
“that”, “from”, “page”, “site”, “data”, “info”, “news”, “more”, “all”,
“live”, “table”, “fixtures”, “results”, “standing”, “tip”, “bet”,
“odds”, “prediction”, “analysis”, “preview”, “report”, “update”,
}

# Palavras que frequentemente aparecem em nomes de times reais

# (usadas como critério positivo de validação)

SUFIXOS_TIME = {
“fc”, “cf”, “sc”, “ac”, “bc”, “bk”, “sk”, “fk”, “if”, “ff”,
“united”, “city”, “town”, “rovers”, “wanderers”, “athletic”,
“albion”, “rangers”, “county”, “villa”, “palace”, “orient”,
“wednesday”, “thursday”, “friday”, “saturday”,  # times com dia no nome
“hotspur”, “arsenal”, “chelsea”, “liverpool”,
}

def limpar_nome_time(texto: str) -> str:
“”“Limpa e normaliza texto extraído de célula HTML.”””
if not texto:
return “”
try:
texto = unquote(texto)
except Exception:
pass
# Remove tudo que não seja letra, espaço, hífen ou ponto
texto = re.sub(r”[^a-zA-ZÀ-ÿ\s-.']”, “ “, texto)
texto = re.sub(r”\s+”, “ “, texto).strip()
return texto

def nome_valido(nome: str) -> bool:
“””
Valida se o texto parece um nome de clube de futebol.
Critérios rígidos para eliminar lixo de UI/cookie/cabeçalho.
“””
if not nome:
return False

```
# Tamanho: times reais têm entre 3 e 30 chars
if len(nome) < 3 or len(nome) > 30:
    return False

# Precisa ter ao menos 3 letras (não só símbolos)
letras = re.sub(r"[^a-zA-ZÀ-ÿ]", "", nome)
if len(letras) < 3:
    return False

palavras = nome.lower().split()

# Rejeita se QUALQUER palavra for lixo conhecido e o nome for curto
# (nomes compostos reais podem ter "and" mas são raros)
if len(palavras) <= 3:
    for p in palavras:
        if p in PALAVRAS_LIXO:
            return False

# Rejeita frases longas (4+ palavras sem sufixo de time)
if len(palavras) >= 4:
    tem_sufixo = any(p in SUFIXOS_TIME for p in palavras)
    if not tem_sufixo:
        return False

# Rejeita se contém % ou números de 3+ dígitos (lixo de stats)
if "%" in nome or re.search(r"\d{3,}", nome):
    return False

# Rejeita se começa com letra minúscula (times sempre têm maiúscula)
if nome[0].islower():
    return False

return True
```

# =========================

# 2. PEGAR JOGOS (SCRAPING)

# =========================

def pegar_jogos():
“””
Busca jogos do dia no soccerstats.com.
Estratégia principal: procura links internos do tipo /ltable.asp?league=X
que o soccerstats usa para cada partida listada.
Fallback: varredura por separador ‘x’ entre células.
“””
url = “https://www.soccerstats.com/matches.asp”
headers = {
“User-Agent”: (
“Mozilla/5.0 (Windows NT 10.0; Win64; x64) “
“AppleWebKit/537.36 (KHTML, like Gecko) “
“Chrome/120.0.0.0 Safari/537.36”
)
}

```
try:
    response = requests.get(url, headers=headers, timeout=15)
    response.encoding = "utf-8"
except requests.RequestException as e:
    print(f"Erro de conexão: {e}")
    return []

if response.status_code != 200:
    print(f"Erro HTTP {response.status_code} ao acessar site")
    return []

soup = BeautifulSoup(response.text, "html.parser")
jogos = []
vistos = set()

# ── Estratégia principal: busca linhas que tenham link de time ──
# O soccerstats marca cada time com um link interno (href com teamstats.asp ou similar)
for row in soup.find_all("tr"):
    links = row.find_all("a", href=True)
    times_na_linha = []

    for link in links:
        href = link.get("href", "")
        texto = limpar_nome_time(link.text)

        # Links de times costumam apontar para ltable.asp ou teamstats.asp
        if any(p in href for p in ["ltable", "teamstats", "team", "latest"]):
            if nome_valido(texto):
                times_na_linha.append(texto)

    # Uma linha válida de jogo tem exatamente 2 times
    if len(times_na_linha) == 2:
        home, away = times_na_linha[0], times_na_linha[1]
        chave = home + "|" + away
        if chave not in vistos:
            vistos.add(chave)

            # Tenta detectar a liga pelo contexto próximo
            liga = "Internacional"
            prev = row.find_previous("td", {"colspan": True})
            if prev:
                txt_liga = prev.text.strip().split("stats")[0].strip()
                if txt_liga and len(txt_liga) < 50:
                    liga = txt_liga

            jogos.append({"liga": liga, "home": home, "away": away})

# ── Fallback: separador "x" entre células ──
if not jogos:
    print("  ⚠ Estratégia de links vazia, tentando separador 'x'...")
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        for i in range(1, len(cols) - 1):
            sep = cols[i].text.strip().lower()
            if sep == "x":
                h = limpar_nome_time(cols[i - 1].text)
                a = limpar_nome_time(cols[i + 1].text)
                if nome_valido(h) and nome_valido(a):
                    chave = h + "|" + a
                    if chave not in vistos:
                        vistos.add(chave)
                        jogos.append({"liga": "Internacional", "home": h, "away": a})

print(f"  → {len(jogos)} jogos válidos extraídos")
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
