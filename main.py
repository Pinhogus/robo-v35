“””
Bot Briefing Diário Over/Under — adaptado para Koyeb
Flask roda em paralelo apenas para manter o serviço vivo.
“””

import requests
import schedule
import time
import threading
from datetime import date
from flask import Flask

# ════════════════════════════════════════════════

# ⚙️  CONFIGURAÇÕES

# ════════════════════════════════════════════════

RAPIDAPI_KEY   = “https://free-api-live-football-data.p.rapidapi.com/football-players-search?search=m”
TELEGRAM_TOKEN = “8418160843:AAGnbicIYPV-MxZQvZcF-HbpOTmJcrx-qLE”
CHAT_ID        = “1027866106”
HORARIO_ENVIO  = “08:00”

LIGAS = {
39:   “Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿”,
140:  “La Liga 🇪🇸”,
135:  “Serie A 🇮🇹”,
78:   “Bundesliga 🇩🇪”,
61:   “Ligue 1 🇫🇷”,
2:    “Champions League 🌍”,
3:    “Europa League 🌍”,
848:  “Conference League 🌍”,
71:   “Brasileirão 🇧🇷”,
73:   “Copa do Brasil 🇧🇷”,
13:   “Libertadores 🌎”,
11:   “Sudamericana 🌎”,
253:  “MLS 🇺🇸”,
262:  “Liga MX 🇲🇽”,
88:   “Eredivisie 🇳🇱”,
94:   “Liga Portugal 🇵🇹”,
203:  “Süper Lig 🇹🇷”,
144:  “Pro League Bélgica 🇧🇪”,
128:  “Série A Argentina 🇦🇷”,
40:   “Championship 🏴󠁧󠁢󠁥󠁮󠁧󠁿”,
}

SEASON = 2024

TIMES_GRANDES = {
“Manchester City”, “Arsenal”, “Liverpool”, “Chelsea”,
“Manchester United”, “Tottenham”, “Newcastle”,
“Real Madrid”, “Barcelona”, “Atletico Madrid”,
“Inter”, “AC Milan”, “Juventus”, “Napoli”,
“Bayern Munich”, “Borussia Dortmund”, “Bayer Leverkusen”,
“PSG”, “Monaco”, “Marseille”,
“Flamengo”, “Palmeiras”, “Corinthians”, “Atletico Mineiro”,
“São Paulo”, “Grêmio”, “Internacional”, “Botafogo”, “Fluminense”,
“Boca Juniors”, “River Plate”,
}

# ════════════════════════════════════════════════

# 🌐  FLASK — health check para o Koyeb

# ════════════════════════════════════════════════

app = Flask(**name**)

@app.route(”/”)
def home():
return “✅ Bot Over/Under rodando.”, 200

@app.route(”/health”)
def health():
return {“status”: “ok”, “proximo_envio”: HORARIO_ENVIO}, 200

# ════════════════════════════════════════════════

# 🌐  API-FOOTBALL

# ════════════════════════════════════════════════

BASE_URL    = “https://api-football-v1.p.rapidapi.com/v3”
HEADERS_API = {
“X-RapidAPI-Key”:  RAPIDAPI_KEY,
“X-RapidAPI-Host”: “api-football-v1.p.rapidapi.com”,
}

calls_usadas = [0]

def api_get(endpoint, params):
calls_usadas[0] += 1
try:
r = requests.get(f”{BASE_URL}/{endpoint}”, headers=HEADERS_API,
params=params, timeout=15)
if r.status_code == 200:
return r.json()
except Exception as e:
print(f”[!] API erro: {e}”)
return None

# ════════════════════════════════════════════════

# 📅  JOGOS DO DIA

# ════════════════════════════════════════════════

def jogos_do_dia():
hoje = date.today().strftime(”%Y-%m-%d”)
jogos = []
for liga_id, liga_nome in LIGAS.items():
data = api_get(“fixtures”, {“league”: liga_id, “season”: SEASON, “date”: hoje})
if not data:
continue
for f in data.get(“response”, []):
home = f[“teams”][“home”][“name”]
away = f[“teams”][“away”][“name”]
jogos.append({
“id”:         f[“fixture”][“id”],
“liga”:       liga_nome,
“home”:       home,
“away”:       away,
“hora”:       f[“fixture”][“date”][11:16],
“importante”: home in TIMES_GRANDES or away in TIMES_GRANDES,
})
time.sleep(0.3)
jogos.sort(key=lambda x: (not x[“importante”], x[“hora”]))
return jogos

