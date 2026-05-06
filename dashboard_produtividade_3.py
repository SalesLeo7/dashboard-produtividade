"""
Dashboard de Produtividade — Tema Corporativo Dark (estilo Power BI)
Execute com: streamlit run dashboard_produtividade_2.py
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
#  CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Produtividade",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# =========================================================
#  PALETA E TEMA (Dark + Light — estilo Power BI)
# =========================================================
THEMES = {
    "dark": {
        "bg":          "#0E1117",
        "bg_card":     "#161B22",
        "bg_card_2":   "#1C232C",
        "border":      "#2A323D",
        "text":        "#E6EDF3",
        "text_muted":  "#8B949E",
        "primary":     "#2EA8FF",
        "accent":      "#00D4B4",
        "warning":     "#F2B441",
        "danger":      "#F85149",
        "success":     "#3FB950",
        "header_grad": "linear-gradient(120deg, #0E1117 0%, #14253B 60%, #0E1117 100%)",
        "heat": [
            [0.0, "#0E1117"], [0.2, "#0B2942"], [0.5, "#125E96"],
            [0.8, "#2EA8FF"], [1.0, "#7CC9FF"],
        ],
    },
    "light": {
        "bg":          "#F4F6F8",
        "bg_card":     "#FFFFFF",
        "bg_card_2":   "#F8FAFC",
        "border":      "#E2E8F0",
        "text":        "#1A202C",
        "text_muted":  "#64748B",
        "primary":     "#0078D4",
        "accent":      "#00B294",
        "warning":     "#D97706",
        "danger":      "#DC2626",
        "success":     "#16A34A",
        "header_grad": "linear-gradient(120deg, #FFFFFF 0%, #E6F2FB 60%, #FFFFFF 100%)",
        "heat": [
            [0.0, "#F4F6F8"], [0.2, "#CDE4F7"], [0.5, "#7FB8E5"],
            [0.8, "#0078D4"], [1.0, "#003E73"],
        ],
    },
}

# Inicializa o tema antes de qualquer render
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

THEME = st.session_state["theme_mode"]
COLORS = THEMES[THEME]

PLOTLY_SEQ = ["#2EA8FF", "#00D4B4", "#F2B441", "#F85149", "#A371F7", "#3FB950", "#FF7B72"] \
    if THEME == "dark" else \
    ["#0078D4", "#00B294", "#D97706", "#DC2626", "#7C3AED", "#16A34A", "#E11D48"]

PLOTLY_HEAT = COLORS["heat"]

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
#  CSS CUSTOMIZADO
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
        background: {COLORS["header_grad"]};
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
    ::-webkit-scrollbar-thumb:hover {{ background: {COLORS["primary"]}; }}

    /* Sidebar — branding e seções */
    .sb-brand {{
        display: flex; align-items: center; gap: 10px;
        padding: 6px 4px 14px 4px;
        border-bottom: 1px solid {COLORS["border"]};
        margin-bottom: 14px;
    }}
    .sb-brand .logo {{
        width: 34px; height: 34px; border-radius: 8px;
        background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["accent"]} 100%);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px; box-shadow: 0 4px 14px rgba(46,168,255,0.35);
    }}
    .sb-brand .title {{
        font-size: 0.95rem; font-weight: 700; color: {COLORS["text"]};
        line-height: 1.1;
    }}
    .sb-brand .subtitle {{
        font-size: 0.72rem; color: {COLORS["text_muted"]};
        text-transform: uppercase; letter-spacing: 0.08em;
    }}

    .sb-section-label {{
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {COLORS["text_muted"]} !important;
        font-weight: 600;
        margin: 18px 0 8px 0;
        padding-left: 2px;
    }}

    /* Upload card no rodapé da sidebar */
    .sb-upload-wrap {{
        margin-top: 10px;
        padding: 12px;
        background: {COLORS["bg_card_2"]};
        border: 1px dashed {COLORS["border"]};
        border-radius: 10px;
    }}
    .sb-upload-title {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {COLORS["text"]};
        display: flex; align-items: center; gap: 6px;
        margin-bottom: 4px;
    }}
    .sb-upload-hint {{
        font-size: 0.7rem;
        color: {COLORS["text_muted"]};
        margin-bottom: 8px;
    }}

    /* Compactar o file_uploader dentro da sidebar */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] section {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 8px !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] small {{
        color: {COLORS["text_muted"]} !important;
        font-size: 0.68rem !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
        background: {COLORS["primary"]} !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        padding: 4px 12px !important;
    }}

    /* Status do arquivo carregado */
    .sb-file-status {{
        display: flex; align-items: center; gap: 8px;
        background: rgba(63,185,80,0.08);
        border: 1px solid rgba(63,185,80,0.3);
        border-radius: 8px;
        padding: 8px 10px;
        margin-top: 8px;
        font-size: 0.75rem;
        color: {COLORS["success"]};
    }}
    .sb-file-status .dot-ok {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {COLORS["success"]};
        box-shadow: 0 0 8px {COLORS["success"]};
    }}

    /* Footer da sidebar */
    .sb-footer {{
        margin-top: 18px;
        padding-top: 10px;
        border-top: 1px solid {COLORS["border"]};
        font-size: 0.68rem;
        color: {COLORS["text_muted"]};
        text-align: center;
    }}
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
#  LOAD DATA
# FIX: recebe bytes (hashável pelo cache) em vez do objeto UploadedFile.
# FIX: filtra usuários "?" — movimentações automáticas do sistema.
# FIX: parsing de datetime e ordenação movidos para dentro do cache.
# =========================================================
@st.cache_data(show_spinner="Carregando dados...")
def load_data(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = (
        df.columns.str.lower().str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(" ", "_")
    )
    rename_dict = {
        "useruser_name":                       "user_name",
        "event_typeevent_type_name":           "event_type_name",
        "time_event_datetime_hour_interval":   "time_hour_interval",
        "calendar_event_datedate":             "date",
        "event_count":                         "event_count",
        "event_elapsed_time_avg":              "event_elapsed_time",
        "clientclient_id":                     "client_id",
    }
    df = df.rename(columns=rename_dict)

    # ----- FIX: remove movimentações automáticas do sistema -----
    # Usuários cujo nome é "?" representam ações internas e não devem
    # aparecer nas análises de produtividade da equipe.
    if "user_name" in df.columns:
        df = df[df["user_name"].notna()]
        df = df[df["user_name"].astype(str).str.strip() != "?"]

    # ----- FIX: parsing de horários dentro do cache -----
    if "time_hour_interval" in df.columns:
        df["hora_inicio"] = pd.to_datetime(
            df["time_hour_interval"].str.extract(r"(\d{2}:\d{2})")[0],
            format="%H:%M",
        )
        df["hora_fim"] = pd.to_datetime(
            df["time_hour_interval"].str.extract(r"-(\d{2}:\d{2})")[0],
            format="%H:%M",
        )
        df = df.sort_values("hora_inicio")

    return df


# =========================================================
# HEADER
# =========================================================
st.markdown(f"""
<div class="header-banner">
    <h1>📊 Dashboard de Produtividade</h1>
    <p>Visão executiva por usuário · análise de jornada, volume e performance</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🧭 SIDEBAR — Branding
