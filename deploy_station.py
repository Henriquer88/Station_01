import streamlit as st
import pandas as pd
import requests
import time

# ===========================================
# CONFIGURAÇÕES INICIAIS
# ===========================================
st.set_page_config(
    page_title="Dashboard Estações Meteorológicas",
    page_icon="🌦️",
    layout="wide"
)

urls = [
    "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/1",
    "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/2",
    "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/3",
    "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/4",
    "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/5"
]

REFRESH_INTERVAL = 60  # segundos


# ===========================================
# FUNÇÃO PARA BUSCAR OS DADOS
# ===========================================
@st.cache_data(ttl=REFRESH_INTERVAL)
def get_estacoes_data():
    data = []
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                json_data = response.json().get("arrResponse", {})
                data.append(json_data)
        except Exception as e:
            st.warning(f"Erro ao acessar {url}: {e}")
    return pd.DataFrame(data)


# ===========================================
# DASHBOARD
# ===========================================
st.title("🌦️ Estações Meteorológicas - Eletromidia")
st.markdown("Dados obtidos automaticamente via API IOT Hub")

# Atualização automática
with st.spinner("Atualizando dados..."):
    df = get_estacoes_data()

if not df.empty:
    # Converter colunas numéricas
    def to_float(s):
        if isinstance(s, str):
            s = s.split(" ")[0].replace(",", ".")
        try:
            return float(s)
        except:
            return None

    df["Temperatura (°C)"] = df["Temperatura"].apply(to_float)
    df["Umidade (%)"] = df["Umidade"].apply(to_float)
    df["Pressão (hPa)"] = df["Pressão Atmosférica"].apply(to_float)
    df["Chuva (mm)"] = df["Chuva"].apply(to_float)
    df["Ruído (dB)"] = df["Ruído"].apply(to_float)

    # ===========================================
    # MÉTRICAS RESUMIDAS
    # ===========================================
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🌡️ Temperatura Média", f"{df['Temperatura (°C)'].mean():.1f} °C")
    col2.metric("💧 Umidade Média", f"{df['Umidade (%)'].mean():.1f} %")
    col3.metric("🌪️ Pressão Média", f"{df['Pressão (hPa)'].mean():.1f} hPa")
    col4.metric("🌧️ Chuva Total", f"{df['Chuva (mm)'].sum():.1f} mm")
    col5.metric("🔊 Ruído Médio", f"{df['Ruído (dB)'].mean():.1f} dB")

    st.divider()

    # ===========================================
    # TABELA DETALHADA
    # ===========================================
    st.subheader("📊 Leituras Detalhadas das Estações")
    st.dataframe(
        df[
            [
                "nome",
                "Última Leitura",
                "Temperatura",
                "Umidade",
                "Pressão Atmosférica",
                "Chuva",
                "Ruído",
                "Luminosidade",
                "Vento",
                "Direção do Vento",
                "Partículas por Milhão 2.5",
                "Partículas por Milhão 10",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    # ===========================================
    # GRÁFICOS
    # ===========================================
    st.subheader("📈 Visualização Gráfica")

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(df.set_index("nome")["Temperatura (°C)"])
    with col2:
        st.bar_chart(df.set_index("nome")["Umidade (%)"])

    st.bar_chart(df.set_index("nome")[["Chuva (mm)", "Ruído (dB)"]])

else:
    st.error("Não foi possível obter dados das estações.")

# Rodapé
st.caption(f"Atualiza automaticamente a cada {REFRESH_INTERVAL} segundos.")