# ════════════════════════════════════════════════

# 📊  HISTÓRICO + SCORING

# ════════════════════════════════════════════════

def ultimos_jogos(team_id, qtd=5):
data = api_get(“fixtures”, {“team”: team_id, “season”: SEASON,
“last”: qtd, “status”: “FT”})
return data.get(“response”, []) if data else []

def stats_historico(jogos, team_id):
gols_m, gols_s, totais, over25, btts = [], [], [], 0, 0
for f in jogos:
hid = f[“teams”][“home”][“id”]
gm  = f[“goals”][“home”] if hid == team_id else f[“goals”][“away”]
gs  = f[“goals”][“away”] if hid == team_id else f[“goals”][“home”]
if gm is None or gs is None:
continue
t = gm + gs
gols_m.append(gm); gols_s.append(gs); totais.append(t)
if t > 2.5:  over25 += 1
if gm > 0 and gs > 0: btts += 1
n = len(totais) or 1
return {
“media_marcados”: round(sum(gols_m) / n, 2),
“media_sofridos”: round(sum(gols_s) / n, 2),
“media_total”:    round(sum(totais)  / n, 2),
“pct_over25”:     round(over25 / n * 100),
“pct_btts”:       round(btts   / n * 100),
}

def calcular_score(sh, sa):
if not sh or not sa:
return {“over”: 0, “under”: 0, “media_total”: 0,
“pct_over25”: 0, “pct_btts”: 0, “diagnostico”: “Sem dados”}

```
media_total = (sh["media_total"]  + sa["media_total"])  / 2
pct_over25  = (sh["pct_over25"]   + sa["pct_over25"])   / 2
pct_btts    = (sh["pct_btts"]     + sa["pct_btts"])     / 2

score_over  = min(100, int(media_total * 14) + int(pct_over25 * 0.30)
                      + int(pct_btts * 0.20)
                      + int((sh["media_marcados"] + sa["media_marcados"]) * 4))

pct_under25 = 100 - pct_over25
score_under = min(100, int(max(0, 2.5 - media_total) * 16)
                      + int(pct_under25 * 0.35)
                      + int(max(0, 1.2 - sh["media_marcados"]) * 12
                          + max(0, 1.2 - sa["media_marcados"]) * 12))

if score_over >= 70:
    diag = f"⚡ Jogo ABERTO — média {media_total:.1f} gols, {pct_over25:.0f}% over 2.5"
elif score_under >= 70:
    diag = f"🧊 Jogo TRAVADO — média {media_total:.1f} gols, {pct_under25:.0f}% under 2.5"
else:
    diag = f"⚖️ Equilibrado — média {media_total:.1f} gols"

return {"over": score_over, "under": score_under, "media_total": media_total,
        "pct_over25": pct_over25, "pct_btts": pct_btts, "diagnostico": diag}
```

def categoria(sc):
o, u = sc[“over”], sc[“under”]
if o >= 75 and o - u > 15:  return “🔴 OVER FORTE”
if o >= 60 and o - u > 5:   return “🟠 OVER MODERADO”
if u >= 75 and u - o > 15:  return “🔵 UNDER FORTE”
if u >= 60 and u - o > 5:   return “🟦 UNDER MODERADO”
return “⚪ SEM TENDÊNCIA”

def barra(score, size=8):
c = round(score / 100 * size)
return “█” * c + “░” * (size - c)

# ════════════════════════════════════════════════

# 📨  TELEGRAM

# ════════════════════════════════════════════════

def enviar(msg):
try:
requests.post(
f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage”,
json={“chat_id”: CHAT_ID, “text”: msg, “parse_mode”: “HTML”},
timeout=10,
)
except Exception as e:
print(f”[!] Telegram erro: {e}”)

# ════════════════════════════════════════════════

# 📋  BRIEFING DIÁRIO

# ════════════════════════════════════════════════

def briefing_diario():
hoje_str = date.today().strftime(”%d/%m/%Y”)
print(f”\n[{hoje_str}] Iniciando briefing…”)

