"""Streamlit frontend for LIGALOL.

Run with: streamlit run src/frontend/app.py
"""

import pandas as pd
import streamlit as st

from src.api.riot_api import fetch_last_n_matches, fetch_player_matches
from src.challenges.engine import evaluate_daily_challenges, evaluate_weekly_challenges
from src.config_loader import load_config, load_players
from src.data.processor import extract_player_stats
from src.data.storage import get_all_stats, get_daily_stats, get_weekly_stats, save_match_data


def main() -> None:
    """Main entry point for the Streamlit app."""
    st.set_page_config(page_title="LIGALOL", page_icon="🏆", layout="wide")

    st.title("🏆 LIGALOL - Liga Competitiva")

    # Validate API key configuration
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
        """Helper to fetch matches and save stats."""
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

    # Load data
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

    # === TAB 1: Resumen Diario ===
    with tab_resumen:
        st.header("📊 Resumen del Día")

        if df_daily.empty:
            st.info("No hay partidas hoy todavía.")
        else:
            # Aggregate daily stats per player
            daily_agg = (
                df_daily.groupby("game_name")
                .agg(
                    partidas=("match_id", "count"),
                    kills=("kills", "sum"),
                    deaths=("deaths", "sum"),
                    assists=("assists", "sum"),
                    kda=("kda", "mean"),
                    victorias=("win", "sum"),
                )
                .reset_index()
            )
            daily_agg["kda"] = daily_agg["kda"].round(2)
            daily_agg["racha"] = daily_agg["victorias"].astype(str) + "/" + daily_agg["partidas"].astype(str)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Partidas totales hoy", len(df_daily))
            with col2:
                if not daily_agg.empty:
                    mvp = daily_agg.loc[daily_agg["kda"].idxmax()]
                    st.metric("⭐ MVP del Día", mvp["game_name"], f"KDA: {mvp['kda']}")
            with col3:
                if not daily_agg.empty:
                    fedeador = daily_agg.loc[daily_agg["kda"].idxmin()]
                    st.metric("💀 Fedeador del Día", fedeador["game_name"], f"KDA: {fedeador['kda']}")

            st.subheader("Tabla de clasificación diaria")
            display_df = daily_agg[["game_name", "partidas", "racha", "kills", "deaths", "assists", "kda"]]
            display_df = display_df.sort_values("kda", ascending=False).reset_index(drop=True)
            st.dataframe(display_df, use_container_width=True)

    # === TAB 2: Sala de Trofeos ===
    with tab_trofeos:
        st.header("🏅 Sala de Trofeos")

        st.subheader("🌟 Desafíos Diarios")
        if df_daily.empty:
            st.info("No hay datos suficientes para evaluar desafíos diarios.")
        else:
            daily_results = evaluate_daily_challenges(df_daily)
            if daily_results:
                daily_df = pd.DataFrame(daily_results)
                daily_df = daily_df[["challenge_name", "challenge_description", "player", "value"]]
                daily_df.columns = ["Desafío", "Descripción", "Jugador", "Valor"]
                st.dataframe(daily_df, use_container_width=True)
            else:
                st.info("Nadie cumplió los requisitos hoy.")

        st.subheader("🏆 Desafíos Semanales")
        if df_weekly.empty:
            st.info("No hay datos suficientes para evaluar desafíos semanales.")
        else:
            weekly_results = evaluate_weekly_challenges(df_weekly)
            # Show both achieved and not achieved for weekly challenges
            weekly_df = pd.DataFrame(weekly_results)
            if not weekly_df.empty:
                weekly_df = weekly_df[["challenge_name", "player", "value", "achieved"]]
                weekly_df.columns = ["Desafío", "Jugador", "Valor", "Conseguido"]
                # Highlight achieved ones
                st.dataframe(weekly_df, use_container_width=True)
            else:
                st.info("Nadie cumplió los requisitos esta semana.")

    # === TAB 3: Histórico Semanal ===
    with tab_historico:
        st.header("📈 Histórico Semanal")

        if df_weekly.empty:
            st.info("No hay partidas en los últimos 7 días.")
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
            weekly_agg["winrate"] = (weekly_agg["victorias"] / weekly_agg["partidas"] * 100).round(1).astype(str) + "%"

            st.subheader("Tabla acumulada de la semana")
            display_w = weekly_agg[
                ["game_name", "partidas", "victorias", "winrate", "kda_promedio", "daño_total", "oro_total", "vision_total"]
            ]
            display_w.columns = [
                "Jugador", "Partidas", "Victorias", "Winrate", "KDA Prom.", "Daño Total", "Oro Total", "Visión Total"
            ]
            display_w = display_w.sort_values("Victorias", ascending=False).reset_index(drop=True)
            st.dataframe(display_w, use_container_width=True)

            st.subheader("📊 Gráfico de KDA por jugador")
            chart_data = weekly_agg[["game_name", "kda_promedio"]].set_index("game_name")
            st.bar_chart(chart_data)


if __name__ == "__main__":
    main()
