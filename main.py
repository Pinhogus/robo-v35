import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# =========================
# CONFIG — preencha aqui
# =========================
TOKEN = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

# =========================
# 1. PEGAR JOGOS (SCRAPING)
# =========================
def pegar_jogos():
    """
    Busca jogos do dia no soccerstats.com.
    Retorna lista de dicts com liga, home, away.
    """
    url = "https://www.soccerstats.com/matches.asp"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = "utf-8"  # FIX: encoding explícito
    except requests.RequestException as e:
        print(f"Erro de conexão: {e}")
        return []

    if response.status_code != 200:
        print(f"Erro HTTP {response.status_code} ao acessar site")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jogos = []
    vistos = set()

    tabelas = soup.find_all("table")

    if not tabelas:
        print("Nenhuma tabela encontrada no HTML")
        return []

    for tabela in tabelas:
        rows = tabela.find_all("tr")

        for row in rows:
            cols = row.find_all("td")

            # FIX: tenta múltiplas combinações de colunas
            pares_tentativa = [
                (2, 4),   # estrutura original
                (1, 3),   # estrutura alternativa
                (0, 2),   # estrutura compacta
            ]

            for col_home, col_away in pares_tentativa:
                if len(cols) > max(col_home, col_away):
                    try:
                        time1 = cols[col_home].text.strip()
                        time2 = cols[col_away].text.strip()

                        # FIX: filtros mais robustos
                        if (
                            time1
                            and time2
                            and len(time1) > 2
                            and len(time2) > 2
                            and not any(
                                lixo in time1.lower()
                                for lixo in ["vs", "home", "away", "time", "team", "-"]
                            )
                            and time1.replace(" ", "").isalpha() is False  # aceita nomes com números
                            or (len(time1) > 3 and len(time2) > 3)
                        ):
                            chave = time1 + "|" + time2
                            if chave not in vistos:
                                vistos.add(chave)
                                jogos.append({
                                    "liga": "Internacional",
                                    "home": time1,
                                    "away": time2
                                })
                            break  # achou par válido, não tenta mais combos
                    except Exception:
                        continue

    print(f"  → {len(jogos)} jogos únicos extraídos")
    return jogos


# =========================
# 2. BUSCAR STATS REAIS (API-Football via RapidAPI)
# =========================
# OPCIONAL: se você tiver chave RapidAPI, descomente e preencha
# RAPIDAPI_KEY = "SUA_CHAVE_AQUI"

def buscar_stats_reais(home: str, away: str) -> dict:
    """
    Placeholder para integração com API real.
    Substitua pelo endpoint da sua API de stats.
    Atualmente retorna valores neutros fixos como base.
    """
    # Exemplo de chamada real (requer RapidAPI):
    # url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics"
    # ...
    return {
        "media_gols": 2.5,
        "over25": 55,
        "under25": 55,
        "media_ultimos5": 2.5,
        "fonte": "base_neutra"
    }


# =========================
# 3. ADICIONAR MÉTRICAS
# =========================
def adicionar_stats(jogos: list) -> list:
    """
    Adiciona métricas a cada jogo.
    Tenta buscar stats reais; usa base neutra se falhar.
    """
    for j in jogos:
        try:
            stats = buscar_stats_reais(j["home"], j["away"])
            j.update(stats)
        except Exception as e:
            print(f"  ⚠ Erro ao buscar stats de {j['home']} x {j['away']}: {e}")
            j["media_gols"] = 2.5
            j["over25"] = 55
            j["under25"] = 55
            j["media_ultimos5"] = 2.5
            j["fonte"] = "fallback"

    return jogos


# =========================
# 4. SCORING
# =========================
def score_under(j: dict) -> int:
    """Pontua jogos com perfil UNDER 2.5."""
    score = 0

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


def score_over(j: dict) -> int:
    """Pontua jogos com perfil OVER 2.5."""
    score = 0

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


# =========================
# 5. RANKING
# =========================
def rankear(jogos: list) -> tuple:
    """
    Calcula scores e retorna top 10 under e top 10 over.
    FIX: filtra jogos sem score mínimo (score > 0).
    """
    for j in jogos:
        j["score_under"] = score_under(j)
        j["score_over"] = score_over(j)

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


# =========================
# 6. MONTAR MENSAGEM
# =========================
def montar_mensagem(top_under: list, top_over: list) -> str:
    """Monta a mensagem formatada para o Telegram."""

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


# =========================
# 7. ENVIAR TELEGRAM — FIX: async/await correto
# =========================
async def enviar_async(msg: str):
    """
    FIX PRINCIPAL: python-telegram-bot v20+ é 100% assíncrono.
    A versão antiga usava bot.send_message() direto (síncrono),
    o que causa RuntimeError nas versões novas.
    """
    try:
        async with Bot(token=TOKEN) as bot:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=msg,
                parse_mode=ParseMode.MARKDOWN
            )
        print("✅ Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar para o Telegram: {e}")


def enviar(msg: str):
    """Wrapper síncrono para chamar a função async."""
    asyncio.run(enviar_async(msg))


# =========================
# MAIN
# =========================
def main():
    print("🔍 Buscando jogos...")
    jogos = pegar_jogos()
    print(f"📋 {len(jogos)} jogos encontrados")

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


if __name__ == "__main__":
    main()
