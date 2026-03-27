import requests
import time
import schedule
from datetime import datetime

# ═══════════════════════════════════════════════
#   ⚙️  CONFIGURAÇÕES
# ═══════════════════════════════════════════════

TELEGRAM_TOKEN     = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID            = "1027866106"
INTERVALO_MINUTOS  = 2

# ── Limiares do motor de scoring ──────────────

# OVER 0.5 HT (janela: 0–20 min, placar 0x0)
OVER_HT_SCORE_MIN       = 60    # score mínimo para disparar
OVER_HT_JANELA_MAX      = 22    # só dispara até este minuto
OVER_HT_CHUTES_MIN      = 4     # chutes totais mínimos no período

# OVER 2T (janela: 65+ min, placar ≤ 1 gol total)
OVER_2T_SCORE_MIN       = 65
OVER_2T_MINUTO_MIN      = 65
OVER_2T_PLACAR_MAX      = 1     # total de gols até agora

# UNDER scalping (qualquer momento)
UNDER_SCORE_MIN         = 65    # score mínimo de "jogo travado"
UNDER_CHUTES_MAX        = 5     # poucos chutes totais
UNDER_XGOLS_MAX         = 0.7   # baixo perigo estimado

# ── Top 20 ligas ──────────────────────────────
LIGAS = {
    17:    "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    8:     "La Liga 🇪🇸",
    23:    "Serie A 🇮🇹",
    35:    "Bundesliga 🇩🇪",
    34:    "Ligue 1 🇫🇷",
    7:     "Champions League 🌍",
    679:   "Europa League 🌍",
    17015: "Conference League 🌍",
    325:   "Brasileirão 🇧🇷",
    390:   "Copa do Brasil 🇧🇷",
    384:   "Libertadores 🌎",
    480:   "Sudamericana 🌎",
    242:   "MLS 🇺🇸",
    352:   "Liga MX 🇲🇽",
    37:    "Eredivisie 🇳🇱",
    238:   "Liga Portugal 🇵🇹",
    52:    "Süper Lig 🇹🇷",
    38:    "Pro League Bélgica 🇧🇪",
    155:   "Série A Argentina 🇦🇷",
    36:    "Scottish Prem 🏴󠁧󠁢󠁳󠁣󠁴󠁿",
}

# ── Times "grandes" por liga (boost de importância) ──
TIMES_GRANDES = {
    # Premier League
    "Manchester City", "Arsenal", "Liverpool", "Chelsea",
    "Manchester United", "Tottenham", "Newcastle",
    # La Liga
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Real Sociedad",
    # Serie A
    "Inter", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio",
    # Bundesliga
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
    # Ligue 1
    "PSG", "Monaco", "Marseille", "Lyon",
    # Brasileirão
    "Flamengo", "Palmeiras", "Corinthians", "São Paulo", "Atlético Mineiro",
    "Grêmio", "Internacional", "Botafogo", "Fluminense", "Santos", "Cruzeiro",
    # Libertadores / Sul-americana (extra)
    "Boca Juniors", "River Plate", "Nacional", "Peñarol",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.sofascore.com/",
    "Accept":  "application/json",
}

# ═══════════════════════════════════════════════
#   🧠  MEMÓRIA  (evita repetir alertas)
# ═══════════════════════════════════════════════

alertas_enviados = {}   # {jogo_id: set(chave_alerta)}


# ═══════════════════════════════════════════════
#   📨  TELEGRAM
# ═══════════════════════════════════════════════

def enviar(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg,
                                     "parse_mode": "HTML"}, timeout=10)
        ok = "✓" if r.status_code == 200 else "✗"
        print(f"  [{ok}] Telegram: {msg[:70].strip()}…")
    except Exception as e:
        print(f"  [✗] Telegram erro: {e}")


# ═══════════════════════════════════════════════
#   🌐  SOFASCORE
# ═══════════════════════════════════════════════