# =========================================================
st.sidebar.markdown("""
<div class="sb-brand">
    <div class="logo">📊</div>
    <div>
        <div class="title">Produtividade</div>
        <div class="subtitle">Painel Gestor</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 📂 UPLOAD
# FIX: armazena os bytes do arquivo no session_state (não o objeto
# UploadedFile, que não é hashável pelo cache e perde referência).
# FIX: render_upload simplificado — sem divs abertas/fechadas separadas.
# =========================================================
def render_upload(container, compact: bool = False, key: str = "up_main"):
    label = "Fonte de Dados" if compact else "📁 Comece aqui"
    hint  = "Substituir base atual (.xlsx)" if compact else "Envie a planilha Excel para iniciar (.xlsx)"
    container.markdown(f'<div class="sb-section-label">{label}</div>', unsafe_allow_html=True)
    container.markdown(
        f'<div class="sb-upload-wrap">'
        f'<div class="sb-upload-title">📁 Arquivo de dados</div>'
        f'<div class="sb-upload-hint">{hint}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    return container.file_uploader(" ", type=["xlsx"], label_visibility="collapsed", key=key)


arquivo_bytes: bytes | None = st.session_state.get("arquivo_bytes")
arquivo_nome:  str   | None = st.session_state.get("arquivo_nome")

if not arquivo_bytes:
    uploaded = render_upload(st.sidebar, compact=False, key="up_main")
    if uploaded:
        st.session_state["arquivo_bytes"] = uploaded.read()
        st.session_state["arquivo_nome"]  = uploaded.name
        st.rerun()

if not arquivo_bytes:
    st.info("👈 Faça upload do arquivo Excel na barra lateral para iniciar a análise.")
    st.stop()

# ----- FIX: try/except para erros de formato no arquivo -----
try:
    df = load_data(arquivo_bytes)
except Exception as e:
    st.error(f"❌ Não foi possível carregar o arquivo: {e}")
    st.caption("Verifique se o Excel está no formato correto e tente novamente.")
    if st.button("Carregar outro arquivo"):
        st.session_state.pop("arquivo_bytes", None)
        st.session_state.pop("arquivo_nome", None)
        st.rerun()
    st.stop()

# =========================================================
# 🎛️ FILTROS (topo da sidebar)
# =========================================================
st.sidebar.markdown('<div class="sb-section-label">🎛️ Filtros</div>', unsafe_allow_html=True)

usuarios = st.sidebar.multiselect(
    "Usuário",
    sorted(df["user_name"].dropna().unique()),
    placeholder="Todos os usuários",
)
eventos = st.sidebar.multiselect(
    "Tipo de Evento",
    sorted(df["event_type_name"].dropna().unique()),
    placeholder="Todos os eventos",
)
clientes = st.sidebar.multiselect(
    "Cliente",
    sorted(df["client_id"].dropna().unique()),
    placeholder="Todos os clientes",
)

# FIX: filtro de data com suporte a intervalo (range) e data única
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    datas = st.sidebar.date_input("Data", [])
    if datas:
        if isinstance(datas, (list, tuple)) and len(datas) == 2:
            start = pd.to_datetime(datas[0])
            end   = pd.to_datetime(datas[1])
            df = df[(df["date"] >= start) & (df["date"] <= end)]
        else:
            df = df[df["date"].isin(pd.to_datetime(list(datas)))]

if eventos:  df = df[df["event_type_name"].isin(eventos)]
if clientes: df = df[df["client_id"].isin(clientes)]

# Salva ANTES do filtro de usuário — usado para ranking global no relatório de feedback
df_global = df.copy()

if usuarios: df = df[df["user_name"].isin(usuarios)]

# =========================================================
# 🎯 CONFIGURAÇÕES
# FIX: pesos do score expostos como sliders para o gestor calibrar.
# =========================================================
st.sidebar.markdown('<div class="sb-section-label">🎯 Configurações</div>', unsafe_allow_html=True)
META_DIARIA = st.sidebar.number_input("Meta diária de eventos por usuário", value=100, min_value=1, help="Quantidade de eventos esperada por dia útil (domingos excluídos automaticamente)")

with st.sidebar.expander("⚖️ Pesos do Score"):
    peso_volume = st.slider(
        "Peso — Volume (%)", min_value=0, max_value=100, value=60, step=5,
    ) / 100
    peso_tempo = round(1 - peso_volume, 2)
    st.caption(f"Tempo: {int(peso_tempo * 100)}% (complementar automático)")

# =========================================================
# 📁 FONTE DE DADOS (rodapé da sidebar — discreto)
# =========================================================
with st.sidebar.expander(f"📁 Fonte: {arquivo_nome}", expanded=False):
    st.markdown(
        '<div class="sb-file-status"><span class="dot-ok"></span>'
        'Arquivo carregado com sucesso</div>',
        unsafe_allow_html=True,
    )
    novo = st.file_uploader(
        "Substituir arquivo", type=["xlsx"],
        label_visibility="collapsed", key="up_replace",
    )
    if novo:
        st.session_state["arquivo_bytes"] = novo.read()
        st.session_state["arquivo_nome"]  = novo.name
        st.rerun()

st.sidebar.markdown(
    '<div class="sb-footer">Dashboard de Produtividade · v1.1</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="sb-section-label">🎨 Aparência</div>', unsafe_allow_html=True)
_is_dark = st.session_state["theme_mode"] == "dark"
_tc1, _tc2 = st.sidebar.columns(2)
if _tc1.button("🌙 Escuro", use_container_width=True,
               type="primary" if _is_dark else "secondary", key="btn_dark"):
    if not _is_dark:
        st.session_state["theme_mode"] = "dark"
        st.rerun()
if _tc2.button("☀️ Claro", use_container_width=True,
               type="primary" if not _is_dark else "secondary", key="btn_light"):
    if _is_dark:
        st.session_state["theme_mode"] = "light"
        st.rerun()

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# =========================================================
# 📅 DIAS ÚTEIS E META DO PERÍODO
# Conta os dias únicos presentes nos dados filtrados,
# excluindo domingos (weekday == 6).
# META_TOTAL = META_DIARIA × dias_uteis
# =========================================================
if "date" in df.columns:
    datas_unicas = pd.to_datetime(df["date"].dropna().dt.normalize().unique())
    dias_uteis   = int((datas_unicas.dayofweek != 6).sum())
else:
    dias_uteis = 1

dias_uteis  = max(dias_uteis, 1)          # garante mínimo 1 dia
META_TOTAL  = META_DIARIA * dias_uteis    # meta real do período selecionado

# =========================================================
# ⏸️ TEMPO OCIOSO  (% do turno + maior gap intra-turno)
#
# Para cada usuário:
#   1. Calcula todos os gaps positivos entre hora_fim[i] e hora_inicio[i+1]
#   2. Identifica o maior gap; se ≥ 45 min → descartado como almoço/pausa longa
#   3. Dos gaps restantes:
#        pct_ocioso = soma(gaps) / duração_total_turno × 100
#        maior_gap  = max(gaps)  — maior ausência pontual intra-turno
# =========================================================
def calc_ociosidade(df_in: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for user, grp in df_in.groupby("user_name"):
        grp = grp.sort_values("hora_inicio").reset_index(drop=True)

        # Duração total do turno (primeiro início → último fim)
        turno_min = (grp["hora_fim"].iloc[-1] - grp["hora_inicio"].iloc[0]).total_seconds() / 60
        if turno_min <= 0:
            rows.append({"user_name": user, "pct_ocioso": 0.0, "maior_gap": 0.0})
            continue

        # Todos os gaps positivos entre eventos consecutivos
        gaps = []
        for i in range(len(grp) - 1):
            delta = (grp.loc[i + 1, "hora_inicio"] - grp.loc[i, "hora_fim"]).total_seconds() / 60
            if delta > 0:
                gaps.append(round(delta, 1))

        if not gaps:
            rows.append({"user_name": user, "pct_ocioso": 0.0, "maior_gap": 0.0})
            continue

        # Remove o maior gap se for ≥ 45 min (almoço / pausa longa)
        gaps_sorted = sorted(gaps, reverse=True)
        if gaps_sorted[0] >= 45:
            gaps_intra = gaps_sorted[1:]   # exclui o almoço
        else:
            gaps_intra = gaps_sorted

        total_ocio = sum(gaps_intra)
        maior_gap  = max(gaps_intra) if gaps_intra else 0.0
        pct_ocioso = round((total_ocio / turno_min) * 100, 1)

        rows.append({
            "user_name":  user,
            "pct_ocioso": pct_ocioso,
            "maior_gap":  round(maior_gap, 1),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["user_name", "pct_ocioso", "maior_gap"]
    )

df_ocio         = calc_ociosidade(df)
ocio_pct_geral  = round(df_ocio["pct_ocioso"].mean(), 1)  if not df_ocio.empty else 0.0
ocio_gap_geral  = round(df_ocio["maior_gap"].mean(),  1)  if not df_ocio.empty else 0.0

# =========================================================
# 📊 KPIs
# FIX: adicionado "Eventos por Usuário" — KPI descrito no manual
# mas que estava ausente nos cards do dashboard.
# =========================================================
total_eventos  = int(df["event_count"].sum())
tempo_medio    = round(df["event_elapsed_time"].mean(), 2)
total_users    = df["user_name"].nunique()
eventos_user   = round(total_eventos / total_users, 1) if total_users else 0
pico           = df.groupby("time_hour_interval")["event_count"].sum().idxmax()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("⚡ Total de Eventos",    f"{total_eventos:,}".replace(",", "."))
k2.metric("⏱️ Tempo Médio (s)",     f"{tempo_medio}")
k3.metric("👥 Usuários Ativos",     total_users)
k4.metric("📈 Eventos / Usuário",   f"{eventos_user:,}".replace(",", "."))
k5.metric("🔥 Horário de Pico",     pico)

st.markdown(
    f'<div class="section-title" style="margin-top:10px;">' +
    f'<span class="dot" style="background:{COLORS["warning"]};box-shadow:0 0 10px {COLORS["warning"]};"></span>' +
    f'Ociosidade da Equipe — Média do Período</div>',
    unsafe_allow_html=True,
)
k6, k7, _k8, _k9 = st.columns(4)
k6.metric("⏸️ % Tempo Ocioso",  f"{ocio_pct_geral}%",
          help="% médio do turno sem registro de eventos (almoço excluído automaticamente)")
k7.metric("⚠️ Maior Gap Médio",  f"{ocio_gap_geral} min",
          help="Média do maior intervalo pontual sem evento por usuário (almoço excluído)")

st.markdown("")

st.markdown(
    f'<div style="font-size:0.8rem; color:{COLORS["text_muted"]}; ' +
    f'padding:6px 12px; border:1px solid {COLORS["border"]}; ' +
    f'border-radius:8px; display:inline-block; margin-bottom:8px;">' +
    f'📅 Meta do período: <strong style="color:{COLORS["text"]};">{str(META_TOTAL).replace(",", ".")} eventos</strong>' +
    f' &nbsp;=&nbsp; {META_DIARIA}/dia × {dias_uteis} dia{"s" if dias_uteis > 1 else ""} útil{"" if dias_uteis == 1 else "is"} ' +
    f'(domingos excluídos)</div>',
    unsafe_allow_html=True,
)

# =========================================================
# 🔥 SCORE
# FIX: proteção contra divisão por zero na normalização.
# FIX: pesos aplicados a partir dos sliders da sidebar.
# =========================================================
df_user = df.groupby("user_name").agg({
    "event_count":        "sum",
    "event_elapsed_time": "mean",
}).reset_index()

max_vol  = df_user["event_count"].max()        or 1
max_time = df_user["event_elapsed_time"].max() or 1

df_user["score_volume"] = df_user["event_count"]        / max_vol
df_user["score_tempo"]  = 1 - (df_user["event_elapsed_time"] / max_time)
df_user["score"]        = df_user["score_volume"] * peso_volume + df_user["score_tempo"] * peso_tempo
df_user["%meta"]        = df_user["event_count"] / META_TOTAL

# =========================================================
# 🧱 GARGALO
# =========================================================
gargalo = df.groupby("time_hour_interval")["event_count"].sum().reset_index()
media   = gargalo["event_count"].mean()
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📈 Visão Geral", "👥 Performance", "🕒 Jornada", "📋 Dados", "📖 Manual", "🖨️ Feedback"]
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
            fillcolor=f"rgba({int(COLORS['primary'][1:3],16)},{int(COLORS['primary'][3:5],16)},{int(COLORS['primary'][5:7],16)},0.15)",
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

    section("⏸️ Análise de Ociosidade por Usuário")
    st.caption(
        "O maior gap diário (≥ 45 min) é descartado automaticamente como almoço/pausa longa. "
        "Apenas intervalos intra-turno são contabilizados."
    )
    if not df_ocio.empty:

        def cor_pct(v):
            if v > 20: return COLORS["danger"]
            if v > 10: return COLORS["warning"]
            return COLORS["success"]

        def cor_gap(v):
            if v > 30: return COLORS["danger"]
            if v > 15: return COLORS["warning"]
            return COLORS["success"]

        col_o1, col_o2 = st.columns(2)

        with col_o1:
            st.markdown(f'<div style="font-size:0.88rem;font-weight:600;color:{COLORS["text"]};margin-bottom:4px;">% do Turno Ocioso</div>', unsafe_allow_html=True)
            st.caption("Quanto do horário de trabalho ficou sem registro de eventos")
            df_pct = df_ocio.sort_values("pct_ocioso", ascending=False)
            fig_pct = go.Figure(go.Bar(
                x=df_pct["user_name"],
                y=df_pct["pct_ocioso"],
                marker_color=[cor_pct(v) for v in df_pct["pct_ocioso"]],
                text=df_pct["pct_ocioso"].apply(lambda v: f"{v}%"),
                textposition="outside",
            ))
            fig_pct.add_hline(
                y=ocio_pct_geral, line_dash="dash", line_color=COLORS["text_muted"],
                annotation_text=f"Média: {ocio_pct_geral}%",
                annotation_font_color=COLORS["text_muted"],
            )
            fig_pct.update_layout(xaxis_title="", yaxis_title="% ocioso")
            st.plotly_chart(style_fig(fig_pct, 340), use_container_width=True)
            leg1, leg2, leg3 = st.columns(3)
            leg1.markdown(f'<span style="color:{COLORS["success"]}; font-weight:600;">● ≤ 10%</span> Ótimo', unsafe_allow_html=True)
            leg2.markdown(f'<span style="color:{COLORS["warning"]}; font-weight:600;">● 10–20%</span> Atenção', unsafe_allow_html=True)
            leg3.markdown(f'<span style="color:{COLORS["danger"]}; font-weight:600;">● > 20%</span> Crítico', unsafe_allow_html=True)

        with col_o2:
            st.markdown(f'<div style="font-size:0.88rem;font-weight:600;color:{COLORS["text"]};margin-bottom:4px;">Maior Gap Intra-turno (min)</div>', unsafe_allow_html=True)
            st.caption("Maior intervalo pontual sem nenhum evento registrado")
            df_gap = df_ocio.sort_values("maior_gap", ascending=False)
            fig_gap = go.Figure(go.Bar(
                x=df_gap["user_name"],
                y=df_gap["maior_gap"],
                marker_color=[cor_gap(v) for v in df_gap["maior_gap"]],
                text=df_gap["maior_gap"].apply(lambda v: f"{v} min"),
                textposition="outside",
            ))
            fig_gap.add_hline(
                y=ocio_gap_geral, line_dash="dash", line_color=COLORS["text_muted"],
                annotation_text=f"Média: {ocio_gap_geral} min",
                annotation_font_color=COLORS["text_muted"],
            )
            fig_gap.update_layout(xaxis_title="", yaxis_title="minutos")
            st.plotly_chart(style_fig(fig_gap, 340), use_container_width=True)
            leg4, leg5, leg6 = st.columns(3)
            leg4.markdown(f'<span style="color:{COLORS["success"]}; font-weight:600;">● ≤ 15 min</span> Ótimo', unsafe_allow_html=True)
            leg5.markdown(f'<span style="color:{COLORS["warning"]}; font-weight:600;">● 15–30 min</span> Atenção', unsafe_allow_html=True)
            leg6.markdown(f'<span style="color:{COLORS["danger"]}; font-weight:600;">● > 30 min</span> Crítico', unsafe_allow_html=True)

    else:
        st.info("Não foi possível calcular o tempo ocioso com os dados disponíveis.")

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
    fim    = df_turno.groupby("user_name")["hora_fim"].max().reset_index()
    turno  = inicio.merge(fim, on="user_name")
    turno["duracao_h"] = ((turno["hora_fim"] - turno["hora_inicio"]).dt.total_seconds() / 3600).round(2)

    turno_fmt = turno.copy()
    turno_fmt["Início"]     = turno_fmt["hora_inicio"].dt.strftime("%H:%M")
    turno_fmt["Fim"]        = turno_fmt["hora_fim"].dt.strftime("%H:%M")
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

        > Os registros de movimentações automáticas do sistema (usuário `?`) são excluídos
        > automaticamente de todas as análises.
        """
    )

    with st.expander("🎯 KPIs principais — Linha 1 (volume e pico)", expanded=True):
        st.markdown(
            """
            - **Total de Eventos** — Soma de todas as ações registradas no período filtrado.
              Mede o **volume bruto** de trabalho executado pela equipe.
            - **Tempo Médio (s)** — Quanto tempo, em média, cada ação consome.
              Quanto **menor**, mais ágil é o processo.
            - **Usuários Ativos** — Quantidade de pessoas distintas que registraram
              ao menos um evento. Útil para dimensionar a operação ativa.
            - **Eventos / Usuário** — Produtividade média individual
              (Total de Eventos ÷ Usuários Ativos).
            - **Horário de Pico** — Faixa horária com maior volume de eventos no período.
            """
        )

    with st.expander("⏸️ KPIs de Ociosidade — Linha 2"):
        st.markdown(
            """
            Calculados automaticamente para toda a equipe. O maior gap diário de cada
            usuário (≥ 45 min) é descartado como almoço ou pausa longa.

            - **% Tempo Ocioso** — Percentual médio do turno sem nenhum evento registrado.
              Fórmula: `soma dos gaps intra-turno ÷ duração total do turno × 100`.
                - 🟢 ≤ 10%: Ótimo · 🟡 10–20%: Atenção · 🔴 > 20%: Crítico.
            - **Maior Gap Médio** — Média do maior intervalo pontual sem evento por usuário.
              Útil para detectar ausências prolongadas durante o expediente.
                - 🟢 ≤ 15 min: Ótimo · 🟡 15–30 min: Atenção · 🔴 > 30 min: Crítico.

            > A linha **📅 Meta do período** exibida abaixo mostra o cálculo automático
            > da meta total: `meta diária × dias úteis no período` (domingos excluídos).
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
            - **Análise de Ociosidade** — Dois gráficos lado a lado:
                - **% do Turno Ocioso**: proporção do expediente sem evento por usuário.
                - **Maior Gap Intra-turno**: maior ausência pontual de cada pessoa.
              Ambos excluem automaticamente o almoço (gap ≥ 45 min).
            """
        )

    with st.expander("👥 Aba Performance"):
        st.markdown(
            """
            - **Score de Performance** — Indicador composto, normalizado de 0 a 100%:
              `Score = Peso Volume × (volume normalizado) + Peso Tempo × (1 − tempo normalizado)`
              Os pesos são configuráveis na sidebar em **⚖️ Pesos do Score**.
              Premia quem entrega **mais volume** com **menor tempo médio**.
                - 🟢 Verde: alto desempenho · 🟡 Amarelo: médio · 🔴 Vermelho: requer atenção.
            - **Atingimento da Meta (%)** — Compara o volume de cada usuário com a
              **meta do período** (diária × dias úteis). A linha de referência marca **100%**.
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

    with st.expander("🖨️ Aba Feedback"):
        st.markdown(
            """
            Ferramenta para o gestor preparar e imprimir um relatório de feedback individual.

            - Selecione o **funcionário**, informe o **gestor** e a **empresa/departamento**.
            - Preencha os campos de **pontos positivos**, **pontos de melhoria**,
              **metas acordadas** e **observações gerais**.
            - Clique em **Gerar Relatório**: um arquivo HTML é baixado com todas as métricas
              do funcionário (eventos, tempo médio, % da meta, score, % ocioso, maior gap).
            - Abra o arquivo no navegador e use **Ctrl+P** para imprimir ou salvar como PDF.
            - O documento inclui três campos de assinatura: **Visto**, **Gestor** e **Funcionário**.

            > O ranking exibido no relatório considera **todos os colaboradores** da base,
            > independentemente do filtro de usuário ativo no momento.
            """
        )

    with st.expander("🧭 Filtros (barra lateral)"):
        st.markdown(
            """
            Todos os filtros são **cumulativos** e impactam **todas as abas**:
            - **Usuários** — Restringe a análise a pessoas selecionadas.
            - **Tipo de Evento** — Foca em uma categoria específica de atividade.
            - **Cliente** — Restringe por cliente vinculado.
            - **Data** — Selecione uma data única ou um intervalo de datas.
              O filtro de data também recalcula automaticamente a **meta do período**
              (meta diária × dias úteis no intervalo, domingos excluídos).
            """
        )

    with st.expander("⚙️ Configurações (barra lateral)"):
        st.markdown(
            """
            - **Meta diária de eventos por usuário** — Define quantos eventos são esperados
              por dia útil. A meta total do período é calculada automaticamente.
            - **⚖️ Pesos do Score** — Controla o quanto o volume e o tempo médio pesam
              no score de performance. Os pesos são complementares (somam 100%).
            - **🎨 Aparência** — Alterna entre o tema **Escuro** (padrão) e **Claro**.
            """
        )

    st.info(
        "💡 **Dica:** Combine o **Heatmap** com o **Status por Faixa Horária** "
        "para identificar gargalos e propor realocações de equipe."
    )

# ----- TAB 6: FEEDBACK -----
with tab6:
    section("🖨️ Relatório de Feedback — Gestor × Funcionário")

    st.markdown(
        "Preencha os campos abaixo e clique em **Gerar Relatório** para baixar "
        "uma página pronta para impressão com os campos de assinatura."
    )

    # ── Cabeçalho do relatório ──────────────────────────────────────
    col_fb1, col_fb2 = st.columns(2)
    with col_fb1:
        usuario_fb   = st.selectbox("👤 Funcionário", sorted(df["user_name"].unique()), key="fb_user")
        gestor_nome  = st.text_input("🏢 Nome do Gestor", placeholder="Ex: João Silva")
    with col_fb2:
        empresa_nome = st.text_input("🏷️ Empresa / Departamento", placeholder="Ex: Operações — Setor A")
        data_fb      = st.date_input("📅 Data do Feedback", value=pd.Timestamp.today())

    st.markdown("---")

    # ── Campos de observação ────────────────────────────────────────
    col_obs1, col_obs2 = st.columns(2)
    with col_obs1:
        pontos_pos = st.text_area(
            "✅ Pontos Positivos",
            height=110,
            placeholder="Descreva os pontos fortes e conquistas do período...",
        )
    with col_obs2:
        pontos_mel = st.text_area(
            "🎯 Pontos de Melhoria",
            height=110,
            placeholder="Descreva as oportunidades de desenvolvimento...",
        )

    metas_acordadas = st.text_area(
        "📋 Metas Acordadas para o Próximo Período",
        height=90,
        placeholder="Ex: Aumentar volume de eventos em 15%, reduzir tempo médio para abaixo de 30s...",
    )

    observacoes_gerais = st.text_area(
        "🗒️ Observações Gerais",
        height=80,
        placeholder="Outras anotações relevantes para o feedback...",
    )

    st.markdown("---")

    # ── Cálculo das métricas do funcionário selecionado ─────────────
    df_fb = df[df["user_name"] == usuario_fb]

    if not df_fb.empty:
        total_ev_fb    = int(df_fb["event_count"].sum())
        tempo_medio_fb = round(df_fb["event_elapsed_time"].mean(), 2)
        meta_pct_fb    = round((total_ev_fb / META_TOTAL) * 100, 1)

        score_row = df_user[df_user["user_name"] == usuario_fb]["score"].values
        score_fb  = round(float(score_row[0]) * 100, 1) if len(score_row) else 0.0

        ocio_row_fb  = df_ocio[df_ocio["user_name"] == usuario_fb]
        ocio_pct_fb  = round(float(ocio_row_fb["pct_ocioso"].values[0]),  1) if len(ocio_row_fb) else 0.0
        ocio_gap_fb  = round(float(ocio_row_fb["maior_gap"].values[0]),   1) if len(ocio_row_fb) else 0.0

        # Cor / label do % ocioso
        if ocio_pct_fb > 20:
            ocio_pct_color, ocio_pct_label = "#DC2626", "Crítico"
        elif ocio_pct_fb > 10:
            ocio_pct_color, ocio_pct_label = "#D97706", "Atenção"
        else:
            ocio_pct_color, ocio_pct_label = "#16A34A", "Ótimo"

        # Cor / label do maior gap
        if ocio_gap_fb > 30:
            ocio_gap_color, ocio_gap_label = "#DC2626", "Crítico"
        elif ocio_gap_fb > 15:
            ocio_gap_color, ocio_gap_label = "#D97706", "Atenção"
        else:
            ocio_gap_color, ocio_gap_label = "#16A34A", "Ótimo"

        # Ranking calculado sobre TODOS os usuários (df_global), não só os filtrados
        df_user_global = df_global.groupby("user_name").agg({
            "event_count":        "sum",
            "event_elapsed_time": "mean",
        }).reset_index()
        max_vol_g  = df_user_global["event_count"].max()        or 1
        max_time_g = df_user_global["event_elapsed_time"].max() or 1
        df_user_global["score_volume"] = df_user_global["event_count"]        / max_vol_g
        df_user_global["score_tempo"]  = 1 - (df_user_global["event_elapsed_time"] / max_time_g)
        df_user_global["score"]        = (
            df_user_global["score_volume"] * peso_volume
            + df_user_global["score_tempo"] * peso_tempo
        )
        df_rank_fb = df_user_global.sort_values("score", ascending=False).reset_index(drop=True)
        rank_matches = df_rank_fb[df_rank_fb["user_name"] == usuario_fb].index
        rank_fb = int(rank_matches[0]) + 1 if len(rank_matches) else "—"
        total_uf   = len(df_rank_fb)

        if score_fb >= 70:
            class_fb    = "Alto Desempenho"
            class_color = "#3FB950"
            class_bg    = "#0d2e16"
        elif score_fb >= 40:
            class_fb    = "Desempenho Médio"
            class_color = "#F2B441"
            class_bg    = "#2e230a"
        else:
            class_fb    = "Requer Atenção"
            class_color = "#F85149"
            class_bg    = "#2e0d0c"

        # ── Preview no dashboard ────────────────────────────────────
        section("📊 Prévia das Métricas do Funcionário")

        pb1, pb2, pb3, pb4 = st.columns(4)
        pb1.metric("⚡ Total de Eventos",  f"{total_ev_fb:,}".replace(",", "."))
        pb2.metric("⏱️ Tempo Médio (s)",   f"{tempo_medio_fb}")
        pb3.metric("🎯 % da Meta",          f"{meta_pct_fb}%")
        pb4.metric("🏅 Score",              f"{score_fb}%")

        pb5, pb6 = st.columns(2)
        pb5.metric("⏸️ % Tempo Ocioso",    f"{ocio_pct_fb}%",
                   help="% do turno sem registro de eventos (almoço excluído)")
        pb6.metric("⚠️ Maior Gap Intra-turno", f"{ocio_gap_fb} min",
                   help="Maior intervalo pontual sem evento (almoço excluído)")

        st.markdown(
            f'<div style="margin:10px 0 18px 0; padding:12px 18px; border-radius:10px; '
            f'background:{class_bg}; border:1px solid {class_color}; '
            f'color:{class_color}; font-weight:600; font-size:1rem;">'
            f'Classificação: {class_fb} &nbsp;|&nbsp; Ranking: {rank_fb}º de {total_uf}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Botão de gerar relatório ────────────────────────────────
        if st.button("🖨️ Gerar Relatório para Impressão", type="primary", key="btn_print"):

            data_fmt = data_fb.strftime("%d/%m/%Y")

            # linha da meta: cor verde/vermelho
            meta_cor = "#16A34A" if meta_pct_fb >= 100 else ("#D97706" if meta_pct_fb >= 70 else "#DC2626")

            # Montar linhas de pontos positivos e de melhoria como <li>
            def lista_html(texto: str) -> str:
                if not texto.strip():
                    return "<li><em>Não informado</em></li>"
                return "".join(f"<li>{ln.strip()}</li>" for ln in texto.strip().splitlines() if ln.strip()) \
                    or "<li><em>Não informado</em></li>"

            html_pos = lista_html(pontos_pos)
            html_mel = lista_html(pontos_mel)
            html_met = lista_html(metas_acordadas)
            html_obs = observacoes_gerais.strip() or "<em>Nenhuma observação registrada.</em>"

            total_ev_fb_fmt = f"{total_ev_fb:,}".replace(",", ".")

            html_report = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Feedback de Produtividade — {usuario_fb}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1A202C;
    background: #fff;
    padding: 28px 36px;
    max-width: 820px;
    margin: auto;
  }}

  /* ── Cabeçalho ── */
  .header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 3px solid #0078D4; padding-bottom: 14px; margin-bottom: 20px;
  }}
  .header h1 {{ font-size: 20px; color: #0078D4; margin-bottom: 4px; }}
  .header .sub {{ font-size: 12px; color: #64748B; }}
  .header .badge {{
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 6px; padding: 6px 14px;
    font-size: 11px; color: #1D4ED8; text-align: center;
    white-space: nowrap;
  }}

  /* ── Info funcionário ── */
  .info-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 10px; margin-bottom: 18px;
  }}
  .info-cell {{
    border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px;
    background: #F8FAFC;
  }}
  .info-cell .label {{
    font-size: 10px; text-transform: uppercase; letter-spacing: .06em;
    color: #64748B; font-weight: 600; margin-bottom: 3px;
  }}
  .info-cell .value {{ font-size: 14px; font-weight: 700; color: #1A202C; }}

  /* ── KPI Cards ── */
  .kpi-row {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 10px; margin-bottom: 10px;
  }}
  .kpi-row-2 {{
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 10px; margin-bottom: 18px;
  }}
  .kpi {{
    border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px;
    text-align: center; background: #F8FAFC;
  }}
  .kpi .kpi-label {{
    font-size: 10px; text-transform: uppercase; color: #64748B;
    letter-spacing: .06em; font-weight: 600; margin-bottom: 6px;
  }}
  .kpi .kpi-value {{ font-size: 22px; font-weight: 800; color: #0078D4; }}
  .kpi .kpi-sub {{ font-size: 10px; color: #94A3B8; margin-top: 2px; }}

  /* ── Classificação ── */
  .classification {{
    border-radius: 8px; padding: 10px 18px; margin-bottom: 18px;
    display: flex; align-items: center; gap: 14px;
  }}
  .classification .cl-label {{
    font-size: 11px; text-transform: uppercase; letter-spacing: .07em; font-weight: 600; opacity: .75;
  }}
  .classification .cl-value {{ font-size: 16px; font-weight: 800; }}
  .classification .cl-rank {{ margin-left: auto; font-size: 13px; font-weight: 600; opacity: .8; }}

  /* ── Seções de texto ── */
  .section-title {{
    font-size: 12px; text-transform: uppercase; letter-spacing: .07em;
    font-weight: 700; color: #0078D4; margin: 16px 0 8px 0;
    padding-bottom: 5px; border-bottom: 1px solid #BFDBFE;
  }}
  .obs-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }}
  .obs-box {{
    border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px;
    background: #FAFAFA; min-height: 90px;
  }}
  .obs-box .obs-title {{
    font-size: 11px; font-weight: 700; color: #374151; margin-bottom: 7px;
  }}
  .obs-box ul {{ padding-left: 16px; }}
  .obs-box li {{ margin-bottom: 4px; line-height: 1.5; color: #374151; }}
  .obs-full {{
    border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px;
    background: #FAFAFA; margin-bottom: 12px; min-height: 70px;
    line-height: 1.6; color: #374151;
  }}

  /* ── Campos de assinatura ── */
  .sign-section {{ margin-top: 28px; }}
  .sign-title {{
    font-size: 11px; text-transform: uppercase; letter-spacing: .07em;
    font-weight: 700; color: #64748B; margin-bottom: 14px;
    border-top: 2px dashed #CBD5E1; padding-top: 14px;
  }}
  .sign-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
  .sign-box {{ text-align: center; }}
  .sign-box .sign-label {{
    font-size: 11px; text-transform: uppercase; letter-spacing: .07em;
    font-weight: 700; color: #374151; margin-bottom: 10px;
  }}
  .sign-line {{
    border-bottom: 1px solid #374151; margin: 0 10px 8px 10px; height: 40px;
  }}
  .sign-name {{
    font-size: 11px; color: #64748B; min-height: 16px;
  }}
  .sign-date-label {{
    font-size: 10px; color: #94A3B8; margin-top: 4px;
  }}
  .sign-date-box {{
    border: 1px solid #CBD5E1; border-radius: 4px; height: 22px;
    margin: 4px 30px 0 30px; display: flex; align-items: center; justify-content: center;
    font-size: 11px; color: #94A3B8;
  }}

  /* ── Rodapé ── */
  .footer {{
    margin-top: 24px; padding-top: 10px;
    border-top: 1px solid #E2E8F0;
    font-size: 10px; color: #94A3B8;
    display: flex; justify-content: space-between;
  }}

  /* ── Print ── */
  @media print {{
    body {{ padding: 10px 18px; }}
    .no-print {{ display: none !important; }}
    .sign-section {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>

<!-- BOTÃO DE IMPRESSÃO (some ao imprimir) -->
<div class="no-print" style="text-align:right; margin-bottom:16px;">
  <button onclick="window.print()" style="
    background:#0078D4; color:#fff; border:none; border-radius:8px;
    padding:10px 24px; font-size:14px; font-weight:600; cursor:pointer;
  ">🖨️ Imprimir / Salvar PDF</button>
</div>

<!-- CABEÇALHO -->
<div class="header">
  <div>
    <h1>📊 Relatório de Feedback de Produtividade</h1>
    <div class="sub">{empresa_nome or "Empresa / Departamento"} &nbsp;·&nbsp; Período filtrado no dashboard</div>
  </div>
  <div class="badge">
    Data do Feedback<br>
    <strong style="font-size:14px;">{data_fmt}</strong>
  </div>
</div>

<!-- INFORMAÇÕES DO FUNCIONÁRIO -->
<div class="info-grid">
  <div class="info-cell">
    <div class="label">Funcionário</div>
    <div class="value">{usuario_fb}</div>
  </div>
  <div class="info-cell">
    <div class="label">Gestor Responsável</div>
    <div class="value">{gestor_nome or "—"}</div>
  </div>
  <div class="info-cell">
    <div class="label">Empresa / Depto</div>
    <div class="value">{empresa_nome or "—"}</div>
  </div>
</div>

<!-- KPIs -->
<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">Total de Eventos</div>
    <div class="kpi-value">{total_ev_fb_fmt}</div>
    <div class="kpi-sub">no período filtrado</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Tempo Médio (s)</div>
    <div class="kpi-value">{tempo_medio_fb}</div>
    <div class="kpi-sub">por evento</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">% da Meta</div>
    <div class="kpi-value" style="color:{meta_cor};">{meta_pct_fb}%</div>
    <div class="kpi-sub">{META_DIARIA}/dia × {dias_uteis} dia(s) útil(is) = {META_TOTAL} eventos</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Score de Performance</div>
    <div class="kpi-value" style="color:{class_color};">{score_fb}%</div>
    <div class="kpi-sub">normalizado</div>
  </div>
</div>

<div class="kpi-row-2">
  <div class="kpi">
    <div class="kpi-label">⏸️ % do Turno Ocioso</div>
    <div class="kpi-value" style="color:{ocio_pct_color};">{ocio_pct_fb}%</div>
    <div class="kpi-sub">{ocio_pct_label} · almoço/pausas longas excluídos</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">⚠️ Maior Gap Intra-turno</div>
    <div class="kpi-value" style="color:{ocio_gap_color};">{ocio_gap_fb} min</div>
    <div class="kpi-sub">{ocio_gap_label} · maior intervalo pontual sem evento</div>
  </div>
</div>

<!-- CLASSIFICAÇÃO -->
<div class="classification" style="background:#f8fafc; border:2px solid {class_color}; border-radius:8px; padding:12px 18px; margin-bottom:18px; display:flex; align-items:center; gap:14px;">
  <div>
    <div class="cl-label">Classificação de Desempenho</div>
    <div class="cl-value" style="color:{class_color};">{class_fb}</div>
  </div>
  <div class="cl-rank">🏅 Ranking: {rank_fb}º de {total_uf} colaboradores</div>
</div>

<!-- OBSERVAÇÕES -->
<div class="section-title">Observações do Gestor</div>

<div class="obs-grid">
  <div class="obs-box">
    <div class="obs-title">✅ Pontos Positivos</div>
    <ul>{html_pos}</ul>
  </div>
  <div class="obs-box">
    <div class="obs-title">🎯 Pontos de Melhoria</div>
    <ul>{html_mel}</ul>
  </div>
</div>

<div class="section-title">Metas Acordadas — Próximo Período</div>
<div class="obs-full"><ul>{html_met}</ul></div>

<div class="section-title">Observações Gerais</div>
<div class="obs-full">{html_obs}</div>

<!-- ASSINATURAS -->
<div class="sign-section">
  <div class="sign-title">✍️ Assinaturas — Confirmação de Ciência</div>
  <div class="sign-grid">

    <div class="sign-box">
      <div class="sign-label">📋 Visto</div>
      <div class="sign-line"></div>
      <div class="sign-name">Responsável pelo Departamento / RH</div>
      <div class="sign-date-label">Data</div>
      <div class="sign-date-box">&nbsp;/&nbsp;&nbsp;&nbsp;/&nbsp;</div>
    </div>

    <div class="sign-box">
      <div class="sign-label">🏢 Gestor</div>
      <div class="sign-line"></div>
      <div class="sign-name">{gestor_nome or "________________________________"}</div>
      <div class="sign-date-label">Data</div>
      <div class="sign-date-box">&nbsp;/&nbsp;&nbsp;&nbsp;/&nbsp;</div>
    </div>

    <div class="sign-box">
      <div class="sign-label">👤 Funcionário</div>
      <div class="sign-line"></div>
      <div class="sign-name">{usuario_fb}</div>
      <div class="sign-date-label">Data</div>
      <div class="sign-date-box">&nbsp;/&nbsp;&nbsp;&nbsp;/&nbsp;</div>
    </div>

  </div>
</div>

<!-- RODAPÉ -->
<div class="footer">
  <span>Dashboard de Produtividade · Relatório gerado automaticamente</span>
  <span>Data: {data_fmt}</span>
</div>

</body>
</html>"""

            st.download_button(
                label="⬇️ Baixar Relatório HTML (abrir no navegador e imprimir)",
                data=html_report.encode("utf-8"),
                file_name=f"feedback_{usuario_fb.replace(' ', '_')}_{data_fb.strftime('%Y%m%d')}.html",
                mime="text/html",
                type="primary",
            )

            st.success(
                "✅ Relatório gerado! Clique no botão acima para baixar. "
                "Abra o arquivo no navegador e use **Ctrl+P** (ou o botão 🖨️ no topo da página) para imprimir."
            )

    else:
        st.warning(f"Nenhum dado encontrado para o usuário **{usuario_fb}** com os filtros atuais.")
