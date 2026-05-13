"""
Minder AI: Streamlit Demo Application
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from config import APP_TITLE, APP_ICON
from ui import (
    initialize_session_state,
    render_sidebar,
    render_factory_floor_display, # Renamed import
    handle_factory_input,         # Added import
    render_agents_brain,
)

def main():
    """Main Streamlit app entry point"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title(APP_TITLE)
    st.markdown(
        "A voice-first co-worker agent designed to safely acquire, verify, and document unwritten tribal knowledge."
    )

    # Initialize session state
    initialize_session_state()

    # Render sidebar configuration
    render_sidebar()

    # --- UI Layout ---
    
    # Create the two-column display for history and debug info
    col_factory, col_brain = st.columns([1, 1])

    with col_factory:
        # Show the chat history here
        render_factory_floor_display()

    with col_brain:
        # Show the brain/internal state here
        render_agents_brain()

    # --- Input Handling ---
    
    # IMPORTANT: chat_input MUST be at the top level, 
    # not inside columns or expanders.
    handle_factory_input()

if __name__ == "__main__":
    main()