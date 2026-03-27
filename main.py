import requests
from bs4 import BeautifulSoup
import asyncio
import re
from urllib.parse import unquote
from telegram import Bot
from telegram.constants import ParseMode

# =========================
# CONFIG — preencha aqui
# =========================
TOKEN = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"

# =========================
# 1. HELPERS DE LIMPEZA
# =========================
def limpar_nome_time(texto: str) -> str:
    """
    Remove lixo comum que vem do scraping do soccerstats:
    - Caracteres URL-encoded (%58, %42 etc.)
    - Números soltos, porcentagens, estatísticas coladas
    - Espaços duplicados
    """
    if not texto:
        return ""

    # Decodifica URL encoding (%58 → X etc.)
    try:
        texto = unquote(texto)
    except Exception:
        pass

    # Remove tudo que não seja letra, espaço ou hífen (nomes compostos)
    texto = re.sub(r"[^a-zA-ZÀ-ÿ\s\-\.]", " ", texto)

    # Remove espaços múltiplos
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def nome_valido(nome: str) -> bool:
    """
    Valida se o texto extraído parece ser um nome de time real.
    Rejeita: muito curto, só números, palavras de cabeçalho de tabela,
    texto longo demais (provavelmente lixo concatenado).
    """
    PALAVRAS_LIXO = {
        "home", "away", "team", "time", "match", "date", "score",
        "stats", "goals", "played", "points", "league", "vs",
        "scope", "blog", "today", "mon", "tue", "wed", "thu",
        "fri", "sat", "sun", "per", "game"
    }

    if not nome:
        return False

    # Tamanho: times reais têm entre 3 e 35 caracteres
    if len(nome) < 3 or len(nome) > 35:
        return False

    # Não pode ser só números ou símbolos
    letras = re.sub(r"[^a-zA-ZÀ-ÿ]", "", nome)
    if len(letras) < 3:
        return False

    # Não pode ser uma palavra de cabeçalho conhecida
    if nome.lower().strip() in PALAVRAS_LIXO:
        return False

    # Não pode conter % ou sequências numéricas longas (lixo de stats)
    if "%" in nome or re.search(r"\d{3,}", nome):
        return False

    return True


# =========================
# 2. PEGAR JOGOS (SCRAPING)
# =========================
def pegar_jogos():
    """
    Busca jogos do dia no soccerstats.com.
    Estratégia: procura links com padrão de jogo (/match.asp?...)
    que é mais confiável que parsear células de tabela diretamente.
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
    liga_atual = "Internacional"

    # ── Estratégia 1: linhas de tabela com padrão "Time x Time" ──
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        # Tenta encontrar a coluna central com "x" ou "vs" separando os times
        # O soccerstats usa estrutura: [hora] [home] [x] [away] [...]
        for i in range(len(cols) - 2):
            separador = cols[i + 1].text.strip().lower()
            if separador in ("-", "x", "vs", "–", ""):
                candidato_home = limpar_nome_time(cols[i].text)
                candidato_away = limpar_nome_time(cols[i + 2].text)

                if nome_valido(candidato_home) and nome_valido(candidato_away):
                    chave = candidato_home + "|" + candidato_away
                    if chave not in vistos:
                        vistos.add(chave)
                        jogos.append({
                            "liga": liga_atual,
                            "home": candidato_home,
                            "away": candidato_away,
                        })
                    break

        # Detecta cabeçalho de liga (linha com colspan ou texto de liga)
        cabecalho = row.find("td", {"colspan": True})
        if cabecalho:
            txt = cabecalho.text.strip()
            if txt and len(txt) < 60 and not any(c.isdigit() for c in txt[:5]):
                liga_atual = txt.split("stats")[0].strip() or "Internacional"

    # ── Estratégia 2 (fallback): varredura sem separador central ──
    if not jogos:
        print("  ⚠ Estratégia 1 vazia, tentando varredura direta...")
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            # Tenta pares de colunas adjacentes
            for idx in range(len(cols) - 1):
                h = limpar_nome_time(cols[idx].text)
                a = limpar_nome_time(cols[idx + 1].text)
                if nome_valido(h) and nome_valido(a) and h != a:
                    chave = h + "|" + a
                    if chave not in vistos:
                        vistos.add(chave)
                        jogos.append({"liga": "Internacional", "home": h, "away": a})
                    break

    print(f"  → {len(jogos)} jogos válidos extraídos")
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
