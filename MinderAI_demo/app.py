"""
Minder AI: Streamlit Demo Application
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from config import APP_TITLE, APP_ICON
from ui import (
    initialize_session_state,
    render_sidebar,
    render_factory_floor_display,
    handle_factory_input,
    render_agents_brain,
)


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session_state()
    render_sidebar()

    # ── Header bar with Brain toggle ──────────────────────────────────────────
    col_title, col_toggle = st.columns([5, 1])
    with col_title:
        st.title(APP_TITLE)
        st.markdown(
            "A voice-first co-worker agent designed to safely acquire, verify, "
            "and document unwritten tribal knowledge."
        )
    with col_toggle:
        st.write("")
        brain_label = "🧠 Hide Brain" if st.session_state.show_brain else "🧠 Agent Brain"
        if st.button(brain_label, use_container_width=True):
            st.session_state.show_brain = not st.session_state.show_brain
            st.rerun()

    # ── Main layout ───────────────────────────────────────────────────────────
    if st.session_state.show_brain:
        st.markdown("""
        <style>
        [data-testid="stHorizontalBlock"] {
            align-items: flex-start;
        }
        [data-testid="stHorizontalBlock"] > div:nth-child(2) {
            position: sticky;
            top: 3.5rem;
            max-height: calc(100vh - 5rem);
            overflow-y: auto;
            border-left: 2px solid #e2e8f0;
            border-radius: 0 8px 8px 0;
            background: #f8fafc;
            box-shadow: -4px 0 16px rgba(0,0,0,0.06);
            padding: 0 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

        col_factory, col_brain = st.columns([3, 2])
        with col_factory:
            render_factory_floor_display()
        with col_brain:
            render_agents_brain()
    else:
        render_factory_floor_display()

    # chat_input must be at the top level, not inside columns
    handle_factory_input()


if __name__ == "__main__":
    main()
