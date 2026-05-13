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
#  CONSTANTES DE NEGÓCIO — OCIOSIDADE / ALMOÇO
# =========================================================
ALMOCO_MIN_MIN  = 40   # gap mínimo (min) para ser considerado almoço
ALMOCO_MIN_MAX  = 60   # gap máximo (min) para ser considerado almoço (acima = ausência grave)
GAP_OCIOSO_MIN  = 15   # gap mínimo (min) para contar como ociosidade real
                        # gaps menores = ritmo normal de trabalho (ciclo, deslocamento)

def _eh_almoco(gap: float) -> bool:
    """True se o gap (em minutos) está na faixa de almoço válido (40–60 min)."""
    return ALMOCO_MIN_MIN <= gap <= ALMOCO_MIN_MAX

def _identificar_almoco(gaps_sorted: list) -> tuple:
    """
    Dado gaps_sorted (decrescente), retorna (almoco_min, gaps_intra).
    Descarta como almoço o MAIOR gap dentro da faixa [40, 60] min — apenas 1 vez.
    Gaps > 60 min são ausências graves e permanecem em gaps_intra.
    """
    alm_idx = next((i for i, g in enumerate(gaps_sorted) if _eh_almoco(g)), None)
    if alm_idx is not None:
        return gaps_sorted[alm_idx], gaps_sorted[:alm_idx] + gaps_sorted[alm_idx + 1:]
    return 0.0, gaps_sorted

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
    # Detecta automaticamente a aba com dados (ignora abas vazias).
    # Necessário pois o arquivo pode ter Sheet1 vazia antes da aba real.
    _xl    = pd.ExcelFile(io.BytesIO(file_bytes))
    _sheet = next(
        (s for s in _xl.sheet_names
         if not pd.read_excel(io.BytesIO(file_bytes), sheet_name=s, nrows=1).empty),
        _xl.sheet_names[0],   # fallback: primeira aba
    )
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=_sheet)

    # Normaliza nomes de colunas: minúsculas, sem colchetes, underscores
    df.columns = (
        df.columns.str.lower().str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
    )

    rename_dict = {
        "useruser_name":                       "user_name",
        "event_typeevent_type_name":           "event_type_name",
        "time_event_datetime_hour_interval":   "time_hour_interval",
        "time_event_datetime_key":             "time_key",      # HH:MM:SS exato
        "time_event_datetime_hour":            "time_hour",
        "calendar_event_datedate":             "date",
        "event_count":                         "event_count",
        "event_elapsed_time_avg":              "event_elapsed_time",
        "event_elapsed_time_hhmmss":           "event_elapsed_hhmmss",
        "clientclient_id":                     "client_id",
        "sitesite_country_id":                 "site_country_id",
        "sitesite_id":                         "site_id",
    }
    df = df.rename(columns=rename_dict)

    # ----- Remove movimentações automáticas do sistema -----
    if "user_name" in df.columns:
        df = df[df["user_name"].notna()]
        df = df[df["user_name"].astype(str).str.strip() != "?"]

    # ----- Parsing de date -----
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ─────────────────────────────────────────────────────────────────
    # PARSING DE HORA_INICIO / HORA_FIM
    #
    # Caminho 1 (preferido): time_key (HH:MM:SS) + date → datetime exato.
    #   Exemplo: date="2026-01-15" + time_key="09:32:45" → 2026-01-15 09:32:45
    #   Garante precisão de segundos e agrupamento correto por dia.
    #
    # Caminho 2 (fallback): extrai HH:MM do time_hour_interval.
    #   Usado quando time_key não está disponível.
    #   Regex aceita 1 ou 2 dígitos na hora (ex: "5:00-5:59" e "22:00-22:59").
    # ─────────────────────────────────────────────────────────────────

    has_time_key = (
        "time_key" in df.columns
        and "date" in df.columns
        and df["time_key"].notna().any()
    )

    if has_time_key:
        # Garante string limpa de time_key (pode vir como object, str ou time)
        tk_str   = df["time_key"].astype(str).str.strip().str.extract(
            r"(\d{1,2}:\d{2}:\d{2})", expand=False
        ).fillna(df["time_key"].astype(str).str.strip())

        # Garante string de date (NaT vira "NaT" → cai em errors="coerce")
        date_str = df["date"].dt.strftime("%Y-%m-%d")

        df["hora_inicio"] = pd.to_datetime(
            date_str + " " + tk_str, errors="coerce"
        )

        # hora_fim = inicio + elapsed_time (mín. 5 min para visibilidade no Gantt)
        if "event_elapsed_time" in df.columns:
            elapsed_s = df["event_elapsed_time"].fillna(0).clip(lower=0)
        else:
            elapsed_s = pd.Series(0, index=df.index, dtype=float)

        df["hora_fim"] = df["hora_inicio"] + pd.to_timedelta(
            elapsed_s.clip(lower=300), unit="s"
        )

    elif "time_hour_interval" in df.columns:
        # ── Fallback: usa o intervalo horário (ex: "5:00-5:59", "22:00-22:59") ──
        # Converte para string antes de qualquer operação .str (evita o erro
        # "Can only use .str accessor with string values!").
        # Regex \d{1,2}:\d{2} aceita hora com 1 ou 2 dígitos.
        hi_str = df["time_hour_interval"].astype(str)
        df["hora_inicio"] = pd.to_datetime(
            hi_str.str.extract(r"(\d{1,2}:\d{2})", expand=False),
            format="%H:%M", errors="coerce",
        )
        df["hora_fim"] = pd.to_datetime(
            hi_str.str.extract(r"-(\d{1,2}:\d{2})", expand=False),
            format="%H:%M", errors="coerce",
        )

    # Remove linhas sem hora_inicio válida e ordena
    if "hora_inicio" in df.columns:
        df = df[df["hora_inicio"].notna()]
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

# Filtro de Site — exibido só quando há mais de um site
if "site_id" in df.columns and df["site_id"].nunique() > 1:
    sites = st.sidebar.multiselect(
        "Site",
        sorted(df["site_id"].dropna().unique()),
        placeholder="Todos os sites",
    )
else:
    sites = []

