import streamlit as st
import requests
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Meu Painel do Strava", page_icon="🏃", layout="wide")

st.title("🏃 Painel de Treinos e Corridas")
st.write("Acompanhe sua evolução, volume acumulado e ritmo de corrida.")

# Sidebar para credenciais
st.sidebar.header("🔑 Configuração Strava")
client_id = st.sidebar.text_input("Client ID")
client_secret = st.sidebar.text_input("Client Secret", type="password")
auth_code = st.sidebar.text_input("Código de Autorização (Obtido no Passo 2)", type="password")

@st.cache_data(ttl=3600)
def get_tokens(c_id, c_secret, code):
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': c_id,
        'client_secret': c_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        return res.json().get('access_token')
    return None

if client_id and client_secret and auth_code:
    access_token = get_tokens(client_id, client_secret, auth_code)
    
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=50", headers=headers)
        
        if res.status_code == 200:
            activities = res.json()
            runs = [a for a in activities if a.get('type') == 'Run']
            
            if runs:
                data = []
                for r in runs:
                    dist_km = r['distance'] / 1000
                    time_min = r['moving_time'] / 60
                    pace_decimal = time_min / dist_km if dist_km > 0 else 0
                    p_min = int(pace_decimal)
                    p_sec = int((pace_decimal - p_min) * 60)
                    
                    data.append({
                        "Data": r['start_date_local'][:10],
                        "Nome": r['name'],
                        "Distância (km)": round(dist_km, 2),
                        "Tempo (min)": round(time_min, 1),
                        "Pace Médio": f"{p_min}:{p_sec:02d} /km",
                        "Elevação (m)": r.get('total_elevation_gain', 0)
                    })
                
                df = pd.DataFrame(data)
                
                # Métricas Principais
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Corridas", len(df))
                col2.metric("Distância Acumulada", f"{df['Distância (km)'].sum():.1f} km")
                col3.metric("Maior Distância", f"{df['Distância (km)'].max():.1f} km")
                
                st.markdown("---")
                
                # Gráfico de evolução
                st.subheader("📊 Volume de Distância por Treino")
                st.bar_chart(df, x="Data", y="Distância (km)")
                
                # Tabela detalhada
                st.subheader("📋 Histórico Recente de Treinos")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Nenhuma atividade de corrida encontrada no histórico recente.")
        else:
            st.error("Não foi possível carregar os dados. Verifique se o código expirou.")
    else:
        st.error("Erro ao autenticar no Strava. Verifique seu Client ID, Client Secret e Código.")
else:
    st.info("Insira seu Client ID, Client Secret e o Código de Autorização no menu lateral esquerdo para carregar seus dados.")