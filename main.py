import requests
import urllib.parse
import time
import csv
from datetime import datetime

# ================= CONFIGURAÇÕES =================
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TELEGRAM_TOKEN = "8418160843:AAE99kJmKxSiAsnH4TViXOkPhl5excFkFjU"
CHAT_ID = "8418160843"

HEADERS = {'x-apisports-key': API_KEY}

# ================= VARIÁVEIS =================
jogos_avisados_gols = set()
jogos_avisados_cantos = set()

sinais_ativos = {}  # fixture_id -> dados do sinal
resultados = []

ultimo_dia = datetime.now().date()

# ================= FUNÇÕES =================
def enviar_telegram(msg):
    texto = urllib.parse.quote(msg)
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    try:
        requests.get(url, timeout=10)
    except:
        pass


def verificar_historico_ht(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = r.get("response", [])
        gols_ht = 0
        for j in jogos:
            h = j["score"]["halftime"]["home"] or 0
            a = j["score"]["halftime"]["away"] or 0
            if h + a > 0:
                gols_ht += 1
        return (gols_ht / len(jogos)) * 100 if jogos else 0
    except:
        return 0


def salvar_resultado_csv(d):
    with open("resultados.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(d)


def registrar_resultado(tipo, liga, pais, green):
    lucro = 0.5 if green else -1
    dado = {
        "tipo": tipo,
        "liga": liga,
        "pais": pais,
        "resultado": "GREEN" if green else "RED",
        "lucro": lucro,
        "data": datetime.now()
    }
    resultados.append(dado)

    salvar_resultado_csv([
        tipo, liga, pais, dado["resultado"], lucro, dado["data"]
    ])


def resumo(periodo):
    agora = datetime.now()
    if periodo == "dia":
        base = [r for r in resultados if r["data"].date() == agora.date()]
    elif periodo == "semana":
        base = [r for r in resultados if r["data"].isocalendar()[1] == agora.isocalendar()[1]]
    else:
        base = [r for r in resultados if r["data"].month == agora.month]

    if not base:
        return

    greens = sum(1 for r in base if r["resultado"] == "GREEN")
    reds = sum(1 for r in base if r["resultado"] == "RED")
    lucro = sum(r["lucro"] for r in base)
    roi = (lucro / len(base)) * 100

    enviar_telegram(
        f"📊 *RESUMO {periodo.upper()}*\n\n"
        f"✅ Greens: {greens}\n"
        f"❌ Reds: {reds}\n"
        f"💰 Lucro: {lucro:.2f}u\n"
        f"📈 ROI: {roi:.1f}%"
    )


def ranking_ligas():
    ranking = {}

    for r in resultados:
        chave = f"{r['pais']} - {r['liga']}"
        ranking.setdefault(chave, {"greens": 0, "reds": 0, "lucro": 0})

        if r["resultado"] == "GREEN":
            ranking[chave]["greens"] += 1
        else:
            ranking[chave]["reds"] += 1

        ranking[chave]["lucro"] += r["lucro"]

    linhas = []
    for liga, d in ranking.items():
        total = d["greens"] + d["reds"]
        if total < 5:
            continue
        winrate = (d["greens"] / total) * 100
        roi = (d["lucro"] / total) * 100
        linhas.append((liga, total, winrate, roi))

    linhas.sort(key=lambda x: x[3], reverse=True)
    return linhas


# ================= LOOP PRINCIPAL =================
print("🛰️ Robô ATIVO | GOLS HT + CANTOS + ROI + RANKING")

while True:
    try:
        live = requests.get(
            "https://v3.football.api-sports.io/fixtures?live=all",
            headers=HEADERS,
            timeout=15
        ).json().get("response", [])

        for f in live:
            m_id = f["fixture"]["id"]
            minuto = f["fixture"]["status"]["elapsed"] or 0
            status = f["fixture"]["status"]["short"]

            g_h = f["goals"]["home"] or 0
            g_a = f["goals"]["away"] or 0

            home = f["teams"]["home"]
            away = f["teams"]["away"]
            liga = f["league"]["name"]
            pais = f["league"]["country"]

            # ---------- GOL HT ----------
            if 22 <= minuto <= 35 and g_h == 0 and g_a == 0:
                if m_id not in jogos_avisados_gols:
                    p_h = verificar_historico_ht(home["id"])
                    p_a = verificar_historico_ht(away["id"])

                    if p_h >= 80 or p_a >= 80:
                        enviar_telegram(
                            f"⚽ *GOL HT*\n"
                            f"{home['name']} x {away['name']}\n"
                            f"{pais} – {liga}\n"
                            f"{minuto}' | 0x0\n"
                            f"Histórico HT: {max(p_h, p_a):.0f}%"
                        )
                        sinais_ativos[m_id] = {
                            "tipo": "GOL_HT",
                            "liga": liga,
                            "pais": pais
                        }
                        jogos_avisados_gols.add(m_id)

            # ---------- RESULTADO HT ----------
            if status == "HT" and m_id in sinais_ativos:
                s = sinais_ativos[m_id]
                if s["tipo"] == "GOL_HT":
                    registrar_resultado(
                        "GOL_HT",
                        s["liga"],
                        s["pais"],
                        g_h + g_a > 0
                    )
                    del sinais_ativos[m_id]

        # ---------- RESUMO DIÁRIO ----------
        hoje = datetime.now().date()
        if hoje != ultimo_dia:
            resumo("dia")
            resumo("semana")
            resumo("mes")

            ranking = ranking_ligas()
            if ranking:
                msg = "🏆 *RANKING LIGAS*\n\n"
                for liga, total, win, roi in ranking[:5]:
                    msg += (
                        f"{liga}\n"
                        f"Sinais: {total} | Win: {win:.1f}% | ROI: {roi:.1f}%\n\n"
                    )
                enviar_telegram(msg)

            ultimo_dia = hoje

    except Exception as e:
        print("Erro:", e)

    time.sleep(120)
