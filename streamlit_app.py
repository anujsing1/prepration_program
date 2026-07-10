#!/usr/bin/env python3
"""Streamlit Workflow Studio — n8n-style LangGraph editor."""

from __future__ import annotations

import streamlit as st

from morning_trading_agent.presentation.streamlit.run_explorer import render_run_explorer
from morning_trading_agent.presentation.streamlit.workflow_editor import render_workflow_editor

st.set_page_config(
    page_title="Morning Trading Agent — Workflow Studio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; }
    div[data-testid="stSidebar"] { background: #0f172a; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Workflow Studio")
    st.caption("LangGraph + LangChain pipeline")
    page = st.radio(
        "Navigation",
        ["Workflow Editor", "Run Explorer", "Architecture"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown(
        """
        **LangChain** — LLM nodes (purple)  
        **Python** — ranking, technical (green)  
        **Gates** — filters (red)
        """
    )

if page == "Workflow Editor":
    render_workflow_editor()
elif page == "Run Explorer":
    render_run_explorer()
else:
    st.subheader("Architecture")
    st.markdown(
        """
        ### LangGraph (orchestration)
        - **6 workflows**, **20 nodes**, linear DAG
        - Built with `StateGraph(TradingState)` in `graph/trading_graph.py`
        - Optional PostgreSQL checkpointing

        ### LangChain (LLM only)
        | Node | Provider |
        |------|----------|
        | `extract_stocks` | Gemini / Ollama structured JSON |
        | `analyze_news` | Gemini / Ollama structured JSON |
        | `generate_watchlist` | Gemini / Ollama markdown report |

        ### Deterministic Python (not LLM)
        Ranking, technical analysis, watchlist gates, tradability policy.

        ### Config
        Edits in **Workflow Editor** are saved to `config/workflow_graph.yaml`
        and picked up on the next pipeline run.
        """
    )
