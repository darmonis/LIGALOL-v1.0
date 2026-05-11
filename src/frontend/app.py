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
# Funciones para el Duelo
# ---------------------------------------------------------------------------

ROAST_PHRASES = {
    "kda": {
        "win": [
            "Lleva el KDA en modo Dios.",
            "Está en su promo a Challenger, seguro.",
            "Hoy no pagó internet al enemigo.",
        ],
        "lose": [
            "El KDA parece un número de teléfono... y no es el suyo.",
            "Farmeando asistencias desde la tumba.",
            "¿Inteando o simplemente tilted? Probablemente ambos.",
        ],
    },
    "damage": {
        "win": [
            "Máquina de destrucción certificada.",
            "El enemigo pidió el /surrender solo por él.",
            "DPS nivel boss final.",
        ],
        "lose": [
            "Hace menos daño que un minion de cañón.",
            "El soporte le está flameando en 3 idiomas.",
            "¿Seguro que no era partida de TFT?",
        ],
    },
    "gold": {
        "win": [
            "Forbes le acaba de llamar.",
            "Monopolizando el oro como un dragón anciano.",
            "Paga las wards con billetes de 500.",
        ],
        "lose": [
            "Vive con 300 de oro desde minuto 10.",
            "Su economía está en recesión.",
            "Incluso el jungla enemigo tiene más oro.",
        ],
    },
    "vision": {
        "win": [
            "Ilumina el mapa más que el Sol de Summoner's Rift.",
            "Tiene más wards que una tienda de camping.",
            "El enemigo no puede ni mirarle sin ser visto.",
        ],
        "lose": [
            "Jugando con el mapa en negro como en Dark Souls.",
            "¿Visión? Eso suena a magia oscura.",
            "El jungla enemigo le visita más que su familia.",
        ],
    },
    "deaths": {
        "win": [
            "Tan difícil de matar como una torreta de inhibidor.",
            "El enemigo se cansó de intentarlo.",
            "¿Inmortal? No, simplemente no se tira.",
        ],
        "lose": [
            "Ha visto más grises que una partida de Ajedrez.",
            "El enemigo le tiene de cliente frecuente.",
            "Su KDA tiene más letras que un diccionario.",
        ],
    },
    "winrate": {
        "win": [
            "Winrate de tryhard. Respeto.",
            "Gana más que el casino.",
            "El equipo enemigo le teme.",
        ],
        "lose": [
            "Su winrate es un speedrun de cómo perder LP.",
            "Incluso el equipo de desarrollo gana más.",
            "Definiendo 'elo hell' desde la temporada 3.",
        ],
    },
}


def _pick_roast(metric: str, winner: bool) -> str:
    import random
    key = "win" if winner else "lose"
    phrases = ROAST_PHRASES.get(metric, {}).get(key, [""])
    return random.choice(phrases)


def _render_duelo_bar(label: str, emoji: str, val_a: float, val_b: float,
                      name_a: str, name_b: str, metric: str) -> str:
    """Barra comparativa horizontal para el duelo entre 2 jugadores."""
    total = val_a + val_b
    if total == 0:
        pct_a = pct_b = 50
    else:
        pct_a = (val_a / total) * 100
        pct_b = (val_b / total) * 100

    roast_a = _pick_roast(metric, val_a >= val_b)
    roast_b = _pick_roast(metric, val_b >= val_a)

    return f"""
    <div style="margin-bottom:1.2rem; background:#1e293b; border-radius:12px; padding:1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <span style="font-weight:700; color:#f8fafc; font-size:1rem;">{name_a}</span>
            <span style="font-size:0.9rem; color:#94a3b8;">{emoji} {label}</span>
            <span style="font-weight:700; color:#f8fafc; font-size:1rem;">{name_b}</span>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
            <div style="flex:{pct_a:.1f}; background:linear-gradient(90deg,#3b82f6,#60a5fa); height:24px; border-radius:6px; display:flex; align-items:center; justify-content:flex-start; padding-left:0.5rem; font-size:0.85rem; color:#fff; font-weight:700; min-width:40px;">
                {_format_number(val_a)}
            </div>
            <div style="flex:{pct_b:.1f}; background:linear-gradient(90deg,#ef4444,#f87171); height:24px; border-radius:6px; display:flex; align-items:center; justify-content:flex-end; padding-right:0.5rem; font-size:0.85rem; color:#fff; font-weight:700; min-width:40px;">
                {_format_number(val_b)}
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#94a3b8; font-style:italic;">
            <span>{roast_a}</span>
            <span>{roast_b}</span>
        </div>
    </div>
    """


