import requests
import urllib.parse
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
API_KEY = "9478a34c4d9fb4cc6d18861a304bdf18"
TOKEN_TELEGRAM = "8418160843:AAElU7KJsdQ0MtzhP8-EFMLNjX4zvIjEWSY"
CHAT_ID = "1027866106"
HEADERS = {'x-apisports-key': API_KEY}

# --- CONTROLE DE ESTADOS (RESETAM DIARIAMENTE) ---
jogos_avisados_gols = set()
jogos_rejeitados_gols = set() 
jogos_avisados_cantos = set()
cache_historico = {}
data_atual = datetime.now().date()

def limpar_valor(valor):
    try: return int(valor) if valor is not None else 0
    except: return 0

def verificar_historico_ht(team_id):
    if team_id in cache_historico:
        return cache_historico[team_id]
    
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10&status=FT"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        jogos = res.get('response', [])
        if not jogos: return 0
        gols_ht = sum(1 for j in jogos if (limpar_valor(j.get('score', {}).get('halftime', {}).get('home')) + 
                                            limpar_valor(j.get('score', {}).get('halftime', {}).get('away'))) > 0)
        percentual = (gols_ht / len(jogos)) * 100
        cache_historico[team_id] = percentual
        return percentual
    except: return 0

def enviar_telegram(mensagem):
    texto = urllib.parse.quote(mensagem)
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={texto}&parse_mode=Markdown"
    try: requests.get(url, timeout=10)
    except: print("❌ Erro ao enviar Telegram")

print(f"🚀 Robô Ativado! Data: {data_atual}")

while True:
    try:
        # --- RESET DIÁRIO ---
        agora = datetime.now().date()
        if agora > data_atual:
            print(f"🧹 Virada de dia detectada ({agora}). Limpando memórias...")
            jogos_avisados_gols.clear()
            jogos_rejeitados_gols.clear()
            jogos_avisados_cantos.clear()
            cache_historico.clear()
            data_atual = agora

        url_live = "https://v3.football.api-sports.io/fixtures?live=all"
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        
        print(f"📊 Varredura: {len(jogos)} jogos | {time.strftime('%H:%M:%S')}")

        for fixture in jogos:
            m_id = fixture['fixture']['id']
            minuto = fixture.get('fixture', {}).get('status', {}).get('elapsed') or 0
            g_h = limpar_valor(fixture.get('goals', {}).get('home'))
            g_a = limpar_valor(fixture.get('goals', {}).get('away'))
            nome_h = fixture['teams']['home']['name']
            nome_a = fixture['teams']['away']['name']

            # --- ESTRATÉGIA GOLS HT ---
            if 20 <= minuto <= 35 and (g_h + g_a) == 0:
                if m_id not in jogos_avisados_gols and m_id not in jogos_rejeitados_gols:
                    id_h = fixture['teams']['home']['id']
                    id_a = fixture['teams']['away']['id']
                    
                    perc_h = verificar_historico_ht(id_h)
                    time.sleep(0.6) # Evitar spam na API
                    perc_a = verificar_historico_ht(id_a)
                    
                    if perc_h >= 80 or perc_a >= 80:
                        msg = (f"⚽ *GOL HT: ODD 1.50+*\n\n"
                               f"🏟️ {nome_h} x {nome_a}\n"
                               f"⏱️ Tempo: {minuto}' | 🥅 0x0\n"
                               f"📊 Histórico HT: {max(perc_h, perc_a):.0f}%\n"
                               f"💰 Sugestão: Over 0.5 HT")
                        enviar_telegram(msg)
                        jogos_avisados_gols.add(m_id)
                    else:
                        print(f"🚫 Ignorando {nome_h} x {nome_a} hoje (Histórico HT baixo)")
                        jogos_rejeitados_gols.add(m_id)

            # --- ESTRATÉGIA CANTOS (PRESSÃO) ---
            alvo = 5 if minuto <= 45 else (10 if 46 <= minuto <= 90 else 0)
            
            if alvo > 0:
                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={m_id}"
                stats_res = requests.get(stats_url, headers=HEADERS).json()
                stats_data = stats_res.get('response', [])

                if len(stats_data) >= 2:
                    s_home = {s['type']: s['value'] for s in stats_data[0].get('statistics', [])}
                    s_away = {s['type']: s['value'] for s in stats_data[1].get('statistics', [])}
                    
                    c_h = limpar_valor(s_home.get('Corner Kicks'))
                    c_a = limpar_valor(s_away.get('Corner Kicks'))
                    
                    msg_canto = ""
                    # Casa empatando/perdendo e >5 ou >10 cantos
                    if g_h <= g_a and c_h > alvo and f"{m_id}_h_{alvo}" not in jogos_avisados_cantos:
                        msg_canto = (f"🚩 *PRESSÃO: CANTOS CASA*\n"
                                     f"🏟️ {nome_h} x {nome_a}\n"
                                     f"⏱️ {minuto}' | 🥅 {g_h}x{g_a}\n"
                                     f"📈 Cantos Casa: {c_h}\n"
                                     f"🎯 Alvo: >{alvo} no {'1ºT' if alvo==5 else '2ºT'}")
                        jogos_avisados_cantos.add(f"{m_id}_h_{alvo}")

                    # Visitante empatando/perdendo e >5 ou >10 cantos
                    elif g_a <= g_h and c_a > alvo and f"{m_id}_a_{alvo}" not in jogos_avisados_cantos:
                        msg_canto = (f"🚩 *PRESSÃO: CANTOS FORA*\n"
                                     f"🏟️ {nome_h} x {nome_a}\n"
                                     f"⏱️ {minuto}' | 🥅 {g_h}x{g_a}\n"
                                     f"📈 Cantos Fora: {c_a}\n"
                                     f"🎯 Alvo: >{alvo} no {'1ºT' if alvo==5 else '2ºT'}")
                        jogos_avisados_cantos.add(f"{m_id}_a_{alvo}")

                    if msg_canto:
                        enviar_telegram(msg_canto)
                
                time.sleep(1) # Delay para respeitar limite da API

    except Exception as e:
        print(f"⚠️ Erro: {e}")
    
    time.sleep(180) # Varredura a cada 3 minutos
