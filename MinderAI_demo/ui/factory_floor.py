"""Factory Floor Chat Interface (Left Column)"""

import streamlit as st


def render_factory_floor_display():
    """Render the chat history (safe for columns)"""
    st.subheader("🏭 Factory Floor")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_factory_input():
    """Render the chat input and handle the 3-phase processing flow."""

    # ── Phase C: run async phases (6-7) queued by a previous render ──────────
    if st.session_state.get("pending_async_phases"):
        sync_result = st.session_state.pending_sync_result
        count = st.session_state.conversation_count
        interval = st.session_state.reflection_interval
        sync_result["run_reflection"] = (count % interval == 0)
        sync_result["previous_reflections"] = st.session_state.reflections
        st.session_state.pending_async_phases = False
        st.session_state.pending_sync_result = {}

        with st.spinner("⏳ Running reflections & planning (Phases 6-7)..."):
            try:
                async_result = st.session_state.pipeline.run_asynchronous_phases(sync_result)
                st.session_state.reflections = async_result.get("reflections", [])
                st.session_state.plan = async_result.get("plan")
            except Exception as e:
                st.session_state.reflections = []
                st.session_state.plan = f"Error in async phases: {str(e)}"
            finally:
                st.session_state.background_task_running = False

        st.rerun()
        return

    # ── Phase B: user message is visible — now run phases 1-5 ────────────────
    if st.session_state.get("pending_pipeline_run"):
        worker_input = st.session_state.pending_worker_input
        st.session_state.pending_pipeline_run = False
        st.session_state.pending_worker_input = None

        with st.spinner("⏳ Processing phases 1-5..."):
            try:
                sync_result = st.session_state.pipeline.run_synchronous_phases(worker_input)
                st.session_state.selected_memories = sync_result.get("selected_memories", [])
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": sync_result["agent_response"]}
                )
                st.session_state.conversation_count += 1
                st.session_state.pending_async_phases = True
                st.session_state.pending_sync_result = sync_result
                st.session_state.background_task_running = True
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                return

        st.rerun()
        return

    # ── Phase A: receive new user input ───────────────────────────────────────
    worker_input = st.chat_input("Ask the Minder Agent...")

    # Guard against stale re-submission (Streamlit quirk)
    if worker_input and worker_input == st.session_state.get("last_processed_input"):
        return

    if worker_input:
        if not st.session_state.pipeline:
            st.error("No data loaded. Use 'Feed Data' in the sidebar first.")
            return

        # Record input, show message immediately, then rerun to trigger Phase B
        st.session_state.last_processed_input = worker_input
        st.session_state.chat_history.append({"role": "user", "content": worker_input})
        st.session_state.pending_pipeline_run = True
        st.session_state.pending_worker_input = worker_input
        st.rerun()
