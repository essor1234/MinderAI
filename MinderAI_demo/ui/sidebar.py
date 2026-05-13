"""Sidebar Configuration for Minder AI"""

import streamlit as st

from pipeline import DefaultPipeline
from config import (
    DATA_DIR,
    DEFAULT_MEMORY_FILE,
    DEFAULT_REFLECTION_INTERVAL,
    AVAILABLE_DATASETS,
)

_CUSTOM_LABEL = "Custom File Path..."


def get_available_pipelines() -> dict:
    return {
        "Default Pipeline": DefaultPipeline,
    }


def _reinit_pipeline(memory_file: str, pipeline_class, score_model: str,
                     chat_model: str, embedding_model: str,
                     reflection_model: str = "qwen-plus",
                     plan_model: str = "qwen-plus"):
    """Create a new pipeline instance and reset memory-related state."""
    try:
        st.session_state.pipeline = pipeline_class(
            memory_file=memory_file,
            score_model=score_model,
            chat_model=chat_model,
            embedding_model=embedding_model,
            reflection_model=reflection_model,
            plan_model=plan_model,
        )
        st.session_state.active_memory_file = memory_file
        # Restore persisted reflections; reset everything else
        pipeline = st.session_state.pipeline
        st.session_state.selected_memories = []
        st.session_state.reflections = pipeline.get_stored_reflections()
        st.session_state.plan = None
        st.session_state.conversation_count = 0
        return True
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return False


def render_sidebar():
    """Render sidebar configuration panel."""
    with st.sidebar:
        st.title("⚙️ Configuration")

        # ── Pipeline class selector ───────────────────────────────────────────
        available_pipelines = get_available_pipelines()
        selected_pipeline_name = st.selectbox(
            "Select Pipeline",
            list(available_pipelines.keys()),
            index=0,
        )
        pipeline_class = available_pipelines[selected_pipeline_name]

        # ── Model configuration ───────────────────────────────────────────────
        with st.expander("🔧 Model Configuration"):
            score_model = st.selectbox(
                "Scoring Model (Phase 2)",
                ["qwen-max", "qwen-turbo", "qwen-plus"],
                index=0,
            )
            chat_model = st.selectbox(
                "Chat Model (Phase 5)",
                ["qwen3.5-flash", "qwen-max", "qwen-turbo"],
                index=0,
            )
            embedding_model = st.selectbox(
                "Embedding Model (Phase 6)",
                ["text-embedding-v3", "text-embedding-v2"],
                index=0,
            )
            reflection_model = st.selectbox(
                "Reflection Model (Phase 6 synthesis)",
                ["qwen-plus", "qwen-turbo", "qwen-max"],
                index=0,
            )
            plan_model = st.selectbox(
                "Planning Model (Phase 7)",
                ["qwen-plus", "qwen-turbo", "qwen-max"],
                index=0,
            )
            reflection_interval = st.slider(
                "Reflection Interval (every N conversations)",
                min_value=1,
                max_value=20,
                value=DEFAULT_REFLECTION_INTERVAL,
                help="Phase 6 (Reflection) runs once every N conversations.",
            )
            st.session_state.reflection_interval = reflection_interval
            st.selectbox(
                "Phase 6-7 Execution",
                options=["plan_first", "concurrent"],
                format_func=lambda x: {
                    "plan_first": "🔄 Plan → Reflect  (free tier)",
                    "concurrent": "⚡ Concurrent  (paid tier)",
                }[x],
                key="execution_mode",
            )

        st.divider()

        # ── Knowledge Base loader ─────────────────────────────────────────────
        st.markdown("### 📂 Knowledge Base")

        dataset_options = list(AVAILABLE_DATASETS.keys()) + [_CUSTOM_LABEL]
        selected_label = st.selectbox("Select Dataset", dataset_options, index=0)

        if selected_label == _CUSTOM_LABEL:
            custom_path = st.text_input(
                "Custom file path",
                placeholder="e.g. C:/path/to/my_conversation.csv",
                help="Absolute path to a CSV with columns: Timestamp, Name, Role, Message",
            )
            chosen_file = custom_path.strip() if custom_path else ""
        else:
            chosen_file = str(DATA_DIR / AVAILABLE_DATASETS[selected_label])
            st.caption(f"`{AVAILABLE_DATASETS[selected_label]}`")

        feed_clicked = st.button("🔄 Feed Data", use_container_width=True)

        # No pipeline loaded yet — wait for user to click Feed Data
        if st.session_state.pipeline is None:
            st.session_state.pipeline_name = selected_pipeline_name

        # Reinit when pipeline class changes
        elif selected_pipeline_name != st.session_state.pipeline_name:
            current_file = st.session_state.active_memory_file or DEFAULT_MEMORY_FILE
            with st.spinner("Switching pipeline..."):
                ok = _reinit_pipeline(current_file, pipeline_class,
                                      score_model, chat_model, embedding_model,
                                      reflection_model, plan_model)
            st.session_state.pipeline_name = selected_pipeline_name
            if ok:
                st.success(f"Switched to {selected_pipeline_name}")
                st.session_state.pending_initial_reflection = True
                st.session_state.background_task_running = True

        # Reinit when "Feed Data" is clicked
        if feed_clicked:
            if not chosen_file:
                st.warning("Please enter a file path.")
            else:
                with st.spinner(f"Loading {selected_label}..."):
                    ok = _reinit_pipeline(chosen_file, pipeline_class,
                                          score_model, chat_model, embedding_model,
                                          reflection_model, plan_model)
                if ok:
                    st.success(f"✅ Loaded: {selected_label}")
                    st.session_state.pipeline_name = selected_pipeline_name
                    st.session_state.pending_initial_reflection = True
                    st.session_state.background_task_running = True

        # ── Memory stats ──────────────────────────────────────────────────────
        st.divider()
        st.markdown("### 📊 Memory Stats")
        if st.session_state.pipeline:
            ms = st.session_state.pipeline.memory_stream
            col1, col2 = st.columns(2)
            col1.metric("Memories", len(ms.memories))
            col2.metric("Exchanges", len(ms.raw_exchanges))
            if st.session_state.active_memory_file:
                import os
                st.caption(f"`{os.path.basename(st.session_state.active_memory_file)}`")
        else:
            st.info("No data loaded yet.")
