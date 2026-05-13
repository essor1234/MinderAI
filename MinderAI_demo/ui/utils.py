"""UI Utilities and Session State Management"""

import streamlit as st


def initialize_session_state():
    """Initialize session state variables"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pipeline_name" not in st.session_state:
        st.session_state.pipeline_name = "Default Pipeline"
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = None
    if "selected_memories" not in st.session_state:
        st.session_state.selected_memories = []
    if "reflections" not in st.session_state:
        st.session_state.reflections = []
    if "plan" not in st.session_state:
        st.session_state.plan = None
    if "background_task_running" not in st.session_state:
        st.session_state.background_task_running = False
    if "pending_async_phases" not in st.session_state:
        st.session_state.pending_async_phases = False
    if "pending_sync_result" not in st.session_state:
        st.session_state.pending_sync_result = {}
    if "conversation_count" not in st.session_state:
        st.session_state.conversation_count = 0
    if "reflection_interval" not in st.session_state:
        st.session_state.reflection_interval = 5
    if "last_processed_input" not in st.session_state:
        st.session_state.last_processed_input = None
    if "pending_pipeline_run" not in st.session_state:
        st.session_state.pending_pipeline_run = False
    if "pending_worker_input" not in st.session_state:
        st.session_state.pending_worker_input = None
    if "active_memory_file" not in st.session_state:
        st.session_state.active_memory_file = None
    if "show_brain" not in st.session_state:
        st.session_state.show_brain = False
    if "pending_initial_reflection" not in st.session_state:
        st.session_state.pending_initial_reflection = False
    if "execution_mode" not in st.session_state:
        st.session_state.execution_mode = "plan_first"
