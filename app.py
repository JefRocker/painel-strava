import streamlit as st
import requests
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Meu Painel do Strava", page_icon="🏃", layout="wide")

st.title("🏃 Painel de Treinos e Corridas")
st.write("Acompanhe a sua evolução, volume acumulado e ritmo de corrida.")

# Tenta ler as credenciais salvas nos Secrets do Streamlit Cloud
client_id = st.secrets.get("CLIENT_ID", "")
client_secret = st.secrets.get("CLIENT_SECRET", "")
refresh_token = st.secrets.get("REFRESH_TOKEN", "")

# Função para renovar o access_token automaticamente usando o refresh_token
def get_access_token_from_refresh(c_id, c_secret, r_token):
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': c_id,
        'client_secret': c_secret,
        'refresh_token': r_token,
        'grant_type': 'refresh_token'
    }
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        return res.json().get('access_token')
    return None

# Função para a troca inicial do código temporário
def exchange_code_for_tokens(c_id, c_secret, code):
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': c_id,
        'client_secret': c_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        return res.json()
    return None

access_token = None

# Se já houver um Refresh Token configurado nos Secrets, usa-o diretamente
if client_id and client_secret and refresh_token:
    access_token = get_access_token_from_refresh(client_id, client_secret, refresh_token)
else:
    # Interface manual temporária para obter o Refresh Token
    st.sidebar.header("🔑 Configuração Strava")
    input_c_id = st.sidebar.text_input("Client ID", value=str(client_id) if client_id else "")
    input_c_secret = st.sidebar.text_input("Client Secret", value=client_secret, type="password")
    auth_code = st.sidebar.text_input("Código de Autorização", type="password")

    if input_c_id and input_c_secret and auth_code:
        tokens_data = exchange_code_for_tokens(input_c_id, input_c_secret, auth_code)
        if tokens_data:
            access_token = tokens_data.get('access_token')
            rec_refresh_token = tokens_data.get('refresh_token')
            st.sidebar.success("Autenticado com sucesso!")
            st.sidebar.info(f"**Copie o seu Refresh Token abaixo:**\n\n`{rec_refresh_token}`")
        else:
            st.sidebar.error("Erro ao autenticar. Verifique se o código expirou.")

if access_token:
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=100", headers=headers)

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

            # Métricas
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Corridas", len(df))
            col2.metric("Distância Acumulada", f"{df['Distância (km)'].sum():.1f} km")
            col3.metric("Maior Distância", f"{df['Distância (km)'].max():.1f} km")

            st.markdown("---")

            # Gráficos
            st.subheader("📊 Volume de Distância por Treino")
            st.bar_chart(df, x="Data", y="Distância (km)")

            st.subheader("📋 Histórico Recente de Treinos")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Nenhuma atividade de corrida encontrada no histórico recente.")
    else:
        st.error("Não foi possível carregar os dados do Strava.")
else:
    if not (client_id and client_secret and refresh_token):
        st.info("Insira as suas credenciais no menu lateral para gerar o seu Refresh Token.")
