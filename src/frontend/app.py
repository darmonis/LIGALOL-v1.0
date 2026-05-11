"""Streamlit frontend for LIGALOL.

Interfaz visual, divertida y responsive con temática de League of Legends.
Run with: streamlit run src/frontend/app.py
"""

import pandas as pd
import streamlit as st

from src.api.riot_api import fetch_last_n_matches, fetch_player_matches
from src.challenges.engine import evaluate_daily_challenges, evaluate_weekly_challenges
from src.config_loader import load_config, load_players
from src.data.processor import extract_player_stats
from src.data.storage import get_all_stats, get_daily_stats, get_weekly_stats, save_match_data

# ---------------------------------------------------------------------------
# Emojis y textos temáticos
# ---------------------------------------------------------------------------
EMOJI = {
    "damage": "⚔️",
    "gold": "💰",
    "cs": "🌾",
    "vision": "👁️",
    "deaths": "💀",
    "kills": "🗡️",
    "assists": "🤝",
    "win": "🏆",
    "loss": "😵",
    "kda": "📊",
    "mvp": "⭐",
    "feeder": "💀",
    "farm": "🌾",
}

# Subtítulos humorísticos para cada desafío
CHALLENGE_FLAVOR = {
    "MVP del Día": "El carry que nadie pidió pero todos necesitaban",
    "Fedeador del Día": "¿Inteando o simplemente tilted?",
    "La Fuente de Oro": "Generosidad extrema con el equipo enemigo",
    "Rey del Farm": "Tractor en la calle del medio",
    "El Centinela": "Iluminando el mapa como un faro",
    "Fábrica de Daño": "Máquina de destrucción certificada",
    "Adicto a la Sangre": "First blood es un estilo de vida",
}

# Emojis para cada desafío
CHALLENGE_EMOJI = {
    "MVP del Día": "⭐",
    "Fedeador del Día": "💀",
    "La Fuente de Oro": "💀",
    "Rey del Farm": "🌾",
    "El Centinela": "👁️",
    "Fábrica de Daño": "⚔️",
    "Adicto a la Sangre": "🩸",
}

