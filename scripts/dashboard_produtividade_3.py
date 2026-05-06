"""
Dashboard de Produtividade — Tema Corporativo Dark (estilo Power BI)
Execute com: streamlit run dashboard_produtividade.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Produtividade",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# =========================================================
# 🎨 PALETA E TEMA (Power BI Dark)
# =========================================================
COLORS = {
    "bg":          "#0E1117",
    "bg_card":     "#161B22",
    "bg_card_2":   "#1C232C",
    "border":      "#2A323D",
    "text":        "#E6EDF3",
    "text_muted":  "#8B949E",
    "primary":     "#2EA8FF",   # azul Power BI
    "accent":      "#00D4B4",   # ciano/teal
    "warning":     "#F2B441",
    "danger":      "#F85149",
    "success":     "#3FB950",
}

PLOTLY_SEQ = ["#2EA8FF", "#00D4B4", "#F2B441", "#F85149", "#A371F7", "#3FB950", "#FF7B72"]
PLOTLY_HEAT = [
    [0.0, "#0E1117"],
    [0.2, "#0B2942"],
    [0.5, "#125E96"],
    [0.8, "#2EA8FF"],
    [1.0, "#7CC9FF"],
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_card"],
    plot_bgcolor=COLORS["bg_card"],
    font=dict(family="Segoe UI, Inter, sans-serif", color=COLORS["text"], size=13),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"]),
)

# =========================================================
# 💅 CSS CUSTOMIZADO
# =========================================================
st.markdown(f"""
<style>
    .stApp {{
        background: {COLORS["bg"]};
        color: {COLORS["text"]};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {COLORS["bg_card"]};
        border-right: 1px solid {COLORS["border"]};
    }}
    section[data-testid="stSidebar"] * {{ color: {COLORS["text"]} !important; }}

    /* Headings */
    h1, h2, h3, h4 {{
        color: {COLORS["text"]} !important;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        letter-spacing: -0.01em;
    }}

    /* KPI cards */
    div[data-testid="stMetric"] {{
        background: linear-gradient(145deg, {COLORS["bg_card"]} 0%, {COLORS["bg_card_2"]} 100%);
        border: 1px solid {COLORS["border"]};
        border-left: 3px solid {COLORS["primary"]};
        padding: 18px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        transition: transform .15s ease, box-shadow .15s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(46,168,255,0.18);
    }}
    div[data-testid="stMetricLabel"] p {{
        color: {COLORS["text_muted"]} !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        color: {COLORS["text"]} !important;
        font-size: 1.9rem !important;
        font-weight: 700 !important;
    }}

    /* Section titles */
    .section-title {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {COLORS["text"]};
        padding: 6px 0 10px 0;
        border-bottom: 1px solid {COLORS["border"]};
        margin: 8px 0 14px 0;
        display: flex; align-items: center; gap: 8px;
    }}
    .section-title .dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {COLORS["primary"]};
        box-shadow: 0 0 10px {COLORS["primary"]};
    }}

    /* Header banner */
    .header-banner {{
        background: linear-gradient(120deg, #0E1117 0%, #14253B 60%, #0E1117 100%);
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 22px 26px;
        margin-bottom: 18px;
        display: flex; flex-direction: column; gap: 4px;
    }}
    .header-banner h1 {{
        margin: 0; font-size: 1.6rem; font-weight: 700;
    }}
    .header-banner p {{
        margin: 0; color: {COLORS["text_muted"]}; font-size: 0.9rem;
    }}

    /* Dataframe wrapper */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        overflow: hidden;
    }}

    /* Divider */
    hr {{ border-color: {COLORS["border"]} !important; }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: {COLORS["bg_card"]};
        border-radius: 10px;
        padding: 4px;
        border: 1px solid {COLORS["border"]};
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: {COLORS["text_muted"]};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS["primary"]} !important;
        color: white !important;
    }}

    /* Inputs */
    .stMultiSelect div[data-baseweb="select"], .stSelectbox div[data-baseweb="select"] {{
        background: {COLORS["bg_card_2"]} !important;
        border-color: {COLORS["border"]} !important;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: {COLORS["bg"]}; }}
    ::-webkit-scrollbar-thumb {{ background: {COLORS["border"]}; border-radius: 6px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #3a4452; }}
</style>
""", unsafe_allow_html=True)


def section(title: str):
    st.markdown(f'<div class="section-title"><span class="dot"></span>{title}</div>', unsafe_allow_html=True)


def style_fig(fig, height: int = 360, title: str | None = None):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=14, color=COLORS["text"]), x=0.01))
    return fig


# =========================================================
# 📥 LOAD DATA
# =========================================================
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = (
        df.columns.str.lower().str.strip()
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
        "clientclient_id": "client_id",
    }
    return df.rename(columns=rename_dict)


# =========================================================
# 🧭 HEADER
# =========================================================
st.markdown(f"""
<div class="header-banner">
    <h1>📊 Dashboard de Produtividade</h1>
    <p>Visão executiva por usuário · análise de jornada, volume e performance</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 📂 UPLOAD
# =========================================================
st.sidebar.markdown("### 📂 Upload de Dados")
arquivo = st.sidebar.file_uploader("Arquivo Excel (.xlsx)", type=["xlsx"])

if not arquivo:
    st.info("👈 Faça upload do arquivo Excel na barra lateral para iniciar a análise.")
    st.stop()

df = load_data(arquivo)

# =========================================================
# ⏱️ ORDENAR HORÁRIOS
# =========================================================
df["hora_inicio"] = pd.to_datetime(df["time_hour_interval"].str.extract(r"(\d{2}:\d{2})")[0], format="%H:%M")
df["hora_fim"]    = pd.to_datetime(df["time_hour_interval"].str.extract(r"-(\d{2}:\d{2})")[0], format="%H:%M")
df = df.sort_values("hora_inicio")

# =========================================================
# 🎛️ FILTROS
# =========================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Filtros")

usuarios = st.sidebar.multiselect("👤 Usuário", sorted(df["user_name"].dropna().unique()))
eventos  = st.sidebar.multiselect("⚡ Tipo de Evento", sorted(df["event_type_name"].dropna().unique()))
clientes = st.sidebar.multiselect("🏢 Cliente", sorted(df["client_id"].dropna().unique()))

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    datas = st.sidebar.date_input("📅 Data", [])
    if datas:
        df = df[df["date"].isin(pd.to_datetime(datas))]

if usuarios: df = df[df["user_name"].isin(usuarios)]
if eventos:  df = df[df["event_type_name"].isin(eventos)]
if clientes: df = df[df["client_id"].isin(clientes)]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Configurações")
META = st.sidebar.number_input("Meta de eventos por usuário", value=100, min_value=1)

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# =========================================================
# 📊 KPIs
# =========================================================
total_eventos = int(df["event_count"].sum())
tempo_medio   = round(df["event_elapsed_time"].mean(), 2)
total_users   = df["user_name"].nunique()
pico          = df.groupby("time_hour_interval")["event_count"].sum().idxmax()

k1, k2, k3, k4 = st.columns(4)
k1.metric("⚡ Total de Eventos", f"{total_eventos:,}".replace(",", "."))
k2.metric("⏱️ Tempo Médio (s)", f"{tempo_medio}")
k3.metric("👥 Usuários Ativos", total_users)
k4.metric("🔥 Horário de Pico", pico)

st.markdown("")

# =========================================================
# 🔥 SCORE
# =========================================================
df_user = df.groupby("user_name").agg({
    "event_count": "sum",
    "event_elapsed_time": "mean",
}).reset_index()

df_user["score_volume"] = df_user["event_count"] / df_user["event_count"].max()
df_user["score_tempo"]  = 1 - (df_user["event_elapsed_time"] / df_user["event_elapsed_time"].max())
df_user["score"]        = df_user["score_volume"] * 0.6 + df_user["score_tempo"] * 0.4
df_user["%meta"]        = df_user["event_count"] / META

# =========================================================
# 🧱 GARGALO
# =========================================================
gargalo = df.groupby("time_hour_interval")["event_count"].sum().reset_index()
media = gargalo["event_count"].mean()
gargalo["status"] = gargalo["event_count"].apply(
    lambda x: "🔥 Pico" if x > media * 1.5 else ("🕳️ Vale" if x < media * 0.5 else "OK")
)

ordem = sorted(
    df["time_hour_interval"].unique(),
    key=lambda x: pd.to_datetime(x.split("-")[0], format="%H:%M"),
)

# =========================================================
# 📈 ABAS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Visão Geral", "👥 Performance", "🕒 Jornada", "📋 Dados", "📖 Manual"]
)

# ----- TAB 1: VISÃO GERAL -----
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        section("Volume de Eventos por Hora")
        fig_vol = px.area(
            gargalo, x="time_hour_interval", y="event_count",
            category_orders={"time_hour_interval": ordem},
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig_vol.update_traces(
            line=dict(width=2.5, color=COLORS["primary"]),
            fillcolor="rgba(46,168,255,0.18)",
            mode="lines+markers",
            marker=dict(size=6, color=COLORS["accent"]),
        )
        fig_vol.add_hline(y=media, line_dash="dash", line_color=COLORS["text_muted"],
                          annotation_text="Média", annotation_font_color=COLORS["text_muted"])
        st.plotly_chart(style_fig(fig_vol, 380), use_container_width=True)

    with col2:
        section("Status por Faixa Horária")
        status_cor = {"🔥 Pico": COLORS["danger"], "🕳️ Vale": COLORS["warning"], "OK": COLORS["success"]}
        fig_st = px.bar(
            gargalo, x="event_count", y="time_hour_interval", color="status",
            orientation="h", category_orders={"time_hour_interval": ordem},
            color_discrete_map=status_cor,
        )
        fig_st.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(style_fig(fig_st, 380), use_container_width=True)

    section("Heatmap — Usuário × Hora")
    pivot = df.pivot_table(
        index="user_name", columns="time_hour_interval",
        values="event_count", aggfunc="sum", fill_value=0,
    )[ordem]
    fig_heat = px.imshow(pivot, aspect="auto", color_continuous_scale=PLOTLY_HEAT)
    fig_heat.update_layout(coloraxis_colorbar=dict(title="Eventos"))
    st.plotly_chart(style_fig(fig_heat, 420), use_container_width=True)

# ----- TAB 2: PERFORMANCE -----
with tab2:
    section("Ranking de Performance (Score)")

    df_rank = df_user.sort_values("score", ascending=False).copy()
    df_rank["score_pct"] = (df_rank["score"] * 100).round(1)

    fig_rank = px.bar(
        df_rank, x="score_pct", y="user_name", orientation="h",
        color="score_pct", color_continuous_scale=[[0, COLORS["danger"]],
                                                   [0.5, COLORS["warning"]],
                                                   [1, COLORS["success"]]],
        text="score_pct",
    )
    fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_rank.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    st.plotly_chart(style_fig(fig_rank, max(320, 28 * len(df_rank))), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Atingimento da Meta")
        df_meta = df_user.sort_values("%meta", ascending=False).copy()
        df_meta["pct"] = (df_meta["%meta"] * 100).round(1)
        fig_meta = px.bar(
            df_meta, x="user_name", y="pct",
            color="pct",
            color_continuous_scale=[[0, COLORS["danger"]], [0.5, COLORS["warning"]], [1, COLORS["success"]]],
            text="pct",
        )
        fig_meta.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig_meta.add_hline(y=100, line_dash="dash", line_color=COLORS["accent"],
                           annotation_text="Meta", annotation_font_color=COLORS["accent"])
        fig_meta.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="% da meta")
        st.plotly_chart(style_fig(fig_meta, 360), use_container_width=True)

    with col_b:
        section("Volume × Tempo Médio")
        fig_sc = px.scatter(
            df_user, x="event_elapsed_time", y="event_count",
            size="event_count", color="score",
            color_continuous_scale=[[0, COLORS["danger"]], [0.5, COLORS["warning"]], [1, COLORS["success"]]],
            hover_name="user_name",
            labels={"event_elapsed_time": "Tempo médio (s)", "event_count": "Eventos"},
        )
        st.plotly_chart(style_fig(fig_sc, 360), use_container_width=True)

# ----- TAB 3: JORNADA -----
with tab3:
    section("Jornada dos Usuários")

    df_turno = df.copy()
    df_turno["gap"] = df_turno.groupby("user_name")["hora_inicio"].diff()
    df_turno["novo_bloco"] = df_turno["gap"].isna() | (df_turno["gap"].dt.total_seconds() > 3600)

    inicio = df_turno[df_turno["novo_bloco"]].groupby("user_name")["hora_inicio"].min().reset_index()
    fim = df_turno.groupby("user_name")["hora_fim"].max().reset_index()
    turno = inicio.merge(fim, on="user_name")
    turno["duracao_h"] = ((turno["hora_fim"] - turno["hora_inicio"]).dt.total_seconds() / 3600).round(2)

    turno_fmt = turno.copy()
    turno_fmt["Início"] = turno_fmt["hora_inicio"].dt.strftime("%H:%M")
    turno_fmt["Fim"] = turno_fmt["hora_fim"].dt.strftime("%H:%M")
    turno_fmt = turno_fmt.rename(columns={"user_name": "Usuário", "duracao_h": "Duração (h)"})
    st.dataframe(
        turno_fmt[["Usuário", "Início", "Fim", "Duração (h)"]],
        use_container_width=True, hide_index=True,
    )

    section("Timeline Individual")
    usuario_timeline = st.selectbox("Selecione um usuário", sorted(df["user_name"].unique()))
    df_tl = df[df["user_name"] == usuario_timeline].copy()

    fig_tl = px.timeline(
        df_tl, x_start="hora_inicio", x_end="hora_fim",
        y="event_type_name", color="event_count",
        color_continuous_scale=[[0, COLORS["primary"]], [1, COLORS["accent"]]],
        hover_data=["event_count", "event_elapsed_time"],
    )
    fig_tl.update_yaxes(autorange="reversed")
    st.plotly_chart(style_fig(fig_tl, 420), use_container_width=True)

# ----- TAB 4: DADOS -----
with tab4:
    section("Base de Dados Filtrada")
    st.caption(f"{len(df):,} registros".replace(",", "."))
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Baixar CSV", csv, "dados_filtrados.csv", "text/csv")

# ----- TAB 5: MANUAL -----
with tab5:
    section("📖 Manual do Usuário — Como Interpretar o Dashboard")

    st.markdown(
        """
        Este painel foi desenhado para **gestores** acompanharem a produtividade da equipe.
        Abaixo, o significado de cada indicador, gráfico e cálculo utilizado.
        """
    )

    with st.expander("🎯 KPIs principais (cards no topo)", expanded=True):
        st.markdown(
            """
            - **Total de Eventos** — Soma de todas as ações registradas no período filtrado.
              Mede o **volume bruto** de trabalho executado pela equipe.
            - **Usuários Ativos** — Quantidade de pessoas distintas que registraram
              ao menos um evento. Útil para dimensionar a operação ativa.
            - **Tempo Médio por Evento (s)** — Quanto tempo, em média, cada ação consome.
              Quanto **menor**, mais ágil é o processo.
            - **Eventos por Usuário** — Produtividade média individual
              (Total de Eventos ÷ Usuários Ativos).
            """
        )

    with st.expander("📈 Aba Visão Geral"):
        st.markdown(
            """
            - **Volume de Eventos por Hora** — Curva de atividade ao longo do dia.
              A linha tracejada mostra a **média horária**; pontos acima indicam picos
              de demanda, abaixo indicam ociosidade.
            - **Status por Faixa Horária** — Classifica cada hora em:
                - 🔥 **Pico**: volume bem acima da média (sobrecarga).
                - 🕳️ **Vale**: volume bem abaixo da média (ociosidade).
                - **OK**: dentro do esperado.
              Use para **redistribuir escalas** e equilibrar a carga de trabalho.
            - **Heatmap Usuário × Hora** — Mapa de calor mostrando *quem* trabalha
              *quando*. Cores mais intensas = maior volume. Identifica rapidamente
              concentração de esforço e lacunas de cobertura.
            """
        )

    with st.expander("👥 Aba Performance"):
        st.markdown(
            """
            - **Score de Performance** — Indicador composto, normalizado de 0 a 100%:
              `Score = 60% × (volume normalizado) + 40% × (1 − tempo normalizado)`
              Premia quem entrega **mais volume** com **menor tempo médio**.
                - 🟢 Verde: alto desempenho.
                - 🟡 Amarelo: desempenho médio.
                - 🔴 Vermelho: requer atenção.
            - **Atingimento da Meta (%)** — Compara o volume de cada usuário com a
              meta definida. A linha de referência marca **100%**. Acima = meta batida.
            - **Volume × Tempo Médio** — Dispersão para identificar perfis:
                - Canto **superior-esquerdo**: alto volume e rápido (estrelas).
                - Canto **inferior-direito**: baixo volume e lento (atenção).
              O tamanho da bolha representa o volume; a cor, o score.
            """
        )

    with st.expander("🕒 Aba Jornada"):
        st.markdown(
            """
            - **Jornada dos Usuários** — Tabela com **início**, **fim** e **duração**
              do turno de cada pessoa. Considera-se um novo bloco de trabalho quando
              há intervalo superior a **1 hora** entre eventos.
            - **Timeline Individual** — Linha do tempo detalhada das atividades de um
              usuário específico, separada por tipo de evento. A intensidade da cor
              representa o volume de eventos em cada bloco. Ideal para **auditoria**
              e análise de fluxo de trabalho individual.
            """
        )

    with st.expander("📋 Aba Dados"):
        st.markdown(
            """
            - **Base de Dados Filtrada** — Tabela completa respeitando os filtros
              aplicados na barra lateral.
            - **⬇️ Baixar CSV** — Exporta os dados filtrados para análise externa
              (Excel, Power BI, etc.).
            """
        )

    with st.expander("🧭 Filtros (barra lateral)"):
        st.markdown(
            """
            Todos os filtros são **cumulativos** e impactam **todas as abas**:
            - **Usuários** — Restringe a análise a pessoas selecionadas.
            - **Tipo de Evento** — Foca em uma categoria específica de atividade.
            - **Faixa Horária** — Recorta o período do dia analisado.
            """
        )

    st.info(
        "💡 **Dica:** Combine o **Heatmap** com o **Status por Faixa Horária** "
        "para identificar gargalos e propor realocações de equipe."
    )