```
enviar(
    f"📋 <b>BRIEFING DO DIA — {hoje_str}</b>\n"
    f"🏆 Análise Over/Under — jogos de hoje\n"
    f"━━━━━━━━━━━━━━━━━━━━━━"
)

jogos = jogos_do_dia()
if not jogos:
    enviar("ℹ️ Nenhum jogo encontrado hoje.")
    return

over_fortes, under_fortes, sem_tend = [], [], []

for jogo in jogos:
    fix = api_get("fixtures", {"id": jogo["id"]})
    if not fix or not fix.get("response"):
        continue
    f      = fix["response"][0]
    home_id = f["teams"]["home"]["id"]
    away_id = f["teams"]["away"]["id"]

    sh  = stats_historico(ultimos_jogos(home_id), home_id)
    sa  = stats_historico(ultimos_jogos(away_id), away_id)
    sc  = calcular_score(sh, sa)
    cat = categoria(sc)

    entry = {**jogo, "sc": sc, "cat": cat}
    if "OVER FORTE"  in cat: over_fortes.append(entry)
    elif "UNDER"     in cat: under_fortes.append(entry)
    else:                    sem_tend.append(entry)
    time.sleep(0.5)

# ── OVER ────────────────────────────────────
if over_fortes:
    msg = "🔴 <b>JOGOS — OVER (tendência gols)</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for e in over_fortes:
        sc = e["sc"]
        msg += (
            f"{'⭐ ' if e['importante'] else ''}"
            f"<b>{e['home']} x {e['away']}</b>\n"
            f"🏆 {e['liga']}  |  ⏱ {e['hora']} UTC\n"
            f"📊 OVER {sc['over']}/100  {barra(sc['over'])}\n"
            f"📈 {sc['diagnostico']}\n"
            f"🎯 Média: {sc['media_total']:.1f} gols  |  "
            f"Over2.5: {sc['pct_over25']:.0f}%  |  "
            f"BTTS: {sc['pct_btts']:.0f}%\n\n"
        )
    enviar(msg)

# ── UNDER ────────────────────────────────────
if under_fortes:
    msg = "🔵 <b>JOGOS — UNDER (tendência travado)</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for e in under_fortes:
        sc = e["sc"]
        msg += (
            f"{'⭐ ' if e['importante'] else ''}"
            f"<b>{e['home']} x {e['away']}</b>\n"
            f"🏆 {e['liga']}  |  ⏱ {e['hora']} UTC\n"
            f"📊 UNDER {sc['under']}/100  {barra(sc['under'])}\n"
            f"🧊 {sc['diagnostico']}\n"
            f"📉 Under2.5: {100 - sc['pct_over25']:.0f}%\n\n"
        )
    enviar(msg)

# ── SEM TENDÊNCIA (só importantes) ──────────
imp = [e for e in sem_tend if e["importante"]]
if imp:
    msg = "⚪ <b>IMPORTANTES — sem tendência clara</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for e in imp:
        sc = e["sc"]
        msg += (
            f"⭐ <b>{e['home']} x {e['away']}</b>\n"
            f"🏆 {e['liga']}  |  ⏱ {e['hora']} UTC\n"
            f"Over: {sc['over']}/100  |  Under: {sc['under']}/100\n\n"
        )
    enviar(msg)

enviar(
    f"✅ <b>Briefing concluído!</b>\n"
    f"🔴 Over fortes: {len(over_fortes)}\n"
    f"🔵 Under: {len(under_fortes)}\n"
    f"⚪ Sem tendência: {len(sem_tend)}\n"
    f"📡 API calls usadas: {calls_usadas[0]}/100\n"
    f"Bons trades! 🎯"
)
calls_usadas[0] = 0
```

# ════════════════════════════════════════════════

# 🚀  INICIALIZAÇÃO

# ════════════════════════════════════════════════

def rodar_agendador():
“”“Roda em thread separada para não bloquear o Flask.”””
briefing_diario()   # executa imediatamente ao subir
schedule.every().day.at(HORARIO_ENVIO).do(briefing_diario)
while True:
schedule.run_pending()
time.sleep(60)

if **name** == “**main**”:
# Inicia o agendador em background
t = threading.Thread(target=rodar_agendador, daemon=True)
t.start()

```
# Flask escuta na porta que o Koyeb espera
import os
port = int(os.environ.get("PORT", 8000))
print(f"🚀 Servidor Flask rodando na porta {port}")
app.run(host="0.0.0.0", port=port)
```
