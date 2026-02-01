import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "7955026793:AAFJUjGWEpm5BG_VHqsHRrQ4nDNroWT5Kz0"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

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

# ================= CONTROLE DE DADOS =================
avisados_gols = set()
sinais_gols = {}
resultados_gols = []

avisados_cantos = set()
memoria_cantos = {} 
ultimo_total_cantos = {} 
resultados_cantos = []
ultimo_dia = datetime.now().date()

# ================= FUNÇÕES AUXILIARES =================
def historico_ht(team_id):
    try:
        r = requests.get(
            f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10",
            headers=HEADERS, timeout=10
        ).json()["response"]
        gols = sum(1 for j in r if (j["score"]["halftime"]["home"] or 0) + (j["score"]["halftime"]["away"] or 0) > 0)
        return (gols / len(r)) * 100 if r else 0
    except: return 0

# ================= INÍCIO =================
print("🚀 Robô GOLS + CANTOS (Filtro Placar + Janelas Fixas) iniciado")

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
            home, away = f["teams"]["home"], f["teams"]["away"]
            liga, pais = f["league"]["name"], f["league"]["country"]
            
            gh = f["goals"]["home"] or 0
            ga = f["goals"]["away"] or 0

            # ========== LÓGICA DE GOLS HT (22' ao 35') ==========
            if 22 <= minuto <= 35 and gh == 0 and ga == 0:
                if fid not in avisados_gols:
                    ph, pa = historico_ht(home["id"]), historico_ht(away["id"])
                    if ph >= 80 or pa >= 80:
                        telegram(f"⚽ *SINAL: GOL HT*\n\n🏟️ {home['name']} x {away['name']}\n🌍 {pais} | 🏆 {liga}\n⏰ {minuto}' min | 0x0\n📊 Histórico HT: {max(ph, pa):.0f}%")
                        sinais_gols[fid] = {"liga": liga, "pais": pais}
                        avisados_gols.add(fid)

            # ========== LÓGICA DE CANTOS (Janelas Fixas + Pressão + Placar) ==========
            # Verificamos se está nas janelas: 33-42 ou 80-88
            no_tempo_canto = (33 <= minuto <= 42) or (80 <= minuto <= 88)

            if no_tempo_canto:
                stats_req = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=HEADERS, timeout=10).json()["response"]
                
                # Pegamos cantos separados por time para ver quem está pressionando
                c_home = 0
                c_away = 0
                for t in stats_req:
                    val = next((s["value"] for s in t["statistics"] if s["type"] == "Corner Kicks"), 0) or 0
                    if t["team"]["id"] == home["id"]: c_home = val
                    else: c_away = val
                
                total_atual = c_home + c_away

                if fid not in ultimo_total_cantos:
                    ultimo_total_cantos[fid] = total_atual
                    memoria_cantos[fid] = []
                
                if total_atual > ultimo_total_cantos[fid]:
                    for _ in range(total_atual - ultimo_total_cantos[fid]):
                        memoria_cantos[fid].append(minuto)
                    ultimo_total_cantos[fid] = total_atual

                # Filtra os últimos 10 minutos
                memoria_cantos[fid] = [m for m in memoria_cantos[fid] if m > (minuto - 10)]

                # VERIFICAÇÃO DE SINAL
                if len(memoria_cantos[fid]) >= 3 and fid not in avisados_cantos:
                    # Lógica de Placar: O time com mais cantos não pode estar vencendo
                    alerta = False
                    if c_home > c_away and gh <= ga: alerta = True # Casa pressiona e não vence
                    elif c_away > c_home and ga <= gh: alerta = True # Fora pressiona e não vence
                    
                    if alerta:
                        telegram(
                            f"🚩 *SINAL: PRESSÃO (CANTOS)*\n\n"
                            f"🏟️ {home['name']} x {away['name']}\n"
                            f"🌍 {pais} | 🏆 {liga}\n"
                            f"⏰ Tempo: {minuto}' min | Placar: {gh}x{ga}\n"
                            f"📈 Pressão: {len(memoria_cantos[fid])} cantos nos últimos 10'"
                        )
                        avisados_cantos.add(fid)

            # Limpeza
            if status in ["HT", "FT"]:
                if status == "HT" and fid in sinais_gols:
                    del sinais_gols[fid] # Para não repetir sinal no 2º tempo se já avisou
                if status == "FT":
                    avisados_cantos.discard(fid)
                    memoria_cantos.pop(fid, None)
                    ultimo_total_cantos.pop(fid, None)

        time.sleep(120) 

    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(60)
