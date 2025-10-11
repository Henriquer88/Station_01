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
    col4.metric("🌧️ Chuva Média", f"{df['Chuva (mm)'].mean():.1f} mm")
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
# GRÁFICOS INTERATIVOS COMPLETOS (PLOTLY)
# ===========================================
import plotly.graph_objects as go
import plotly.express as px

st.header("📊 Visualização Completa das Medições")

# -------- Temperatura --------
st.subheader("🌡️ Temperatura por Estação")
fig_temp = px.bar(
    df,
    x="nome",
    y="Temperatura (°C)",
    color="Temperatura (°C)",
    color_continuous_scale="RdYlBu_r",
    text="Temperatura (°C)",
)
fig_temp.update_traces(texttemplate="%{text:.1f}°C", textposition="outside")
fig_temp.update_layout(
    title="Distribuição de Temperatura (°C)",
    yaxis_title="Temperatura (°C)",
    xaxis_title="Estação",
    title_x=0.5,
    height=420,
)
st.plotly_chart(fig_temp, use_container_width=True)

# -------- Umidade --------
st.subheader("💧 Umidade Relativa")
fig_umid = px.bar(
    df,
    x="nome",
    y="Umidade (%)",
    color="Umidade (%)",
    color_continuous_scale="Blues",
    text="Umidade (%)",
)
fig_umid.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_umid.update_layout(
    title="Distribuição de Umidade (%)",
    yaxis_title="Umidade (%)",
    xaxis_title="Estação",
    title_x=0.5,
    height=420,
)
st.plotly_chart(fig_umid, use_container_width=True)

# -------- Pressão Atmosférica --------
st.subheader("🌪️ Pressão Atmosférica")
fig_press = px.bar(
    df,
    x="nome",
    y="Pressão (hPa)",
    color="Pressão (hPa)",
    color_continuous_scale="Viridis",
    text="Pressão (hPa)",
)
fig_press.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig_press.update_layout(
    title="Pressão Atmosférica (hPa)",
    yaxis_title="Pressão (hPa)",
    xaxis_title="Estação",
    title_x=0.5,
    height=420,
)
st.plotly_chart(fig_press, use_container_width=True)

# -------- Chuva --------
st.subheader("🌧️ Índice de Chuva")
fig_chuva = px.bar(
    df,
    x="nome",
    y="Chuva (mm)",
    color="Chuva (mm)",
    color_continuous_scale="Blues_r",
    text="Chuva (mm)",
)
fig_chuva.update_traces(texttemplate="%{text:.1f} mm", textposition="outside")
fig_chuva.update_layout(
    title="Precipitação (mm)",
    yaxis_title="Chuva (mm)",
    xaxis_title="Estação",
    title_x=0.5,
    height=420,
)
st.plotly_chart(fig_chuva, use_container_width=True)

# -------- Luminosidade --------
st.subheader("💡 Luminosidade (lux)")
fig_lux = px.bar(
    df,
    x="nome",
    y="Luminosidade",
    color="Luminosidade",
    color_continuous_scale="YlOrBr",
    text="Luminosidade",
)
fig_lux.update_traces(texttemplate="%{text}", textposition="outside")
fig_lux.update_layout(
    title="Luminosidade (lux)",
    yaxis_title="Luminosidade (lux)",
    xaxis_title="Estação",
    title_x=0.5,
    height=420,
)
st.plotly_chart(fig_lux, use_container_width=True)

# -------- Vento --------
st.subheader("🌬️ Velocidade do Vento e Direção")
fig_vento = go.Figure()
fig_vento.add_trace(go.Bar(
    x=df["nome"],
    y=df["Vento"].apply(lambda x: float(str(x).split(" ")[0])),
    name="Velocidade (m/s)",
    marker_color="skyblue",
    text=df["Vento"],
    textposition="outside"
))
fig_vento.add_trace(go.Scatter(
    x=df["nome"],
    y=df["Direção do Vento"].apply(lambda x: float(str(x).split(" ")[0])),
    name="Direção (°)",
    mode="lines+markers",
    line=dict(color="orange", width=3),
))
fig_vento.update_layout(
    title="Velocidade e Direção do Vento",
    yaxis_title="Velocidade / Direção",
    xaxis_title="Estação",
    title_x=0.5,
    height=450,
)
st.plotly_chart(fig_vento, use_container_width=True)

# -------- Partículas --------
st.subheader("🌫️ Material Particulado (PM2.5 / PM10)")
df_part = df.melt(
    id_vars=["nome"],
    value_vars=["Partículas por Milhão 2.5", "Partículas por Milhão 10"],
    var_name="Tipo",
    value_name="µg/m³",
)
fig_pm = px.bar(
    df_part,
    x="nome",
    y="µg/m³",
    color="Tipo",
    barmode="group",
    text="µg/m³",
    color_discrete_sequence=["#4B9CD3", "#A06CD5"],
)
fig_pm.update_traces(texttemplate="%{text}", textposition="outside")
fig_pm.update_layout(
    title="Concentração de Partículas (µg/m³)",
    yaxis_title="µg/m³",
    xaxis_title="Estação",
    title_x=0.5,
    height=450,
)
st.plotly_chart(fig_pm, use_container_width=True)

# -------- Ruído --------
st.subheader("🔊 Nível de Ruído")
fig_ruido = px.bar(
    df,
    x="nome",
    y="Ruído (dB)",
    color="Ruído (dB)",
    color_continuous_scale="OrRd",
    text="Ruído (dB)",
)
fig_ruido.update_traces(texttemplate="%{text:.1f} dB", textposition="outside")
fig_ruido.update_layout(
    title="Nível de Ruído (dB)",
    yaxis_title="Ruído (dB)",
    xaxis_title="Estação",
    title_x=0.5,
    height=420,
)
st.plotly_chart(fig_ruido, use_container_width=True)
