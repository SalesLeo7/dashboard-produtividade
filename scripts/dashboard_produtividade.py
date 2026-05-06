import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Produtividade")

# =========================
# 📥 LOAD DATA
# =========================
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)

    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(" ", "_")
    )

    rename_dict = {
        "useruser_name": "user_name",
        "event_typeevent_type_name": "event_type_name",
        "time_event_datetime_hour_interval": "time_hour_interval",
        "calendar_event_datedate": "date",
        "event_count": "event_count",
        "event_elapsed_time_avg": "event_elapsed_time",
        "clientclient_id": "client_id"
    }

    df = df.rename(columns=rename_dict)

    return df

# =========================
# 📂 UPLOAD
# =========================
st.sidebar.title("Upload")

arquivo = st.sidebar.file_uploader("Selecione o Excel", type=["xlsx"])

if not arquivo:
    st.warning("Faça upload do arquivo")
    st.stop()

df = load_data(arquivo)

# =========================
# ⏱️ ORDENAR HORÁRIOS
# =========================
df["hora_inicio"] = df["time_hour_interval"].str.extract(r"(\d{2}:\d{2})")
df["hora_inicio"] = pd.to_datetime(df["hora_inicio"], format="%H:%M")

df["hora_fim"] = df["time_hour_interval"].str.extract(r"-(\d{2}:\d{2})")
df["hora_fim"] = pd.to_datetime(df["hora_fim"], format="%H:%M")

df = df.sort_values("hora_inicio")

# =========================
# 🎛️ FILTROS
# =========================
st.sidebar.title("Filtros")

usuarios = st.sidebar.multiselect("Usuário", df["user_name"].unique())
eventos = st.sidebar.multiselect("Evento", df["event_type_name"].unique())
clientes = st.sidebar.multiselect("Cliente", df["client_id"].unique())

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    datas = st.sidebar.date_input("Data", [])

    if datas:
        df = df[df["date"].isin(pd.to_datetime(datas))]

if usuarios:
    df = df[df["user_name"].isin(usuarios)]

if eventos:
    df = df[df["event_type_name"].isin(eventos)]

if clientes:
    df = df[df["client_id"].isin(clientes)]

# =========================
# 📊 KPIs
# =========================
k1, k2, k3, k4 = st.columns(4)

k1.metric("Eventos", int(df["event_count"].sum()))
k2.metric("Tempo Médio", round(df["event_elapsed_time"].mean(), 2))
k3.metric("Usuários", df["user_name"].nunique())
k4.metric("Pico", df.groupby("time_hour_interval")["event_count"].sum().idxmax())

st.divider()

# =========================
# 🔥 SCORE
# =========================
df_user = df.groupby("user_name").agg({
    "event_count": "sum",
    "event_elapsed_time": "mean"
}).reset_index()

df_user["score_volume"] = df_user["event_count"] / df_user["event_count"].max()
df_user["score_tempo"] = 1 - (df_user["event_elapsed_time"] / df_user["event_elapsed_time"].max())

df_user["score"] = df_user["score_volume"] * 0.6 + df_user["score_tempo"] * 0.4

# =========================
# 🎯 META
# =========================
META = st.sidebar.number_input("Meta", value=100)
df_user["%meta"] = df_user["event_count"] / META

# =========================
# 🧱 GARGALO
# =========================
gargalo = df.groupby("time_hour_interval")["event_count"].sum().reset_index()

media = gargalo["event_count"].mean()

gargalo["status"] = gargalo["event_count"].apply(
    lambda x: "🔥" if x > media * 1.5 else "🕳️" if x < media * 0.5 else "OK"
)

# =========================
# 📈 VOLUME
# =========================
st.subheader("Volume por Hora")

ordem = sorted(
    df["time_hour_interval"].unique(),
    key=lambda x: pd.to_datetime(x.split("-")[0], format="%H:%M")
)

fig = px.line(
    gargalo,
    x="time_hour_interval",
    y="event_count",
    category_orders={"time_hour_interval": ordem}
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# 🔥 HEATMAP
# =========================
pivot = df.pivot_table(
    index="user_name",
    columns="time_hour_interval",
    values="event_count",
    aggfunc="sum",
    fill_value=0
)

pivot = pivot[ordem]

st.subheader("Heatmap")

st.plotly_chart(px.imshow(pivot, aspect="auto"), use_container_width=True)

# =========================
# 🧑 RANKING
# =========================
st.subheader("Ranking")

st.plotly_chart(
    px.bar(df_user.sort_values("score", ascending=False),
           x="user_name", y="score"),
    use_container_width=True
)

# =========================
# 🧠 DETECÇÃO DE TURNO
# =========================
df_turno = df.copy()

df_turno["gap"] = df_turno.groupby("user_name")["hora_inicio"].diff()

df_turno["novo_bloco"] = (
    df_turno["gap"].isna() |
    (df_turno["gap"].dt.total_seconds() > 3600)
)

inicio = df_turno[df_turno["novo_bloco"]].groupby("user_name")["hora_inicio"].min().reset_index()
fim = df_turno.groupby("user_name")["hora_fim"].max().reset_index()

turno = inicio.merge(fim, on="user_name")
turno["duracao"] = (turno["hora_fim"] - turno["hora_inicio"]).dt.total_seconds() / 3600

st.subheader("Jornada dos Usuários")

turno_formatado = turno.copy()

turno_formatado["hora_inicio"] = turno_formatado["hora_inicio"].dt.strftime("%H:%M")
turno_formatado["hora_fim"] = turno_formatado["hora_fim"].dt.strftime("%H:%M")

st.dataframe(turno_formatado, use_container_width=True)

# =========================
# ⏳ TIMELINE
# =========================
st.subheader("Timeline")

usuario_timeline = st.selectbox("Usuário", df["user_name"].unique())

df_tl = df[df["user_name"] == usuario_timeline].copy()

fig_timeline = px.timeline(
    df_tl,
    x_start="hora_inicio",
    x_end="hora_fim",
    y="event_type_name",
    color="event_count"
)

fig_timeline.update_yaxes(autorange="reversed")

st.plotly_chart(fig_timeline, use_container_width=True)

# =========================
# 📋 BASE FINAL
# =========================
st.subheader("Base")

st.dataframe(df, use_container_width=True)