# ---------------------------------------------------------------------------
# CSS personalizado — tema oscuro con acentos dorados (LoL)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* --- Fondo y tipografía general --- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0e17 0%, #111827 50%, #0f172a 100%);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b3a 100%);
}
/* --- Tarjetas de métrica --- */
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.95rem !important;
}
/* --- Barras de progreso con estilo --- */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #c89b3c 0%, #f0c040 100%) !important;
    border-radius: 6px;
}
.stProgress > div > div {
    background: #1e293b !important;
    border-radius: 6px;
}
/* --- Tarjetas de jugador --- */
.player-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.player-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(200, 155, 60, 0.15);
}
/* --- Trofeo card --- */
.trophy-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #c89b3c44;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    margin-bottom: 0.8rem;
}
.trophy-card.achieved {
    border-color: #c89b3c;
    box-shadow: 0 0 15px rgba(200, 155, 60, 0.2);
}
.trophy-card.not-achieved {
    opacity: 0.5;
    border-color: #475569;
}
/* --- Etiquetas de métrica con color --- */
.metric-label {
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.2rem;
}
.metric-value {
    font-size: 1.3rem;
    font-weight: 700;
}
.metric-value.gold { color: #f0c040; }
.metric-value.red { color: #ef4444; }
.metric-value.green { color: #22c55e; }
.metric-value.blue { color: #38bdf8; }
.metric-value.cyan { color: #06b6d4; }
/* --- KDA colores --- */
.kda-great { color: #22c55e; font-weight: 700; }
.kda-ok { color: #facc15; font-weight: 600; }
.kda-bad { color: #ef4444; font-weight: 700; }
/* --- Título con degradado dorado --- */
.lol-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #c89b3c, #f0c040, #c89b3c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.3rem;
}
.lol-subtitle {
    text-align: center;
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}
/* --- Sección de barra lateral --- */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #c89b3c !important;
}
/* --- Tabs estilo --- */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}
/* --- Mensaje vacío gracioso --- */
.empty-msg {
    text-align: center;
    padding: 2rem;
    color: #64748b;
    font-size: 1.1rem;
}
/* --- Responsive: ocultar en móvil columnas estrechas --- */
@media (max-width: 600px) {
    .lol-title { font-size: 1.5rem; }
    .player-card { padding: 0.8rem; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
}
</style>
"""


def _kda_class(kda: float) -> str:
    """Devuelve la clase CSS para el KDA según su valor."""
    if kda >= 3:
        return "kda-great"
    elif kda >= 1:
        return "kda-ok"
    return "kda-bad"


def _kda_emoji(kda: float) -> str:
    """Devuelve un emoji según el KDA."""
    if kda >= 5:
        return "🔥"
    elif kda >= 3:
        return "✨"
    elif kda >= 1:
        return "😐"
    return "😵"


def _format_number(n: float) -> str:
    """Formatea números grandes con separador de miles estilo ES."""
    if n >= 1000:
        return f"{n:,.0f}".replace(",", ".")
    return f"{n:.1f}" if isinstance(n, float) else str(int(n))


def _render_player_card(row: pd.Series, max_damage: float, max_gold: float,
                        max_vision: float, max_cs_per_min: float) -> str:
    """Genera el HTML de una tarjeta de jugador para el Resumen Diario."""
    kda = row["kda"]
    kda_cls = _kda_class(kda)
    kda_emoji = _kda_emoji(kda)

    # Barras de progreso (0-100 relativas al máximo del día)
    dmg_pct = min(row["total_damage"] / max_damage, 1.0) if max_damage > 0 else 0
    gold_pct = min(row["gold_earned"] / max_gold, 1.0) if max_gold > 0 else 0
    vis_pct = min(row["vision_score"] / max_vision, 1.0) if max_vision > 0 else 0
    cs_pct = min(row["cs_per_min"] / max_cs_per_min, 1.0) if max_cs_per_min > 0 else 0

    # Racha de victorias
    wins = int(row["victorias"])
    total = int(row["partidas"])
    winrate = (wins / total * 100) if total > 0 else 0
    winrate_color = "green" if winrate >= 50 else "red"

    return f"""
    <div class="player-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
            <div>
                <span style="font-size:1.4rem; font-weight:700; color:#f8fafc;">{row['game_name']}</span>
                <span style="margin-left:0.5rem; font-size:0.85rem; color:#94a3b8;">
                    {wins}/{total} W &middot;
                    <span style="color:{'#22c55e' if winrate >= 50 else '#ef4444'};">{winrate:.0f}% WR</span>
                </span>
            </div>
            <div>
                <span class="{kda_cls}" style="font-size:1.3rem;">
                    {kda_emoji} {kda:.2f} KDA
                </span>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem 1.5rem; font-size:0.85rem;">
            <div>
                <div class="metric-label">{EMOJI['damage']} Daño</div>
                <div class="metric-value red">{_format_number(row['total_damage'])}</div>
            </div>
            <div>
                <div class="metric-label">{EMOJI['gold']} Oro</div>
                <div class="metric-value gold">{_format_number(row['gold_earned'])}</div>
            </div>
            <div>
                <div class="metric-label">{EMOJI['vision']} Visión</div>
                <div class="metric-value cyan">{_format_number(row['vision_score'])}</div>
            </div>
            <div>
                <div class="metric-label">{EMOJI['cs']} CS/min</div>
                <div class="metric-value blue">{row['cs_per_min']:.1f}</div>
            </div>
        </div>
        <div style="margin-top:0.7rem;">
            <div style="margin-bottom:0.3rem;">
                <span style="font-size:0.75rem; color:#94a3b8;">{EMOJI['damage']} Daño</span>
                <div style="background:#1e293b; border-radius:6px; overflow:hidden; height:8px;">
                    <div style="width:{dmg_pct*100:.0f}%; height:100%; background:linear-gradient(90deg,#ef4444,#f87171); border-radius:6px;"></div>
                </div>
            </div>
            <div style="margin-bottom:0.3rem;">
                <span style="font-size:0.75rem; color:#94a3b8;">{EMOJI['gold']} Oro</span>
                <div style="background:#1e293b; border-radius:6px; overflow:hidden; height:8px;">
                    <div style="width:{gold_pct*100:.0f}%; height:100%; background:linear-gradient(90deg,#c89b3c,#f0c040); border-radius:6px;"></div>
                </div>
            </div>
            <div style="margin-bottom:0.3rem;">
                <span style="font-size:0.75rem; color:#94a3b8;">{EMOJI['vision']} Visión</span>
                <div style="background:#1e293b; border-radius:6px; overflow:hidden; height:8px;">
                    <div style="width:{vis_pct*100:.0f}%; height:100%; background:linear-gradient(90deg,#06b6d4,#38bdf8); border-radius:6px;"></div>
                </div>
            </div>
            <div>
                <span style="font-size:0.75rem; color:#94a3b8;">{EMOJI['cs']} Farm</span>
                <div style="background:#1e293b; border-radius:6px; overflow:hidden; height:8px;">
                    <div style="width:{cs_pct*100:.0f}%; height:100%; background:linear-gradient(90deg,#22c55e,#4ade80); border-radius:6px;"></div>
                </div>
            </div>
        </div>
        <div style="margin-top:0.5rem; display:flex; gap:1rem; font-size:0.85rem; color:#94a3b8;">
            <span>{EMOJI['kills']} {int(row['kills'])} kills</span>
            <span>{EMOJI['deaths']} {int(row['deaths'])} deaths</span>
            <span>{EMOJI['assists']} {int(row['assists'])} assists</span>
        </div>
    </div>
    """


def _render_trophy_card(name: str, player: str, value, achieved: bool = True) -> str:
    """Genera el HTML de una tarjeta de trofeo/desafío."""
    emoji = CHALLENGE_EMOJI.get(name, "🏅")
    flavor = CHALLENGE_FLAVOR.get(name, "")
    achieved_cls = "achieved" if achieved else "not-achieved"
    status_icon = "✅" if achieved else "❌"
    value_str = str(value)

    return f"""
    <div class="trophy-card {achieved_cls}">
        <div style="font-size:2.5rem; margin-bottom:0.3rem;">{emoji}</div>
        <div style="font-size:1.1rem; font-weight:700; color:#f8fafc;">{name}</div>
        <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:0.4rem;">{flavor}</div>
        <div style="font-size:1.3rem; font-weight:700; color:#c89b3c;">{player}</div>
        <div style="font-size:0.9rem; color:#94a3b8;">{value_str} {status_icon}</div>
    </div>
    """


def _render_weekly_bar(label: str, emoji: str, values: dict, max_val: float, color: str) -> str:
    """Genera HTML para una barra comparativa semanal por jugador."""
    rows = ""
    for player, val in values.items():
        pct = min(val / max_val, 1.0) if max_val > 0 else 0
        rows += f"""
        <div style="margin-bottom:0.5rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.15rem;">
                <span style="color:#f8fafc; font-weight:600;">{player}</span>
                <span style="color:{color};">{_format_number(val)}</span>
            </div>
            <div style="background:#1e293b; border-radius:6px; overflow:hidden; height:10px;">
                <div style="width:{pct*100:.0f}%; height:100%; background:{color}; border-radius:6px; transition:width 0.3s ease;"></div>
            </div>
        </div>
        """
    return f"""
    <div style="margin-bottom:1.5rem;">
        <div style="font-size:1rem; font-weight:700; color:#f8fafc; margin-bottom:0.5rem;">
            {emoji} {label}
        </div>
        {rows}
    </div>
    """


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------
def main() -> None:
    """Punto de entrada principal de la app Streamlit."""
    st.set_page_config(page_title="LIGALOL", page_icon="🏆", layout="wide")

    # Inyectar CSS personalizado
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Título principal con estilo dorado
    st.markdown('<div class="lol-title">🏆 LIGALOL</div>', unsafe_allow_html=True)
    st.markdown('<div class="lol-subtitle">Liga Competitiva — Donde el tilt se vuelve estadística</div>',
                unsafe_allow_html=True)

    # Validar API key
    config = load_config()
    if not config.get("api_key") or config["api_key"] in ("your_api_key_here", ""):
        st.error("🔑 **API Key no configurada.**")
        st.info(
            "Para ejecutar localmente, crea un archivo `config/.env` basado en `config/.env.example`.\n\n"
            "Para Streamlit Cloud, configura los secrets en el dashboard."
        )
        st.stop()

    # --- Sidebar ---
    st.sidebar.header("⚙️ Configuración")

    def _fetch_and_save(fetch_func, label: str) -> None:
        """Helper para obtener partidas y guardar estadísticas."""
        players = load_players()
        all_stats = []
        progress_bar = st.sidebar.progress(0)
        for i, player in enumerate(players):
            st.sidebar.write(f"Consultando {player['game_name']}...")
            matches = fetch_func(player)
            for match in matches:
                stats = extract_player_stats(
                    match,
                    match.get("_query_puuid"),
                    player["game_name"],
                    player["tag_line"],
                )
                if stats:
                    all_stats.append(stats)
            progress_bar.progress((i + 1) / len(players))

        if all_stats:
            save_match_data(all_stats)
            st.sidebar.success(f"¡{len(all_stats)} partidas guardadas!")
        else:
            st.sidebar.warning("No se encontraron partidas nuevas.")

    if st.sidebar.button("🔄 Actualizar datos (últimas 24h)"):
        _fetch_and_save(lambda p: fetch_player_matches(p, hours=24), "24h")

    if st.sidebar.button("📥 Cargar histórico inicial (10 partidas)"):
        _fetch_and_save(lambda p: fetch_last_n_matches(p, n=10), "histórico")

    with st.sidebar.expander("🔍 Diagnóstico"):
        if st.button("Probar API y primer jugador"):
            from src.api.riot_api import diagnose_player
            players = load_players()
            if players:
                p = players[0]
                diag = diagnose_player(p["game_name"], p["tag_line"])
                st.json(diag)
            else:
                st.warning("No hay jugadores configurados.")

    # Cargar datos
    df_all = get_all_stats()
    df_daily = get_daily_stats()
    df_weekly = get_weekly_stats()

    if df_all.empty:
        st.info("No hay datos todavía. Pulsa '📥 Cargar histórico inicial (10 partidas)' en el panel lateral para empezar.")
        st.stop()

    # --- Tabs ---
    tab_resumen, tab_trofeos, tab_historico = st.tabs(
        ["📊 Resumen Diario", "🏅 Sala de Trofeos", "📈 Histórico Semanal"]
    )

    # ===================================================================
    # TAB 1: Resumen Diario
    # ===================================================================
    with tab_resumen:
        st.markdown("### 📊 Resumen del Día")

        if df_daily.empty:
            st.markdown(
                '<div class="empty-msg">😴 Ninguna partida hoy... ¿Están en promo o qué?</div>',
                unsafe_allow_html=True,
            )
        else:
            # Agregar estadísticas diarias por jugador
            daily_agg = (
                df_daily.groupby("game_name")
                .agg(
                    partidas=("match_id", "count"),
                    kills=("kills", "sum"),
                    deaths=("deaths", "sum"),
                    assists=("assists", "sum"),
                    kda=("kda", "mean"),
                    victorias=("win", "sum"),
                    total_damage=("total_damage", "sum"),
                    gold_earned=("gold_earned", "sum"),
                    vision_score=("vision_score", "sum"),
                    cs_per_min=("cs_per_min", "mean"),
                )
                .reset_index()
            )
            daily_agg["kda"] = daily_agg["kda"].round(2)

            # --- Métricas superiores ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="🎮 Partidas hoy",
                    value=str(len(df_daily)),
                )
            with col2:
                if not daily_agg.empty:
                    mvp = daily_agg.loc[daily_agg["kda"].idxmax()]
                    st.metric(
                        label="⭐ MVP del Día",
                        value=mvp["game_name"],
                        delta=f"KDA: {mvp['kda']:.2f}",
                    )
                    st.caption("_El carry que nadie pidió pero todos necesitaban_")
            with col3:
                if not daily_agg.empty:
                    fedeador = daily_agg.loc[daily_agg["kda"].idxmin()]
                    st.metric(
                        label="💀 Fedeador del Día",
                        value=fedeador["game_name"],
                        delta=f"KDA: {fedeador['kda']:.2f}",
                        delta_color="inverse",
                    )
                    st.caption("_¿Inteando o simplemente tilted?_")

            st.markdown("---")

            # --- Tarjetas de jugador ---
            st.markdown("### 🎮 Jugadores del Día")

            # Calcular máximos para las barras de progreso relativas
            max_damage = daily_agg["total_damage"].max()
            max_gold = daily_agg["gold_earned"].max()
            max_vision = daily_agg["vision_score"].max()
            max_cs = daily_agg["cs_per_min"].max()

            # Ordenar por KDA descendente
            daily_agg_sorted = daily_agg.sort_values("kda", ascending=False).reset_index(drop=True)

            for _, row in daily_agg_sorted.iterrows():
                card_html = _render_player_card(row, max_damage, max_gold, max_vision, max_cs)
                st.markdown(card_html, unsafe_allow_html=True)

            # --- Tabla detallada colapsable ---
            with st.expander("📋 Ver tabla detallada"):
                display_df = daily_agg_sorted[[
                    "game_name", "partidas", "kills", "deaths", "assists",
                    "kda", "total_damage", "gold_earned", "vision_score", "cs_per_min",
                ]].copy()
                display_df.columns = [
                    "Jugador", "Partidas", "Kills", "Deaths", "Assists",
                    "KDA", "Daño", "Oro", "Visión", "CS/min",
                ]
                st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ===================================================================
    # TAB 2: Sala de Trofeos
    # ===================================================================
    with tab_trofeos:
        st.markdown("### 🏅 Sala de Trofeos")

        # --- Desafíos Diarios ---
        st.markdown("#### 🌟 Desafíos Diarios")

        if df_daily.empty:
            st.markdown(
                '<div class="empty-msg">😴 Sin partidas hoy... Los trofeos no se ganan solos</div>',
                unsafe_allow_html=True,
            )
        else:
            daily_results = evaluate_daily_challenges(df_daily)
            if daily_results:
                # Mostrar como tarjetas de trofeo en columnas de 2
                for i in range(0, len(daily_results), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(daily_results):
                            r = daily_results[i + j]
                            with cols[j]:
                                st.markdown(
                                    _render_trophy_card(
                                        name=r["challenge_name"],
                                        player=r["player"],
                                        value=r["value"],
                                        achieved=r.get("achieved", True),
                                    ),
                                    unsafe_allow_html=True,
                                )
            else:
                st.markdown(
                    '<div class="empty-msg">🤷 Nadie cumplió los requisitos hoy... ¿Están jugando o qué?</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # --- Desafíos Semanales ---
        st.markdown("#### 🏆 Desafíos Semanales")

        if df_weekly.empty:
            st.markdown(
                '<div class="empty-msg">📅 Sin datos esta semana... ¡a jugar se ha dicho!</div>',
                unsafe_allow_html=True,
            )
        else:
            weekly_results = evaluate_weekly_challenges(df_weekly)
            if weekly_results:
                weekly_df = pd.DataFrame(weekly_results)
                # Mostrar como tarjetas de trofeo
                for i in range(0, len(weekly_results), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(weekly_results):
                            r = weekly_results[i + j]
                            with cols[j]:
                                st.markdown(
                                    _render_trophy_card(
                                        name=r["challenge_name"],
                                        player=r["player"],
                                        value=r["value"],
                                        achieved=r.get("achieved", False),
                                    ),
                                    unsafe_allow_html=True,
                                )
            else:
                st.markdown(
                    '<div class="empty-msg">🤷 Nadie cumplió los requisitos esta semana...</div>',
                    unsafe_allow_html=True,
                )

    # ===================================================================
    # TAB 3: Histórico Semanal
    # ===================================================================
    with tab_historico:
        st.markdown("### 📈 Histórico Semanal")

        if df_weekly.empty:
            st.markdown(
                '<div class="empty-msg">📅 Sin partidas en los últimos 7 días... ¿Están en hiatus?</div>',
                unsafe_allow_html=True,
            )
        else:
            weekly_agg = (
                df_weekly.groupby("game_name")
                .agg(
                    partidas=("match_id", "count"),
                    kills=("kills", "sum"),
                    deaths=("deaths", "sum"),
                    assists=("assists", "sum"),
                    kda_promedio=("kda", "mean"),
                    daño_total=("total_damage", "sum"),
                    oro_total=("gold_earned", "sum"),
                    vision_total=("vision_score", "sum"),
                    victorias=("win", "sum"),
                )
                .reset_index()
            )
            weekly_agg["kda_promedio"] = weekly_agg["kda_promedio"].round(2)
            weekly_agg["winrate"] = (weekly_agg["victorias"] / weekly_agg["partidas"] * 100).round(1)

            # --- Métricas semanales superiores ---
            col1, col2, col3 = st.columns(3)
            with col1:
                total_games = int(weekly_agg["partidas"].sum())
                st.metric(label="🎮 Partidas esta semana", value=str(total_games))
            with col2:
                top_kda = weekly_agg.loc[weekly_agg["kda_promedio"].idxmax()]
                st.metric(
                    label="⭐ Mejor KDA semanal",
                    value=top_kda["game_name"],
                    delta=f"KDA: {top_kda['kda_promedio']:.2f}",
                )
            with col3:
                top_wr = weekly_agg.loc[weekly_agg["winrate"].idxmax()]
                st.metric(
                    label="🏆 Mejor Winrate",
                    value=top_wr["game_name"],
                    delta=f"{top_wr['winrate']:.0f}%",
                )

            st.markdown("---")

            # --- Tabla acumulada mejorada ---
            st.markdown("#### 📋 Tabla acumulada de la semana")
            display_w = weekly_agg[[
                "game_name", "partidas", "victorias", "winrate",
                "kda_promedio", "daño_total", "oro_total", "vision_total",
            ]].copy()
            display_w.columns = [
                "Jugador", "Partidas", "Victorias", "Winrate",
                "KDA Prom.", "Daño Total", "Oro Total", "Visión Total",
            ]
            display_w = display_w.sort_values("Winrate", ascending=False).reset_index(drop=True)

            # Aplicar formato condicional con HTML
            st.dataframe(display_w, use_container_width=True, hide_index=True)

            st.markdown("---")

            # --- Gráfico de KDA ---
            st.markdown("#### 📊 KDA Promedio por Jugador")
            chart_data = weekly_agg[["game_name", "kda_promedio"]].set_index("game_name")
            st.bar_chart(chart_data)

            st.markdown("---")

            # --- Comparativas visuales con barras ---
            st.markdown("#### ⚔️ Comparativas Semanales")

            # Daño total
            damage_vals = dict(zip(weekly_agg["game_name"], weekly_agg["daño_total"]))
            max_dmg = max(damage_vals.values()) if damage_vals else 1
            st.markdown(
                _render_weekly_bar("Daño Total", EMOJI["damage"], damage_vals, max_dmg, "#ef4444"),
                unsafe_allow_html=True,
            )

            # Oro total
            gold_vals = dict(zip(weekly_agg["game_name"], weekly_agg["oro_total"]))
            max_gld = max(gold_vals.values()) if gold_vals else 1
            st.markdown(
                _render_weekly_bar("Oro Total", EMOJI["gold"], gold_vals, max_gld, "#f0c040"),
                unsafe_allow_html=True,
            )

            # Visión total
            vision_vals = dict(zip(weekly_agg["game_name"], weekly_agg["vision_total"]))
            max_vis = max(vision_vals.values()) if vision_vals else 1
            st.markdown(
                _render_weekly_bar("Visión Total", EMOJI["vision"], vision_vals, max_vis, "#06b6d4"),
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()