def _duelo_veredicto(name_a: str, name_b: str, score_a: int, score_b: int) -> str:
    diff = abs(score_a - score_b)
    if score_a > score_b:
        winner, loser, winner_score = name_a, name_b, score_a
        color = "#3b82f6"
    elif score_b > score_a:
        winner, loser, winner_score = name_b, name_a, score_b
        color = "#ef4444"
    else:
        return f"""
        <div style="text-align:center; padding:1.5rem; background:#1e293b; border-radius:12px; margin-top:1rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🤝</div>
            <div style="font-size:1.3rem; font-weight:700; color:#f8fafc;">¡Empate técnico!</div>
            <div style="font-size:0.95rem; color:#94a3b8;">Nadie gana, ambos pierden LP. Classic.</div>
        </div>
        """

    if diff >= 5:
        phrase = f"{winner} le ha dado una paliza de {winner_score}-{abs(score_a-score_b)}. {loser} debería considerar jugar Aram."
        icon = "🏆"
    elif diff >= 3:
        phrase = f"{winner} gana con claridad. {loser} estaba cerca, pero 'cerca' solo sirve en herraduras y granadas."
        icon = "⚡"
    else:
        phrase = f"Victoria ajustada para {winner}. {loser} puede pedir la revancha... o simplemente blamear al jungla."
        icon = "🥊"

    return f"""
    <div style="text-align:center; padding:1.5rem; background:{color}22; border:2px solid {color}; border-radius:12px; margin-top:1rem;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">{icon}</div>
        <div style="font-size:1.3rem; font-weight:700; color:{color};">{winner} GANA</div>
        <div style="font-size:0.95rem; color:#94a3b8; margin-top:0.3rem;">{phrase}</div>
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
    tab_resumen, tab_trofeos, tab_historico, tab_duelo = st.tabs(
        ["📊 Resumen Diario", "🏅 Sala de Trofeos", "📈 Histórico Semanal", "⚔️ Duelo"]
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


    # ===================================================================
    # TAB 4: Duelo
    # ===================================================================
    with tab_duelo:
        st.markdown("### ⚔️ Duelo de Leyendas")
        st.markdown(
            '<div style="color:#94a3b8; margin-bottom:1rem;">Elige dos jugadores y deja que los datos hablen. Que empiece la polémica.</div>',
            unsafe_allow_html=True,
        )

        players_list = sorted(df_all["game_name"].unique().tolist())
        if len(players_list) < 2:
            st.markdown(
                '<div class="empty-msg">👤 Necesitas al menos 2 jugadores con datos para un duelo. ¡A jugar!</div>',
                unsafe_allow_html=True,
            )
        else:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                p_a = st.selectbox("Jugador A", players_list, index=0, key="duelo_a")
            with col_sel2:
                default_b = 1 if len(players_list) > 1 else 0
                p_b = st.selectbox("Jugador B", players_list, index=default_b, key="duelo_b")

            if p_a == p_b:
                st.warning("No puedes comparar a un jugador consigo mismo... a menos que quieras ver cuánto ha empeorado.")
            else:
                # Usar datos históricos totales para el duelo
                df_duelo = df_all.groupby("game_name").agg(
                    partidas=("match_id", "count"),
                    kills=("kills", "sum"),
                    deaths=("deaths", "sum"),
                    assists=("assists", "sum"),
                    kda=("kda", "mean"),
                    total_damage=("total_damage", "sum"),
                    gold_earned=("gold_earned", "sum"),
                    vision_score=("vision_score", "sum"),
                    victorias=("win", "sum"),
                ).reset_index()

                row_a = df_duelo[df_duelo["game_name"] == p_a].iloc[0]
                row_b = df_duelo[df_duelo["game_name"] == p_b].iloc[0]

                winrate_a = (row_a["victorias"] / row_a["partidas"] * 100) if row_a["partidas"] > 0 else 0
                winrate_b = (row_b["victorias"] / row_b["partidas"] * 100) if row_b["partidas"] > 0 else 0

                # Puntuación por métrica (quién gana cada una)
                score_a = 0
                score_b = 0

                metrics = [
                    ("KDA", EMOJI["kda"], row_a["kda"], row_b["kda"], "kda"),
                    ("Daño Total", EMOJI["damage"], row_a["total_damage"], row_b["total_damage"], "damage"),
                    ("Oro Total", EMOJI["gold"], row_a["gold_earned"], row_b["gold_earned"], "gold"),
                    ("Visión Total", EMOJI["vision"], row_a["vision_score"], row_b["vision_score"], "vision"),
                    ("Muertes (menos es mejor)", EMOJI["deaths"], -row_a["deaths"], -row_b["deaths"], "deaths"),
                    ("Winrate", EMOJI["win"], winrate_a, winrate_b, "winrate"),
                ]

                for label, emoji, val_a, val_b, metric_key in metrics:
                    if metric_key == "deaths":
                        # Para muertes, invertimos la lógica visual (menos es mejor)
                        st.markdown(
                            _render_duelo_bar(label, emoji, row_a["deaths"], row_b["deaths"], p_a, p_b, metric_key),
                            unsafe_allow_html=True,
                        )
                        if row_a["deaths"] < row_b["deaths"]:
                            score_a += 1
                        elif row_b["deaths"] < row_a["deaths"]:
                            score_b += 1
                    else:
                        st.markdown(
                            _render_duelo_bar(label, emoji, val_a, val_b, p_a, p_b, metric_key),
                            unsafe_allow_html=True,
                        )
                        if val_a > val_b:
                            score_a += 1
                        elif val_b > val_a:
                            score_b += 1

                # Veredicto final
                st.markdown(
                    _duelo_veredicto(p_a, p_b, score_a, score_b),
                    unsafe_allow_html=True,
                )

                # Estadísticas cruzadas graciosas
                st.markdown("---")
                st.markdown("#### 🔥 Estadísticas Cruzadas")

                # Calcular ratios humorísticos
                if row_a["deaths"] > 0 and row_b["deaths"] > 0:
                    death_ratio = row_b["deaths"] / row_a["deaths"]
                    st.markdown(
                        f"<div style='color:#f8fafc; font-size:0.95rem; margin-bottom:0.5rem;'>"
                        f"💀 Por cada muerte de <b>{p_a}</b>, <b>{p_b}</b> muere <b>{death_ratio:.1f}x</b> veces."
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                if row_a["kills"] > 0 and row_b["kills"] > 0:
                    kill_ratio = row_b["kills"] / row_a["kills"]
                    st.markdown(
                        f"<div style='color:#f8fafc; font-size:0.95rem; margin-bottom:0.5rem;'>"
                        f"🗡️ Por cada kill de <b>{p_a}</b>, <b>{p_b}</b> consigue <b>{kill_ratio:.1f}x</b>."
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                if row_a["gold_earned"] > 0:
                    gold_per_death_a = row_a["gold_earned"] / max(row_a["deaths"], 1)
                    gold_per_death_b = row_b["gold_earned"] / max(row_b["deaths"], 1)
                    richer = p_a if gold_per_death_a > gold_per_death_b else p_b
                    st.markdown(
                        f"<div style='color:#f8fafc; font-size:0.95rem; margin-bottom:0.5rem;'>"
                        f"💰 <b>{richer}</b> es más eficiente: genera más oro por cada vez que muere."
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # Partidas jugadas
                st.markdown(
                    f"<div style='color:#94a3b8; font-size:0.85rem; margin-top:0.5rem; font-style:italic;'>"
                    f"📊 Datos basados en {row_a['partidas']} partidas de {p_a} y {row_b['partidas']} de {p_b}."
                    f"</div>",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()