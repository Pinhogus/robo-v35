import requests
import time
from datetime import datetime

# ================= CONFIGURAÇÕES =================
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAE99kJmKxSiAsnH4TViXOkPhl5excFkFj"
CHAT_ID = "8418160843"

HEADERS = {"x-apisports-key": API_KEY}

# ================= TELEGRAM =================
def telegram(msg):
    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage",
            params={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass

# ================= VARIÁVEIS GERAIS =================
ultimo_dia = datetime.now().date()

# ================= ROBÔ GOLS =================
avisados_gols = set()
sinais_gols = {}
resultados_gols = []

def historico_ht(team_id):
    try:
        r = requests.get(
            f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10",
            headers=HEADERS, timeout=10
        ).json()["response"]
        gols = sum(
            1 for j in r
            if (j["score"]["halftime"]["home"] or 0) +
               (j["score"]["halftime"]["away"] or 0) > 0
        )
        return (gols / len(r)) * 100 if r else 0
    except:
        return 0

def registrar_gol(liga, pais, green):
    lucro = 0.5 if green else -1
    resultados_gols.append({
        "liga": liga,
        "pais": pais,
        "green": green,
        "lucro": lucro,
        "data": datetime.now()
    })

def resumo_gols(periodo):
    agora = datetime.now()
    if periodo == "dia":
        base = [r for r in resultados_gols if r["data"].date() == agora.date()]
    elif periodo == "semana":
        base = [r for r in resultados_gols if r["data"].isocalendar()[1] == agora.isocalendar()[1]]
    else:
        base = [r for r in resultados_gols if r["data"].month == agora.month]

    if not base:
        return

    greens = sum(1 for r in base if r["green"])
    reds = len(base) - greens
    lucro = sum(r["lucro"] for r in base)
    roi = (lucro / len(base)) * 100

    telegram(
        f"⚽ *RESUMO GOLS – {periodo.upper()}*\n\n"
        f"✅ Greens: {greens}\n"
        f"❌ Reds: {reds}\n"
        f"💰 Lucro: {lucro:.2f}u\n"
        f"📈 ROI: {roi:.1f}%"
    )

# ================= ROBÔ CANTOS =================
avisados_cantos = set()
historico_cantos = {}
resultados_cantos = []

def registrar_canto(liga, pais, green):
    lucro = 0.4 if green else -1
    resultados_cantos.append({
        "liga": liga,
        "pais": pais,
        "green": green,
        "lucro": lucro,
        "data": datetime.now()
    })

def resumo_cantos(periodo):
    agora = datetime.now()
    if periodo == "dia":
        base = [r for r in resultados_cantos if r["data"].date() == agora.date()]
    elif periodo == "semana":
        base = [r for r in resultados_cantos if r["data"].isocalendar()[1] == agora.isocalendar()[1]]
    else:
        base = [r for r in resultados_cantos if r["data"].month == agora.month]

    if not base:
        return

    greens = sum(1 for r in base if r["green"])
    reds = len(base) - greens
    lucro = sum(r["lucro"] for r in base)
    roi = (lucro / len(base)) * 100

    telegram(
        f"🚩 *RESUMO CANTOS – {periodo.upper()}*\n\n"
        f"✅ Greens: {greens}\n"
        f"❌ Reds: {reds}\n"
        f"💰 Lucro: {lucro:.2f}u\n"
        f"📈 ROI: {roi:.1f}%"
    )

# ================= INÍCIO =================
print("🚀 Robô GOLS + CANTOS iniciado")

while True:
    try:
        jogos = requests.get(
            "https://v3.football.api-sports.io/fixtures?live=all",
            headers=HEADERS, timeout=15
        ).json()["response"]

        for f in jogos:
            fid = f["fixture"]["id"]
            minuto = f["fixture"]["status"]["elapsed"] or 0
            status = f["fixture"]["status"]["short"]

            gh = f["goals"]["home"] or 0
            ga = f["goals"]["away"] or 0

            home = f["teams"]["home"]
            away = f["teams"]["away"]
            liga = f["league"]["name"]
            pais = f["league"]["country"]

            # ========== GOLS HT ==========
            if 22 <= minuto <= 35 and gh == 0 and ga == 0:
                if fid not in avisados_gols:
                    ph = historico_ht(home["id"])
                    pa = historico_ht(away["id"])
                    if ph >= 80 or pa >= 80:
                        telegram(
                            f"⚽ *GOL HT*\n"
                            f"{home['name']} x {away['name']}\n"
                            f"{pais} – {liga}\n"
                            f"{minuto}' | 0x0\n"
                            f"Histórico HT: {max(ph, pa):.0f}%"
                        )
                        sinais_gols[fid] = {"liga": liga, "pais": pais}
                        avisados_gols.add(fid)

            if status == "HT" and fid in sinais_gols:
                registrar_gol(liga, pais, gh + ga > 0)
                del sinais_gols[fid]

            # ========== CANTOS ==========
            if fid not in historico_cantos:
                historico_cantos[fid] = []

            stats = requests.get(
                f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}",
                headers=HEADERS, timeout=10
            ).json()["response"]

            total_cantos = sum(
                s["value"] or 0
                for t in stats
                for s in t["statistics"]
                if s["type"] == "Corner Kicks"
            )

            historico_cantos[fid].append(total_cantos)
            historico_cantos[fid] = historico_cantos[fid][-10:]

            if fid not in avisados_cantos:
                if (33 <= minuto <= 42) or (80 <= minuto <= 88):
                    if len(historico_cantos[fid]) >= 2:
                        if historico_cantos[fid][-1] - historico_cantos[fid][0] >= 3:
                            telegram(
                                f"🚩 *CANTOS*\n"
                                f"{home['name']} x {away['name']}\n"
                                f"{pais} – {liga}\n"
                                f"{minuto}' | +3 cantos (10 min)"
                            )
                            avisados_cantos.add(fid)

            if status == "FT" and fid in avisados_cantos:
                registrar_canto(liga, pais, True)
                avisados_cantos.remove(fid)

        # ======== RESUMOS =========
        hoje = datetime.now().date()
        if hoje != ultimo_dia:
            resumo_gols("dia")
            resumo_gols("semana")
            resumo_gols("mes")

            resumo_cantos("dia")
            resumo_cantos("semana")
            resumo_cantos("mes")

            ultimo_dia = hoje

    except Exception as e:
        print("Erro:", e)

    time.sleep(360)