def get_json(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  [!] Req falhou: {url[-60:]} — {e}")
    return None


def jogos_ao_vivo():
    data = get_json("https://api.sofascore.com/api/v1/sport/football/events/live")
    return data.get("events", []) if data else []


def estatisticas(jogo_id: int):
    return get_json(f"https://api.sofascore.com/api/v1/event/{jogo_id}/statistics")


def incidents(jogo_id: int):
    """Busca eventos do jogo (gols, cartões, etc.)"""
    return get_json(f"https://api.sofascore.com/api/v1/event/{jogo_id}/incidents")


# ═══════════════════════════════════════════════
#   🔍  EXTRAÇÃO DE STATS
# ═══════════════════════════════════════════════

def stat(data, nome) -> tuple[float, float]:
    """Retorna (casa, fora) de uma estatística pelo nome."""
    if not data:
        return 0, 0
    try:
        for periodo in data.get("statistics", []):
            for grupo in periodo.get("groups", []):
                for item in grupo.get("statisticsItems", []):
                    if nome.lower() in item.get("name", "").lower():
                        h = float(str(item.get("home", 0) or 0).replace("%", "").strip() or 0)
                        a = float(str(item.get("away", 0) or 0).replace("%", "").strip() or 0)
                        return h, a
    except:
        pass
    return 0, 0


def xgols_estimado(chutes_gol_c, chutes_gol_f, chutes_tot_c, chutes_tot_f) -> float:
    """Estima perigo ofensivo geral (0-10 escala interna)."""
    return (chutes_gol_c + chutes_gol_f) * 0.35 + (chutes_tot_c + chutes_tot_f) * 0.12


def eh_jogo_importante(time_casa: str, time_fora: str) -> bool:
    return time_casa in TIMES_GRANDES or time_fora in TIMES_GRANDES


# ═══════════════════════════════════════════════
#   🚦  MOTOR DE SCORING
# ═══════════════════════════════════════════════

def calcular_scores(stats, minuto, gols_casa, gols_fora):
    """
    Retorna dict com scores 0-100 para cada tipo de sinal.
    """
    chutes_gol_c,  chutes_gol_f  = stat(stats, "Shots on target")
    chutes_tot_c,  chutes_tot_f  = stat(stats, "Total shots")
    posse_c,       _             = stat(stats, "Ball possession")
    esc_c,         esc_f         = stat(stats, "Corner kicks")
    atq_c,         atq_f         = stat(stats, "Attacks")
    atq_peri_c,    atq_peri_f    = stat(stats, "Dangerous attacks")

    total_chutes_gol = chutes_gol_c + chutes_gol_f
    total_chutes     = chutes_tot_c + chutes_tot_f
    total_escanteios = esc_c + esc_f
    total_atq_peri   = atq_peri_c + atq_peri_f
    total_gols       = gols_casa + gols_fora
    xg               = xgols_estimado(chutes_gol_c, chutes_gol_f, chutes_tot_c, chutes_tot_f)

    # ── OVER HT (0-20 min, 0x0, muito movimentado) ─────────────────
    score_over_ht = 0
    if minuto <= OVER_HT_JANELA_MAX and total_gols == 0:
        # ritmo de chutes por minuto (esperamos ≥ 0.3/min = 6 em 20 min)
        ritmo = total_chutes / max(minuto, 1)
        score_over_ht += min(40, int(ritmo * 80))         # até 40 pts
        score_over_ht += min(25, int(total_chutes_gol * 7))  # chutes a gol
        score_over_ht += min(20, int(total_atq_peri / 3))    # ataques perigosos
        score_over_ht += min(15, int(total_escanteios * 2.5)) # escanteios = pressão

    # ── OVER 2T (65+ min, placar baixo) ─────────────────────────────
    score_over_2t = 0
    if minuto >= OVER_2T_MINUTO_MIN and total_gols <= OVER_2T_PLACAR_MAX:
        score_over_2t += min(35, int(total_chutes_gol * 6))
        score_over_2t += min(25, int(total_atq_peri / 4))
        score_over_2t += min(20, int(total_escanteios * 1.8))
        # bônus se muito equilibrado (jogo aberto)
        if 40 <= posse_c <= 60:
            score_over_2t += 20

    # ── UNDER scalping (jogo morto) ─────────────────────────────────
    score_under = 0
    if total_gols == 0 or (total_gols == 1 and minuto < 70):
        # Jogo travado = poucos chutes, poucos ataques perigosos
        travamento = max(0, 10 - total_chutes)          # quanto mais travado, maior
        pouco_peri = max(0, 20 - total_atq_peri)
        ritmo_baixo = max(0, 5 - (total_chutes / max(minuto, 1) * 10))

        score_under += min(40, travamento * 4)
        score_under += min(30, int(pouco_peri * 1.5))
        score_under += min(30, int(ritmo_baixo * 6))

    return {
        "over_ht":  min(100, score_over_ht),
        "over_2t":  min(100, score_over_2t),
        "under":    min(100, score_under),
        # extras para o relatório
        "total_chutes":     total_chutes,
        "chutes_gol":       total_chutes_gol,
        "escanteios":       total_escanteios,
        "atq_perigosos":    total_atq_peri,
        "xg":               round(xg, 2),
        "posse_c":          posse_c,
    }


# ═══════════════════════════════════════════════
#   🔤  BARRA DE PROGRESSO  (visual no Telegram)
# ═══════════════════════════════════════════════

def barra(score: int, tamanho: int = 10) -> str:
    cheios = round(score / 100 * tamanho)
    return "█" * cheios + "░" * (tamanho - cheios)


def label_forca(score: int) -> str:
    if score >= 85: return "🔥 MUITO FORTE"
    if score >= 70: return "⚡ FORTE"
    return "✅ MODERADO"


# ═══════════════════════════════════════════════
#   📬  MONTAGEM E ENVIO DAS MENSAGENS
# ═══════════════════════════════════════════════

def processar_jogo(jogo):
    jogo_id    = jogo["id"]
    time_casa  = jogo["homeTeam"]["name"]
    time_fora  = jogo["awayTeam"]["name"]
    gols_c     = jogo.get("homeScore", {}).get("current", 0) or 0
    gols_f     = jogo.get("awayScore", {}).get("current", 0) or 0
    minuto     = jogo.get("time", {}).get("played", 0) or 0
    liga_id    = jogo.get("tournament", {}).get("uniqueTournament", {}).get("id", 0)
    liga_nome  = LIGAS.get(liga_id, jogo.get("tournament", {}).get("name", ""))
    importante = eh_jogo_importante(time_casa, time_fora)

    if jogo_id not in alertas_enviados:
        alertas_enviados[jogo_id] = set()
    enviados = alertas_enviados[jogo_id]

    stats = estatisticas(jogo_id)
    if not stats:
        return

    sc = calcular_scores(stats, minuto, gols_c, gols_f)

    cabec = (
        f"{'⭐ ' if importante else ''}"
        f"<b>{time_casa}  {gols_c}–{gols_f}  {time_fora}</b>\n"
        f"🏆 {liga_nome}  |  ⏱ {minuto}'\n"
    )

    stats_resumo = (
        f"\n📈 <b>Stats:</b> {sc['total_chutes']} chutes "
        f"({sc['chutes_gol']} a gol)  |  "
        f"⛳ {sc['escanteios']} esc  |  "
        f"💥 {sc['atq_perigosos']} atq peri"
    )

    # ── SINAL: OVER 0.5 HT ──────────────────────────────────────────
    if sc["over_ht"] >= OVER_HT_SCORE_MIN and minuto <= OVER_HT_JANELA_MAX:
        chave = f"over_ht_{minuto // 5}"
        if chave not in enviados:
            msg = (
                f"🔴 SINAL — OVER 0.5 HT  {label_forca(sc['over_ht'])}\n"
                + cabec +
                f"\n{barra(sc['over_ht'])} {sc['over_ht']}/100\n"
                f"\n🟡 Jogo 0x0 mas muito ABERTO até o 1T!"
                f"\n🎯 Entrada: OVER 0.5 HT  (feche se sair 1 gol)"
                + stats_resumo
            )
            enviar(msg)
            enviados.add(chave)

    # ── SINAL: OVER 2T (65+ min) ─────────────────────────────────────
    if sc["over_2t"] >= OVER_2T_SCORE_MIN and minuto >= OVER_2T_MINUTO_MIN:
        gols_total = gols_c + gols_f
        chave = f"over_2t_{minuto // 5}"
        if chave not in enviados:
            mercado = "OVER 0.5 2T" if gols_total == 0 else f"OVER {gols_total + 0.5}"
            msg = (
                f"🟠 SINAL — {mercado}  {label_forca(sc['over_2t'])}\n"
                + cabec +
                f"\n{barra(sc['over_2t'])} {sc['over_2t']}/100\n"
                f"\n🔥 Pressão alta no 2T — placar ainda baixo!"
                f"\n🎯 Entrada: {mercado}  "
                f"({'busca do empate' if gols_c != gols_f else 'jogo equilibrado'})"
                + stats_resumo
            )
            enviar(msg)
            enviados.add(chave)

    # ── SINAL: UNDER scalping ────────────────────────────────────────
    if sc["under"] >= UNDER_SCORE_MIN:
        # Não emite under se o jogo já virou carnival (muitos chutes)
        if sc["total_chutes"] <= UNDER_CHUTES_MAX + 3:
            # Agrupa em janelas de 10 minutos para não repetir demais
            chave = f"under_{minuto // 10}"
            if chave not in enviados:
                gols_total = gols_c + gols_f
                mercado_u = f"UNDER {gols_total + 0.5}" if gols_total > 0 else "UNDER 0.5 / 1.5"
                estilo = (
                    "Entrada cedo — odd ainda baixa, trava aqui"
                    if minuto < 30 else
                    "Scalping — placar parado, odd valorizada"
                    if minuto < 65 else
                    "CASH OUT rápido — jogo morto mas tarde"
                )
                msg = (
                    f"🔵 SINAL — {mercado_u}  {label_forca(sc['under'])}\n"
                    + cabec +
                    f"\n{barra(sc['under'])} {sc['under']}/100\n"
                    f"\n🧊 Jogo MORTO — pouquíssimo perigo!"
                    f"\n🎯 {estilo}"
                    + stats_resumo
                )
                enviar(msg)
                enviados.add(chave)


# ═══════════════════════════════════════════════
#   🔄  CICLO PRINCIPAL
# ═══════════════════════════════════════════════

def ciclo():
    agora = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{agora}] 🔍 Escaneando jogos ao vivo…")

    jogos = jogos_ao_vivo()
    ids_ligas = set(LIGAS.keys())

    filtrados = [
        j for j in jogos
        if j.get("tournament", {}).get("uniqueTournament", {}).get("id") in ids_ligas
    ]

    print(f"  → {len(filtrados)} jogos nas ligas mon