# Filtro de data — usa hora_inicio quando time_key disponível (mais preciso)
_date_col_avail = "hora_inicio" in df.columns and df["hora_inicio"].notna().any()
if _date_col_avail or "date" in df.columns:
    datas = st.sidebar.date_input("Data", [])
    if datas:
        if isinstance(datas, (list, tuple)) and len(datas) == 2:
            start = pd.to_datetime(datas[0])
            end   = pd.to_datetime(datas[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            if _date_col_avail:
                df = df[(df["hora_inicio"] >= start) & (df["hora_inicio"] <= end)]
            else:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df[(df["date"] >= start) & (df["date"] <= end)]
        elif len(datas) == 1:
            d = pd.to_datetime(datas[0])
            if _date_col_avail:
                df = df[df["hora_inicio"].dt.normalize() == d]
            else:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df[df["date"].dt.normalize() == d]

if eventos:  df = df[df["event_type_name"].isin(eventos)]
if clientes: df = df[df["client_id"].isin(clientes)]
if sites and "site_id" in df.columns:
    df = df[df["site_id"].isin(sites)]

# Salva ANTES do filtro de usuário — usado para ranking global no relatório de feedback
df_global = df.copy()

if usuarios: df = df[df["user_name"].isin(usuarios)]

# =========================================================
# 🎯 CONFIGURAÇÕES
# FIX: pesos do score expostos como sliders para o gestor calibrar.
# =========================================================
st.sidebar.markdown('<div class="sb-section-label">🎯 Configurações</div>', unsafe_allow_html=True)
META_DIARIA = st.sidebar.number_input("Meta diária de eventos por usuário", value=100, min_value=1, help="Quantidade de eventos esperada por dia útil (domingos excluídos automaticamente)")

GAP_OCIOSO_MIN = st.sidebar.number_input(
    "Limiar de gap ocioso (min)",
    min_value=5, max_value=60, value=15, step=5,
    help=(
        "Gaps menores que este valor são ritmo normal de trabalho (ciclo, deslocamento) "
        "e NÃO contam como ociosidade. "
        "Gaps ≥ este valor contam. Padrão: 15 min."
    ),
)

with st.sidebar.expander("⚖️ Pesos do Score"):
    peso_volume = st.slider(
        "Peso — Volume (%)", min_value=0, max_value=90, value=55, step=5,
    ) / 100
    peso_ocio_raw = st.slider(
        "Peso — Ociosidade (%)", min_value=0, max_value=40, value=15, step=5,
        help="Penaliza usuários com alto tempo ocioso. 0% = ociosidade não afeta o score.",
    ) / 100
    peso_tempo = max(round(1 - peso_volume - peso_ocio_raw, 2), 0.0)
    peso_ocio  = round(1 - peso_volume - peso_tempo, 2)
    st.caption(
        f"Velocidade: {int(peso_tempo * 100)}% (complementar automático) · "
        f"Ociosidade: {int(peso_ocio * 100)}%"
    )

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
# META_TOTAL = META_DIÁRIA × dias_uteis
# =========================================================
# Usa hora_inicio (exato) para derivar datas únicas — mais confiável que date separado
if "hora_inicio" in df.columns and df["hora_inicio"].notna().any():
    datas_unicas = df["hora_inicio"].dt.normalize().dropna().unique()
    dias_uteis   = int((pd.DatetimeIndex(datas_unicas).dayofweek != 6).sum())
elif "date" in df.columns:
    datas_unicas = pd.to_datetime(df["date"].dropna().dt.normalize().unique())
    dias_uteis   = int((datas_unicas.dayofweek != 6).sum())
else:
    dias_uteis = 1

dias_uteis  = max(dias_uteis, 1)          # garante mínimo 1 dia
META_TOTAL  = META_DIARIA * dias_uteis    # meta real do período selecionado

# =========================================================
# ⏸️ TEMPO Ocioso (% do turno + maior gap intra-turno)
#
# Para cada usuário:
#   1. Calcula todos os gaps positivos entre hora_fim[i] e hora_inicio[i+1]
#   2. Identifica o gap na faixa [40–60 min] → descartado como almoço (1 vez por dia)
#   3. Dos gaps restantes:
#        pct_ocioso = soma(gaps) / duração_total_turno × 100
#        maior_gap  = max(gaps)  — maior ausência pontual intra-turno
# =========================================================
def calc_ociosidade(df_in: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula ociosidade por usuário usando hora_inicio (exato, de time_key).

    Regras de negócio:
      • Agrupa por (user_name, dia) — dia derivado de hora_inicio.dt.normalize().
      • Usa cálculo vetorizado com .shift() — muito mais eficiente que loops Python.
      • Gap = diferença entre hora_inicio de eventos consecutivos do mesmo user/dia.
      • O maior gap na faixa [40–60 min] do dia = almoço (excluído da ociosidade, 1 vez).
      • Gaps > 60 min = ausências graves (contam como ociosidade).
      • Turno efetivo = span total do dia − almoço.
      • pct_ocioso limitado a 100%.
    """
    if df_in.empty or "hora_inicio" not in df_in.columns:
        return pd.DataFrame(
            columns=["user_name", "pct_ocioso", "maior_gap", "n_ausencias_graves"]
        )

    df_work = df_in[["user_name", "hora_inicio", "event_elapsed_time", "event_count"]].copy()

    # hora_fim_real = inicio + (n_eventos × tempo_médio_por_evento)
    # Desconta o tempo efetivo de trabalho do gap, evitando que o processamento
    # seja contabilizado como ociosidade.
    elapsed_total_s = (
        df_work["event_elapsed_time"].fillna(0).clip(lower=0) *
        df_work["event_count"].fillna(1).clip(lower=1)
    )
    df_work["_hora_fim_real"] = df_work["hora_inicio"] + pd.to_timedelta(elapsed_total_s, unit="s")

    df_work["_date"] = df_work["hora_inicio"].dt.normalize()
    df_work = df_work.sort_values(["user_name", "_date", "hora_inicio"])

    # gap = início do próximo evento − fim real do evento atual (≥ 0)
    df_work["_next_inicio"] = df_work.groupby(["user_name", "_date"])["hora_inicio"].shift(-1)
    df_work["_gap_min"] = (
        (df_work["_next_inicio"] - df_work["_hora_fim_real"]).dt.total_seconds() / 60
    ).clip(lower=0)

    rows = []
    for (user, date), grp in df_work.groupby(["user_name", "_date"]):
        # turno vai do início do primeiro evento ao fim real do último
        turno_min = (
            grp["_hora_fim_real"].max() - grp["hora_inicio"].min()
        ).total_seconds() / 60
        if turno_min <= 0:
            continue

        gaps = grp["_gap_min"].dropna()
        gaps = gaps[gaps > 0].tolist()

        if not gaps:
            rows.append({"user_name": user, "pct_ocioso": 0.0,
                         "maior_gap": 0.0, "n_ausencias_graves": 0})
            continue

        gaps_sorted = sorted(gaps, reverse=True)
        # Almoço: maior gap na faixa [40–60 min], descartado 1 vez por dia
        almoco_min, gaps_intra = _identificar_almoco(gaps_sorted)

        turno_efetivo      = max(turno_min - almoco_min, 1.0)
        # Apenas gaps >= GAP_OCIOSO_MIN contam como ociosidade real;
        # gaps menores são ritmo normal de trabalho (ciclo, deslocamento).
        total_ocio         = sum(g for g in gaps_intra if g >= GAP_OCIOSO_MIN)
        maior_gap          = max(gaps_intra) if gaps_intra else 0.0
        pct_ocioso         = min(round((total_ocio / turno_efetivo) * 100, 1), 100.0)
        # Ausência grave: gap > 60 min que NÃO foi o almoço
        n_ausencias_graves = sum(1 for g in gaps_intra if g > ALMOCO_MIN_MAX)

        rows.append({
            "user_name":          user,
            "pct_ocioso":         pct_ocioso,
            "maior_gap":          round(maior_gap, 1),
            "n_ausencias_graves": n_ausencias_graves,
        })

    if not rows:
        return pd.DataFrame(
            columns=["user_name", "pct_ocioso", "maior_gap", "n_ausencias_graves"]
        )

    df_r = pd.DataFrame(rows)
    return (
        df_r.groupby("user_name")
        .agg(
            pct_ocioso         =("pct_ocioso",         "mean"),
            maior_gap          =("maior_gap",           "mean"),
            n_ausencias_graves =("n_ausencias_graves",  "sum"),
        )
        .round({"pct_ocioso": 1, "maior_gap": 1})
        .reset_index()
    )

# =========================================================
# ⏸️ OCIOSIDADE DIÁRIA — detalhamento por dia para o feedback
# =========================================================
def calc_ociosidade_diaria(df_in: pd.DataFrame, user_name: str) -> pd.DataFrame:
    """
    Retorna detalhamento de ociosidade dia a dia para um usuário, usando
    hora_inicio exato (de time_key). Usado na aba de Feedback.

    Colunas retornadas:
      data, primeiro_evento, ultimo_evento, turno_min,
      pct_ocioso, maior_gap, total_ocio_min,
      almoco_min, n_ausencias_graves, gaps_detalhe
    """
    cols = [
        "data", "primeiro_evento", "ultimo_evento", "turno_min",
        "pct_ocioso", "maior_gap", "total_ocio_min",
        "almoco_min", "n_ausencias_graves", "gaps_detalhe",
    ]
    df_u = df_in[df_in["user_name"] == user_name].copy()
    if df_u.empty or "hora_inicio" not in df_u.columns:
        return pd.DataFrame(columns=cols)

    elapsed_total_s = (
        df_u["event_elapsed_time"].fillna(0).clip(lower=0) *
        df_u["event_count"].fillna(1).clip(lower=1)
    )
    df_u["_hora_fim_real"] = df_u["hora_inicio"] + pd.to_timedelta(elapsed_total_s, unit="s")

    df_u["_date"] = df_u["hora_inicio"].dt.normalize()
    df_u = df_u.sort_values(["_date", "hora_inicio"])
    df_u["_next"] = df_u.groupby("_date")["hora_inicio"].shift(-1)
    df_u["_gap_min"] = (
        (df_u["_next"] - df_u["_hora_fim_real"]).dt.total_seconds() / 60
    ).clip(lower=0)

    rows = []
    for dia, grp in df_u.groupby("_date"):
        turno_min = (
            grp["_hora_fim_real"].max() - grp["hora_inicio"].min()
        ).total_seconds() / 60
        if turno_min <= 0:
            continue

        primeiro = grp["hora_inicio"].min()
        ultimo   = grp["hora_inicio"].max()

        gaps = grp["_gap_min"].dropna()
        gaps = gaps[gaps > 0].tolist()

        if not gaps:
            rows.append({
                "data": dia, "primeiro_evento": primeiro, "ultimo_evento": ultimo,
                "turno_min": round(turno_min, 1),
                "pct_ocioso": 0.0, "maior_gap": 0.0, "total_ocio_min": 0.0,
                "almoco_min": 0.0, "n_ausencias_graves": 0, "gaps_detalhe": "—",
            })
            continue

        gaps_sorted = sorted(gaps, reverse=True)
        # Almoço: maior gap na faixa [40–60 min], descartado 1 vez por dia
        almoco_min, gaps_intra = _identificar_almoco(gaps_sorted)

        turno_efetivo      = max(turno_min - almoco_min, 1.0)
        total_ocio         = sum(g for g in gaps_intra if g >= GAP_OCIOSO_MIN)
        maior_gap          = max(gaps_intra) if gaps_intra else 0.0
        pct_ocioso         = min(round((total_ocio / turno_efetivo) * 100, 1), 100.0)
        n_ausencias_graves = sum(1 for g in gaps_intra if g > ALMOCO_MIN_MAX)

        gaps_visiveis = sorted([g for g in gaps_intra if g > 5], reverse=True)
        if gaps_visiveis:
            gaps_detalhe = ", ".join(f"{g:.0f} min" for g in gaps_visiveis[:6])
            if len(gaps_visiveis) > 6:
                gaps_detalhe += f" (+{len(gaps_visiveis) - 6} menores)"
        else:
            gaps_detalhe = "Nenhum gap > 5 min"

        rows.append({
            "data":               dia,
            "primeiro_evento":    primeiro,
            "ultimo_evento":      ultimo,
            "turno_min":          round(turno_min, 1),
            "pct_ocioso":         pct_ocioso,
            "maior_gap":          round(maior_gap, 1),
            "total_ocio_min":     round(total_ocio, 1),
            "almoco_min":         round(almoco_min, 1),
            "n_ausencias_graves": n_ausencias_graves,
            "gaps_detalhe":       gaps_detalhe,
        })

    if not rows:
        return pd.DataFrame(columns=cols)

    return pd.DataFrame(rows).sort_values("data").reset_index(drop=True)


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

<<<<<<<< HEAD:dashboard_produtividade_5.py
# Incorpora ociosidade: 0% ocioso → score_ocio = 1.0 | 100% ocioso → 0.0
df_user = df_user.merge(df_ocio[["user_name", "pct_ocioso"]], on="user_name", how="left")
df_user["pct_ocioso"] = df_user["pct_ocioso"].fillna(0)
df_user["score_ocio"] = 1 - (df_user["pct_ocioso"] / 100)

df_user["score"]  = (
    df_user["score_volume"] * peso_volume
    + df_user["score_tempo"]  * peso_tempo
    + df_user["score_ocio"]   * peso_ocio
)
df_user["%meta"]  = df_user["event_count"] / META_TOTAL

========
>>>>>>>> 590f6c089b19dfbc27a61a735b8a287eb301fcfa:scripts/dashboard_produtividade_6.py
# =========================================================
# 🧱 GARGALO
# =========================================================
gargalo = df.groupby("time_hour_interval")["event_count"].sum().reset_index()
media   = gargalo["event_count"].mean()
gargalo["status"] = gargalo["event_count"].apply(
    lambda x: "🔥 Pico" if x > media * 1.5 else ("🕳️ Vale" if x < media * 0.5 else "✅ OK")
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
        fig_vol.update_layout(xaxis=dict(tickangle=-35, tickfont=dict(size=11)))
        st.plotly_chart(style_fig(fig_vol, 380), use_container_width=True)

    with col2:
        section("Status por Faixa Horária")
        status_cor = {"🔥 Pico": COLORS["danger"], "🕳️ Vale": COLORS["warning"], "✅ OK": COLORS["success"]}
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
        f"Apenas gaps ≥ {GAP_OCIOSO_MIN} min contam como ociosidade (gaps menores = ritmo de trabalho). "
        "Almoço: gap entre 40–60 min, descartado 1 vez/dia. "
        "Gaps > 60 min = ausência grave."
    )
    if not df_ocio.empty:
        # Ausências graves: gaps > 60 min que NÃO foram o almoço
        total_ausencias = int(df_ocio["n_ausencias_graves"].sum()) if "n_ausencias_graves" in df_ocio.columns else 0
        if total_ausencias > 0:
            s = "s" if total_ausencias > 1 else ""
            st.warning(
                f"⚠️ {total_ausencias} ausência{s} grave{s} detectada{s} no período "
                f"(gap > 60 min além do almoço — ausência não justificada). "
                f"Use a aba Jornada para ver o dia/horário exato."
            )

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
            st.caption("Quanto do horário de trabalho ficou sem registro de eventos (média diária por usuário)")
            df_pct = df_ocio.sort_values("pct_ocioso", ascending=False)
            _pct_ymax = max(df_pct["pct_ocioso"].max() * 1.2, 10) if not df_pct.empty else 10
            fig_pct = go.Figure(go.Bar(
                x=df_pct["user_name"],
                y=df_pct["pct_ocioso"],
                marker_color=[cor_pct(v) for v in df_pct["pct_ocioso"]],
                text=df_pct["pct_ocioso"].apply(lambda v: f"{v}%"),
                textposition="outside",
                cliponaxis=False,
            ))
            fig_pct.add_hline(
                y=ocio_pct_geral, line_dash="dash", line_color=COLORS["text_muted"],
                annotation_text=f"Média: {ocio_pct_geral}%",
                annotation_font_color=COLORS["text_muted"],
            )
            fig_pct.update_layout(xaxis_title="", yaxis_title="% ocioso",
                                  yaxis=dict(range=[0, _pct_ymax]))
            st.plotly_chart(style_fig(fig_pct, 340), use_container_width=True)
            leg1, leg2, leg3 = st.columns(3)
            leg1.markdown(f'<span style="color:{COLORS["success"]}; font-weight:600;">● ≤ 10%</span> Ótimo', unsafe_allow_html=True)
            leg2.markdown(f'<span style="color:{COLORS["warning"]}; font-weight:600;">● 10–20%</span> Atenção', unsafe_allow_html=True)
            leg3.markdown(f'<span style="color:{COLORS["danger"]}; font-weight:600;">● > 20%</span> Crítico', unsafe_allow_html=True)

        with col_o2:
            st.markdown(f'<div style="font-size:0.88rem;font-weight:600;color:{COLORS["text"]};margin-bottom:4px;">Gap Máximo Médio por Usuário (min)</div>', unsafe_allow_html=True)
            st.caption("Média do maior gap intra-turno por dia — almoço (40–60 min) excluído")
            df_gap = df_ocio.sort_values("maior_gap", ascending=False)
            _gap_ymax = max(df_gap["maior_gap"].max() * 1.2, 10) if not df_gap.empty else 10
            fig_gap = go.Figure(go.Bar(
                x=df_gap["user_name"],
                y=df_gap["maior_gap"],
                marker_color=[cor_gap(v) for v in df_gap["maior_gap"]],
                text=df_gap["maior_gap"].apply(lambda v: f"{v} min"),
                textposition="outside",
                cliponaxis=False,
            ))
            fig_gap.add_hline(
                y=ocio_gap_geral, line_dash="dash", line_color=COLORS["text_muted"],
                annotation_text=f"Média: {ocio_gap_geral} min",
                annotation_font_color=COLORS["text_muted"],
            )
            fig_gap.update_layout(xaxis_title="", yaxis_title="minutos",
                                  yaxis=dict(range=[0, _gap_ymax]))
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
            hover_name="user_name", text="user_name",
            labels={"event_elapsed_time": "Tempo médio (s)", "event_count": "Eventos"},
        )
        fig_sc.update_traces(textposition="top center", textfont=dict(size=10, color=COLORS["text_muted"]))
        st.plotly_chart(style_fig(fig_sc, 360), use_container_width=True)

# ----- TAB 3: JORNADA -----
with tab3:
    section("Resumo de Jornada por Usuário × Dia")

    df_turno = df.copy()
    df_turno["_date"] = df_turno["hora_inicio"].dt.normalize()

    # ── Calcula gaps por (user, dia) de forma vetorizada ──
    df_turno_s = df_turno.sort_values(["user_name", "_date", "hora_inicio"])

    _et_s = (
        df_turno_s["event_elapsed_time"].fillna(0).clip(lower=0) *
        df_turno_s["event_count"].fillna(1).clip(lower=1)
    )
    df_turno_s["_hora_fim_real"] = df_turno_s["hora_inicio"] + pd.to_timedelta(_et_s, unit="s")

    df_turno_s["_next"] = df_turno_s.groupby(["user_name", "_date"])["hora_inicio"].shift(-1)
    df_turno_s["_gap"]  = (
        (df_turno_s["_next"] - df_turno_s["_hora_fim_real"]).dt.total_seconds() / 60
    ).clip(lower=0)

    # Agrega por user/dia: primeiro/ultimo baseados em hora_inicio para exibição;
    # duracao inclui o processamento do último evento (_hora_fim_real)
    turno_grp = df_turno_s.groupby(["user_name", "_date"]).agg(
        primeiro=("hora_inicio",     "min"),
        ultimo=  ("hora_inicio",     "max"),
        _fim_real=("_hora_fim_real", "max"),
    ).reset_index()
    turno_grp["duracao_min"] = (
        (turno_grp["_fim_real"] - turno_grp["primeiro"]).dt.total_seconds() / 60
    ).round(1)

    # Maior gap e total ocioso por user/dia (almoço = faixa 40–60 min, 1 vez)
    def _resumo_gaps(grp):
        gs = grp["_gap"].dropna()
        gs = gs[gs > 0].tolist()
        if not gs:
            return pd.Series({"almoco_min": 0.0, "total_ocio_min": 0.0, "maior_gap_min": 0.0})
        gs_s = sorted(gs, reverse=True)
        alm, intra = _identificar_almoco(gs_s)
        return pd.Series({
            "almoco_min":     round(alm, 1),
            "total_ocio_min": round(sum(g for g in intra if g >= GAP_OCIOSO_MIN), 1),
            "maior_gap_min":  round(max(intra) if intra else 0.0, 1),
        })

    gap_resumo = df_turno_s.groupby(["user_name", "_date"]).apply(
        _resumo_gaps, include_groups=False
    ).reset_index()
    turno_grp = turno_grp.merge(gap_resumo, on=["user_name", "_date"], how="left")
    turno_grp["pct_ocioso"] = (
        turno_grp["total_ocio_min"]
        / (turno_grp["duracao_min"] - turno_grp["almoco_min"]).clip(lower=1)
        * 100
    ).clip(upper=100).round(1)

    fmt = "%H:%M:%S" if "time_key" in df.columns else "%H:%M"
    turno_fmt = turno_grp.copy()
    turno_fmt["Usuário"]       = turno_fmt["user_name"]
    turno_fmt["Data"]          = turno_fmt["_date"].dt.strftime("%d/%m/%Y")
    turno_fmt["1º Evento"]     = turno_fmt["primeiro"].dt.strftime(fmt)
    turno_fmt["Último Evento"] = turno_fmt["ultimo"].dt.strftime(fmt)
    turno_fmt["Duração"]       = turno_fmt["duracao_min"].apply(
        lambda v: f"{int(v//60)}h{int(v%60):02d}min"
    )
    turno_fmt["Almoço (min)"]     = turno_fmt["almoco_min"].apply(
        lambda v: f"{v:.0f}" if v > 0 else "—"
    )
    turno_fmt["Ocioso (min)"]     = turno_fmt["total_ocio_min"]
    turno_fmt["Maior Gap (min)"]  = turno_fmt["maior_gap_min"]
    turno_fmt["% Ocioso"]         = turno_fmt["pct_ocioso"].apply(lambda v: f"{v}%")

    # Filtros da tabela de jornada
    _jorn_users = st.multiselect(
        "Filtrar usuários (jornada)", sorted(df["user_name"].unique()),
        placeholder="Todos", key="jorn_users",
    )
    _jorn_mask = turno_fmt["Usuário"].isin(_jorn_users) if _jorn_users else slice(None)
    st.dataframe(
        turno_fmt.loc[_jorn_mask, [
            "Usuário", "Data", "1º Evento", "Último Evento",
            "Duração", "Almoço (min)", "Ocioso (min)", "Maior Gap (min)", "% Ocioso"
        ]].sort_values(["Usuário", "Data"]),
        use_container_width=True, hide_index=True,
    )
    csv_jorn = turno_fmt[[
        "Usuário", "Data", "1º Evento", "Último Evento",
        "Duração", "Almoço (min)", "Ocioso (min)", "Maior Gap (min)", "% Ocioso"
    ]].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar Jornada CSV", csv_jorn, "jornada.csv", "text/csv")

    st.markdown("---")
    section("Timeline de Atividade — por Usuário e Dia")
    st.caption(
        "Selecione um usuário e um dia específico. "
    )

    col_tl1, col_tl2 = st.columns([2, 2])
    with col_tl1:
        usuario_timeline = st.selectbox(
            "Usuário", sorted(df["user_name"].unique()), key="tl_user"
        )
    with col_tl2:
        # Datas disponíveis para o usuário selecionado
        _datas_user = sorted(
            df[df["user_name"] == usuario_timeline]["hora_inicio"]
            .dt.normalize().dt.date.unique()
        )
        dia_timeline = st.selectbox(
            "Dia", _datas_user,
            format_func=lambda d: d.strftime("%d/%m/%Y"),
            key="tl_date",
        )

    # Filtra somente o dia selecionado
    _dia_ts   = pd.Timestamp(dia_timeline)
    df_tl     = df[
        (df["user_name"] == usuario_timeline) &
        (df["hora_inicio"].dt.normalize() == _dia_ts)
    ].copy().sort_values("hora_inicio").reset_index(drop=True)

    if df_tl.empty:
        st.info("Nenhum evento encontrado para esse usuário nesse dia.")
    else:
        # hora_fim_real = descontando o tempo de processamento dos eventos
        _tl_elapsed_s = (
            df_tl["event_elapsed_time"].fillna(0).clip(lower=0) *
            df_tl["event_count"].fillna(1).clip(lower=1)
        )
        df_tl["_hora_fim_real"] = df_tl["hora_inicio"] + pd.to_timedelta(_tl_elapsed_s, unit="s")
        df_tl["_next_inicio"]   = df_tl["hora_inicio"].shift(-1)

        # gap = início do próximo evento − fim real do evento atual (≥ 0)
        df_tl["_gap_min"] = (
            (df_tl["_next_inicio"] - df_tl["_hora_fim_real"]).dt.total_seconds() / 60
        ).clip(lower=0)

        # Métricas do dia
        _gaps_dia = df_tl["_gap_min"].dropna()
        _gaps_pos = _gaps_dia[_gaps_dia > 0].tolist()
        if _gaps_pos:
            _gs = sorted(_gaps_pos, reverse=True)
            _alm, _intra = _identificar_almoco(_gs)
        else:
            _alm, _intra = 0.0, []
        _turno    = (df_tl["_hora_fim_real"].max() - df_tl["hora_inicio"].min()).total_seconds() / 60
        _ocio_tot = sum(g for g in _intra if g >= GAP_OCIOSO_MIN)
        _tef      = max(_turno - _alm, 1.0)
        _pct_ocio = min(round(_ocio_tot / _tef * 100, 1), 100.0)
        _maior    = max(_intra) if _intra else 0.0
        _n_aus    = sum(1 for g in _intra if g > ALMOCO_MIN_MAX)

        mk1, mk2, mk3, mk4 = st.columns(4)
        mk1.metric("🕐 1º Evento",  df_tl["hora_inicio"].min().strftime(fmt))
        mk2.metric("🕔 Último",     df_tl["hora_inicio"].max().strftime(fmt))
        mk3.metric("⏸️ % Ocioso",   f"{_pct_ocio}%")
        mk4.metric("⚠️ Maior Gap",  f"{_maior:.0f} min")

        # ── Timeline Gantt ──────────────────────────────────────────
        fig_tl = px.timeline(
            df_tl, x_start="hora_inicio", x_end="hora_fim",
            y="event_type_name", color="event_count",
            color_continuous_scale=[[0, COLORS["primary"]], [1, COLORS["accent"]]],
            hover_data=["event_count", "event_elapsed_time", "_gap_min"],
            labels={"_gap_min": "Gap até próx. (min)"},
        )
        fig_tl.update_yaxes(autorange="reversed")

        # Adiciona vrect somente para gaps significativos (> 15 min)
        # x0 = fim real do evento (após descontar processamento), x1 = início do próximo
        _danger_r  = f"rgba({int(COLORS['danger'][1:3],16)},{int(COLORS['danger'][3:5],16)},{int(COLORS['danger'][5:7],16)},0.20)"
        _warn_r    = f"rgba({int(COLORS['warning'][1:3],16)},{int(COLORS['warning'][3:5],16)},{int(COLORS['warning'][5:7],16)},0.15)"
        _neutral_r = "rgba(120,120,120,0.10)"

        for i, row in df_tl[df_tl["_gap_min"] > 15].iterrows():
            g = row["_gap_min"]
            x0 = row["_hora_fim_real"]
            x1 = row["_next_inicio"]
            if pd.isna(x1):
                continue
            if _alm > 0 and g == _alm:
                fc, lbl = _neutral_r, f"🍽 Almoço: {g:.0f} min"
            elif g > ALMOCO_MIN_MAX:
                fc, lbl = _danger_r, f"🔴 Ausência: {g:.0f} min"
            else:
                fc, lbl = _warn_r, f"🟡 Gap: {g:.0f} min"
            fig_tl.add_vrect(
                x0=x0, x1=x1, fillcolor=fc, line_width=0,
                annotation_text=lbl, annotation_font_size=9,
                annotation_font_color=COLORS["text_muted"],
            )

        st.plotly_chart(style_fig(fig_tl, 440), use_container_width=True)

        # Tabela de gaps do dia
        if _gaps_pos:
            with st.expander("📋 Gaps detectados neste dia"):
                _gap_rows = []
                for i, row in df_tl[df_tl["_gap_min"].notna()].iterrows():
                    g = row["_gap_min"]
                    if g <= 0: continue
                    tipo = "🍽 Almoço"   if (_alm > 0 and g == _alm)  else \
                           "🔴 Ausência" if g > ALMOCO_MIN_MAX          else \
                           "🟡 Atenção"  if g >= 15                     else \
                           "✅ Normal"
                    _gap_rows.append({
                        "Início": row["hora_inicio"].strftime(fmt),
                        "Retorno": row["_next_inicio"].strftime(fmt) if pd.notna(row["_next_inicio"]) else "—",
                        "Gap (min)": round(g, 1),
                        "Classificação": tipo,
                    })
                if _gap_rows:
                    st.dataframe(
                        pd.DataFrame(_gap_rows).sort_values("Gap (min)", ascending=False),
                        use_container_width=True, hide_index=True,
                    )

# ----- TAB 4: DADOS -----
with tab4:
    section("Base de Dados Filtrada")
    st.caption(f"{len(df):,} registros".replace(",", "."))
    colunas_visiveis = [c for c in df.columns if c not in ("hora_inicio", "hora_fim", "_date")]
    st.dataframe(df[colunas_visiveis], use_container_width=True, hide_index=True)

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
            Calculados automaticamente para toda a equipe.
            O **maior gap entre 40 e 60 min** de cada dia é descartado como almoço (uma vez por dia).
            Gaps **> 60 min** no mesmo dia são tratados como **ausência grave** e contam
            como ociosidade real. O % é calculado sobre o **turno efetivo** (total − almoço).

            - **% Tempo Ocioso** — Percentual médio do turno sem nenhum evento registrado.
              Fórmula: `soma dos gaps intra-turno ÷ turno efetivo × 100`.
                - 🟢 ≤ 10%: Ótimo · 🟡 10–20%: Atenção · 🔴 > 20%: Crítico.
            - **Gap Máximo Médio** — Média do maior gap intra-turno por dia por usuário (almoço excluído).
              Útil para detectar ausências prolongadas durante o expediente.
                - 🟢 ≤ 15 min: Ótimo · 🟡 15–30 min: Atenção · 🔴 > 30 min: Crítico.

            > Se forem detectadas **ausências graves** (gaps > 60 min fora do almoço),
            > um aviso em amarelo aparece acima dos gráficos de ociosidade.
            > Use a **Timeline Individual** (Aba Jornada) para identificar o horário exato.
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
                - **% do Turno Ocioso**: proporção do expediente sem evento por usuário (média diária).
                - **Gap Máximo Médio**: média do maior gap intra-turno por dia por usuário.
              Ambos excluem automaticamente o almoço (gap entre 40–60 min, 1 vez por dia).
            """
        )

    with st.expander("👥 Aba Performance"):
        st.markdown(
            """
            - **Score de Performance** — Indicador composto, normalizado de 0 a 100%:
              `Score = Peso Volume × (volume normalizado) + Peso Velocidade × (1 − tempo normalizado) + Peso Ociosidade × (1 − % ocioso)`
              Os pesos são configuráveis na sidebar em **⚖️ Pesos do Score**.
              Premia quem entrega **mais volume** com **menor tempo médio** e **menor ociosidade**.
                - 🟢 Verde: alto desempenho · 🟡 Amarelo: médio · 🔴 Vermelho: requer atenção.
            - **Atingimento da Meta (%)** — Compara o volume de cada usuário com a
              **meta do período** (diária × dias úteis). A linha de referência marca **100%**.
            - **Volume × Tempo Médio** — Dispersão para identificar perfis:
                - Canto **superior-esquerdo**: alto volume e rápido (estrelas).
                - Canto **inferior-direito**: baixo volume e lento (atenção).
              O tamanho da bolha representa o volume; a cor, o score. Os nomes aparecem sobre cada ponto.
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
              representa o volume de eventos em cada bloco.
              **Destaque visual de gaps:**
                - 🟡 Faixa amarela: gap médio entre 15–30 min.
                - 🔴 Faixa vermelha: gap crítico acima de 30 min.
                - Faixa cinza: almoço detectado (40–60 min, excluído da contagem de ociosidade).
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
        empresa_nome = st.text_input("🏷️ Departamento", placeholder="Ex: Operações — Setor A")
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
        pb5.metric("⏸️ % Tempo Ocioso (média)",    f"{ocio_pct_fb}%",
                   help="Média diária do % do turno sem registro de eventos (almoço excluído)")
        pb6.metric("⚠️ Maior Gap Médio (média)", f"{ocio_gap_fb} min",
                   help="Média do maior gap intra-turno por dia (almoço excluído)")

        st.markdown(
            f'<div style="margin:10px 0 18px 0; padding:12px 18px; border-radius:10px; '
            f'background:{class_bg}; border:1px solid {class_color}; '
            f'color:{class_color}; font-weight:600; font-size:1rem;">'
            f'Classificação: {class_fb} &nbsp;|&nbsp; Ranking: {rank_fb}º de {total_uf}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Detalhamento diário de ociosidade ───────────────────────
        df_ocio_diario = calc_ociosidade_diaria(df_fb, usuario_fb)

        if not df_ocio_diario.empty and "date" in df_fb.columns:
            section("⏸️ Detalhamento Diário de Ociosidade")

            # KPIs do pico
            idx_pico   = df_ocio_diario["pct_ocioso"].idxmax()
            dia_pico   = df_ocio_diario.loc[idx_pico, "data"]
            pct_pico   = df_ocio_diario.loc[idx_pico, "pct_ocioso"]
            gap_pico   = df_ocio_diario.loc[idx_pico, "maior_gap"]
            dias_criticos  = int((df_ocio_diario["pct_ocioso"] > 20).sum())
            dias_atencao   = int(((df_ocio_diario["pct_ocioso"] > 10) & (df_ocio_diario["pct_ocioso"] <= 20)).sum())
            total_ausencias_fb = int(df_ocio_diario["n_ausencias_graves"].sum())

            pk1, pk2, pk3, pk4 = st.columns(4)
            pk1.metric("📅 Dia de Pico",
                       dia_pico.strftime("%d/%m/%Y") if hasattr(dia_pico, "strftime") else str(dia_pico),
                       help="Dia com maior % de ociosidade no período")
            pk2.metric("🔴 % Ocioso no Pico",   f"{pct_pico}%")
            pk3.metric("⚠️ Gap no Pico",        f"{gap_pico} min",
                       help="Maior gap intra-turno no dia de pico")
            pk4.metric("📆 Dias Críticos (>20%)", dias_criticos,
                       help="Dias em que o % de ociosidade ficou acima de 20%")

            if total_ausencias_fb > 0:
                s = "s" if total_ausencias_fb > 1 else ""
                st.warning(
                    f"⚠️ {total_ausencias_fb} ausência{s} grave{s} detectada{s} no período "
                    f"(gap > 60 min fora do horário de almoço)."
                )

            # Gráficos lado a lado
            col_d1, col_d2 = st.columns(2)

            with col_d1:
                st.markdown(
                    f'<div style="font-size:0.85rem;font-weight:600;color:{COLORS["text"]};margin-bottom:4px;">' +
                    "% Ocioso por Dia</div>", unsafe_allow_html=True
                )
                def _cor_pct(v):
                    if v > 20: return COLORS["danger"]
                    if v > 10: return COLORS["warning"]
                    return COLORS["success"]

                _dpct_ymax = max(df_ocio_diario["pct_ocioso"].max() * 1.2, 25)
                fig_dpct = go.Figure(go.Bar(
                    x=df_ocio_diario["data"].dt.strftime("%d/%m"),
                    y=df_ocio_diario["pct_ocioso"],
                    marker_color=[_cor_pct(v) for v in df_ocio_diario["pct_ocioso"]],
                    text=df_ocio_diario["pct_ocioso"].apply(lambda v: f"{v}%"),
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="<b>%{x}</b><br>% Ocioso: %{y}%<extra></extra>",
                ))
                fig_dpct.add_hline(y=10, line_dash="dot", line_color=COLORS["warning"],
                                   annotation_text="Atenção (10%)",
                                   annotation_font_color=COLORS["warning"])
                fig_dpct.add_hline(y=20, line_dash="dash", line_color=COLORS["danger"],
                                   annotation_text="Crítico (20%)",
                                   annotation_font_color=COLORS["danger"])
                fig_dpct.update_layout(xaxis_title="", yaxis_title="% ocioso",
                                       xaxis=dict(tickangle=-35),
                                       yaxis=dict(range=[0, _dpct_ymax]))
                st.plotly_chart(style_fig(fig_dpct, 300), use_container_width=True)

            with col_d2:
                st.markdown(
                    f'<div style="font-size:0.85rem;font-weight:600;color:{COLORS["text"]};margin-bottom:4px;">' +
                    "Maior Gap por Dia (min)</div>", unsafe_allow_html=True
                )
                def _cor_gap(v):
                    if v > 30: return COLORS["danger"]
                    if v > 15: return COLORS["warning"]
                    return COLORS["success"]

                _dgap_ymax = max(df_ocio_diario["maior_gap"].max() * 1.2, 35)
                fig_dgap = go.Figure(go.Bar(
                    x=df_ocio_diario["data"].dt.strftime("%d/%m"),
                    y=df_ocio_diario["maior_gap"],
                    marker_color=[_cor_gap(v) for v in df_ocio_diario["maior_gap"]],
                    text=df_ocio_diario["maior_gap"].apply(lambda v: f"{v:.0f}min"),
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="<b>%{x}</b><br>Gap: %{y} min<extra></extra>",
                ))
                fig_dgap.add_hline(y=15, line_dash="dot", line_color=COLORS["warning"],
                                   annotation_text="Atenção (15 min)",
                                   annotation_font_color=COLORS["warning"])
                fig_dgap.add_hline(y=30, line_dash="dash", line_color=COLORS["danger"],
                                   annotation_text="Crítico (30 min)",
                                   annotation_font_color=COLORS["danger"])
                fig_dgap.update_layout(xaxis_title="", yaxis_title="minutos",
                                       xaxis=dict(tickangle=-35),
                                       yaxis=dict(range=[0, _dgap_ymax]))
                st.plotly_chart(style_fig(fig_dgap, 300), use_container_width=True)

            # Tabela detalhada por dia
            with st.expander("📋 Ver tabela completa por dia"):
                df_tabela = df_ocio_diario.copy()
                df_tabela["Data"]              = df_tabela["data"].dt.strftime("%d/%m/%Y")
                # Horários exatos quando time_key disponível
                fmt_t = "%H:%M:%S" if "time_key" in df_fb.columns else "%H:%M"
                df_tabela["1º Evento"]         = df_tabela["primeiro_evento"].dt.strftime(fmt_t) if "primeiro_evento" in df_tabela.columns else "—"
                df_tabela["Último Evento"]      = df_tabela["ultimo_evento"].dt.strftime(fmt_t) if "ultimo_evento" in df_tabela.columns else "—"
                df_tabela["Duração Turno"]     = df_tabela["turno_min"].apply(
                    lambda v: f"{int(v//60)}h{int(v%60):02d}min" if "turno_min" in df_tabela.columns else "—"
                ) if "turno_min" in df_tabela.columns else "—"
                df_tabela["% Ocioso"]          = df_tabela["pct_ocioso"].apply(lambda v: f"{v}%")
                df_tabela["Maior Gap (min)"]   = df_tabela["maior_gap"].apply(lambda v: f"{v:.0f}")
                df_tabela["Ocioso Total (min)"]= df_tabela["total_ocio_min"].apply(lambda v: f"{v:.0f}")
                df_tabela["Almoço (min)"]      = df_tabela["almoco_min"].apply(
                    lambda v: f"{v:.0f}" if v > 0 else "—"
                )
                df_tabela["Ausências Graves"]  = df_tabela["n_ausencias_graves"].apply(
                    lambda v: f"⚠️ {v}" if v > 0 else "✅ 0"
                )
                df_tabela["Gaps Detectados"]   = df_tabela["gaps_detalhe"]
                st.dataframe(
                    df_tabela[[
                        "Data", "1º Evento", "Último Evento", "Duração Turno",
                        "% Ocioso", "Maior Gap (min)",
                        "Ocioso Total (min)", "Almoço (min)",
                        "Ausências Graves", "Gaps Detectados",
                    ]],
                    use_container_width=True, hide_index=True,
                )
                csv_ocio = df_tabela[[
                    "Data", "1º Evento", "Último Evento", "Duração Turno",
                    "% Ocioso", "Maior Gap (min)",
                    "Ocioso Total (min)", "Almoço (min)",
                    "Ausências Graves", "Gaps Detectados",
                ]].to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Exportar CSV de Ociosidade",
                    csv_ocio,
                    f"ociosidade_{usuario_fb.replace(' ', '_')}.csv",
                    "text/csv",
                )

            # Guarda variáveis para usar no HTML do relatório
            _ocio_diario_html = df_ocio_diario  # referência para o bloco de impressão
        else:
            _ocio_diario_html = None
            dias_criticos = 0
            total_ausencias_fb = 0

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

            # ── Monta HTML da tabela de ociosidade diária ──────────
            if _ocio_diario_html is not None and not _ocio_diario_html.empty:
                def _cls_pct(v):
                    if v > 20: return "td-crit"
                    if v > 10: return "td-warn"
                    return "td-ok"
                def _cls_gap(v):
                    if v > 30: return "td-crit"
                    if v > 15: return "td-warn"
                    return "td-ok"

                _rows_html = ""
                for _, r in _ocio_diario_html.iterrows():
                    _data_str  = r["data"].strftime("%d/%m/%Y") if hasattr(r["data"], "strftime") else str(r["data"])
                    _alm_str   = f"{r['almoco_min']:.0f} min" if r["almoco_min"] > 0 else "—"
                    _aus_str   = f"⚠️ {int(r['n_ausencias_graves'])}" if r["n_ausencias_graves"] > 0 else "✅ 0"
                    _fmt_t = "%H:%M:%S" if "time_key" in df_fb.columns else "%H:%M"
                    _prim = r["primeiro_evento"].strftime(_fmt_t) if "primeiro_evento" in r.index and pd.notna(r["primeiro_evento"]) else "—"
                    _ult  = r["ultimo_evento"].strftime(_fmt_t)   if "ultimo_evento"  in r.index and pd.notna(r["ultimo_evento"])  else "—"
                    _rows_html += (
                        f"<tr>"
                        f"<td>{_data_str}</td>"
                        f"<td style='font-size:10px;'>{_prim}</td>"
                        f"<td style='font-size:10px;'>{_ult}</td>"
                        f'<td class="{_cls_pct(r["pct_ocioso"])}">{r["pct_ocioso"]}%</td>'
                        f'<td class="{_cls_gap(r["maior_gap"])}">{r["maior_gap"]:.0f} min</td>'
                        f"<td>{r['total_ocio_min']:.0f} min</td>"
                        f"<td>{_alm_str}</td>"
                        f"<td>{_aus_str}</td>"
                        f"<td style='text-align:left;font-size:10px;'>{r['gaps_detalhe']}</td>"
                        f"</tr>"
                    )

                _pico_idx  = _ocio_diario_html["pct_ocioso"].idxmax()
                _pico_data = _ocio_diario_html.loc[_pico_idx, "data"]
                _pico_data_str = _pico_data.strftime("%d/%m/%Y") if hasattr(_pico_data, "strftime") else str(_pico_data)
                _pico_pct  = _ocio_diario_html.loc[_pico_idx, "pct_ocioso"]
                _dias_crit = int((_ocio_diario_html["pct_ocioso"] > 20).sum())
                _dias_anal = len(_ocio_diario_html)

                html_ocio_section = f"""
<div class="section-title">⏸️ Detalhamento Diário de Ociosidade</div>
<div class="ocio-summ">
  <div class="ocio-summ-box">
    <div class="os-label">Média % Ocioso</div>
    <div class="os-value" style="color:{ocio_pct_color};">{ocio_pct_fb}%</div>
    <div class="os-sub">{ocio_pct_label}</div>
  </div>
  <div class="ocio-summ-box">
    <div class="os-label">Dia de Pico</div>
    <div class="os-value">{_pico_data_str}</div>
    <div class="os-sub">{_pico_pct}% ocioso nesse dia</div>
  </div>
  <div class="ocio-summ-box">
    <div class="os-label">Dias Críticos (&gt;20%)</div>
    <div class="os-value" style="color:{"#DC2626" if _dias_crit > 0 else "#16A34A"};">{_dias_crit} / {_dias_anal}</div>
    <div class="os-sub">dias analisados</div>
  </div>
</div>
<table class="ocio-table">
  <thead>
    <tr>
      <th>Data</th>
      <th>1º Evento</th>
      <th>Último Evento</th>
      <th>% Ocioso</th>
      <th>Maior Gap</th>
      <th>Total Ocioso</th>
      <th>Almoço</th>
      <th>Ausências</th>
      <th>Gaps detectados (&gt;5 min)</th>
    </tr>
  </thead>
  <tbody>
    {_rows_html}
  </tbody>
</table>"""
            else:
                html_ocio_section = "<p style='color:#94A3B8;font-size:11px;'>Dados diários não disponíveis (sem coluna de data).</p>"

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

  /* ── Tabela de ociosidade diária ── */
  .ocio-table {{ width: 100%; border-collapse: collapse; margin-bottom: 14px; font-size: 11px; }}
  .ocio-table th {{
    background: #EFF6FF; color: #1E40AF; font-weight: 700;
    padding: 6px 8px; text-align: center; border: 1px solid #BFDBFE;
    font-size: 10px; text-transform: uppercase; letter-spacing: .04em;
  }}
  .ocio-table td {{
    padding: 5px 8px; border: 1px solid #E2E8F0; text-align: center; color: #374151;
  }}
  .ocio-table tr:nth-child(even) td {{ background: #F8FAFC; }}
  .ocio-table .td-ok    {{ color: #16A34A; font-weight: 700; }}
  .ocio-table .td-warn  {{ color: #D97706; font-weight: 700; }}
  .ocio-table .td-crit  {{ color: #DC2626; font-weight: 700; }}
  .ocio-summ {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }}
  .ocio-summ-box {{
    border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px;
    text-align: center; background: #FAFAFA;
  }}
  .ocio-summ-box .os-label {{ font-size: 10px; color: #64748B; margin-bottom: 4px; font-weight: 600; }}
  .ocio-summ-box .os-value {{ font-size: 15px; font-weight: 800; color: #1A202C; }}
  .ocio-summ-box .os-sub   {{ font-size: 10px; color: #94A3B8; margin-top: 2px; }}

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
    <div class="kpi-sub">{ocio_pct_label} · média diária · almoço (40–60 min) excluído automaticamente</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">⚠️ Maior Gap Médio</div>
    <div class="kpi-value" style="color:{ocio_gap_color};">{ocio_gap_fb} min</div>
    <div class="kpi-sub">{ocio_gap_label} · maior gap intra-turno por dia</div>
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

<!-- OCIOSIDADE DIÁRIA -->
{html_ocio_section}

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
