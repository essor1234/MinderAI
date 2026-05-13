"""Factory Floor Chat Interface (Left Column)"""

import time

import streamlit as st


def render_factory_floor_display():
    """Render the chat history (safe for columns)"""
    st.subheader("🏭 Factory Floor")

    pipeline = st.session_state.get("pipeline")
    chat_history = st.session_state.get("chat_history", [])
    bg_running = st.session_state.get("background_task_running", False)

    # No dataset loaded yet
    if not pipeline and not chat_history:
        st.info("Select a dataset from the sidebar and click **Feed Data** to begin.")
        return

    # Initial load in progress — show loading state in the chat window
    if bg_running and not chat_history:
        with st.chat_message("assistant"):
            st.markdown(
                "⏳ **Feeding data into model...**  \n"
                "Analysing the dataset and building initial insights. "
                "This may take a moment — please wait."
            )
        return

    # Pipeline ready, no conversation started yet
    if pipeline and not chat_history:
        with st.chat_message("assistant"):
            st.markdown(
                "✅ **Ready to chat!**  \n"
                "Dataset loaded and analysed. Ask me anything about "
                "what you've seen on the floor."
            )
        return

    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "elapsed_s" in message:
                st.caption(f"⏱ {message['elapsed_s']}s")


def handle_factory_input():
    """Render the chat input and handle the 3-phase processing flow."""

    # ── Phase 0: full pipeline run on initial dataset feed (Phases 1-7) ─────────
    if st.session_state.get("pending_initial_reflection"):
        st.session_state.pending_initial_reflection = False
        try:
            pipeline = st.session_state.pipeline
            memories = pipeline.memory_stream.memories if pipeline else []
            if memories:
                synthetic_input = (
                    "What are the key operations, procedures, and important "
                    "knowledge in this dataset?"
                )
                with st.spinner("⏳ Running initial analysis (Phases 1-7)..."):
                    try:
                        # Phases 1-5: score and select memories, generate context
                        sync_result = pipeline.run_synchronous_phases(synthetic_input)
                        st.session_state.selected_memories = sync_result.get("selected_memories", [])

                        # Phases 6-7: reflect then plan
                        sync_result["run_reflection"] = True
                        sync_result["execution_mode"] = st.session_state.get("execution_mode", "plan_first")
                        async_result = pipeline.run_asynchronous_phases(sync_result)
                        st.session_state.reflections = pipeline.get_stored_reflections()
                        st.session_state.plan = async_result.get("plan")
                    except Exception as e:
                        st.session_state.reflections = []
                        st.session_state.plan = f"Initial analysis error: {e}"
        except Exception as e:
            print(f"[Phase 0] Unexpected error: {e}")
        finally:
            st.session_state.background_task_running = False
        st.rerun()
        return

    # ── Phase C: run async phases (6-7) queued by a previous render ──────────
    if st.session_state.get("pending_async_phases"):
        sync_result = st.session_state.pending_sync_result
        count = st.session_state.conversation_count
        interval = st.session_state.reflection_interval
        sync_result["run_reflection"] = (count % interval == 0)
        sync_result["execution_mode"] = st.session_state.get("execution_mode", "plan_first")
        st.session_state.pending_async_phases = False
        st.session_state.pending_sync_result = {}

        with st.spinner("⏳ Running reflections & planning (Phases 6-7)..."):
            try:
                async_result = st.session_state.pipeline.run_asynchronous_phases(sync_result)
                st.session_state.reflections = st.session_state.pipeline.get_stored_reflections()
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
                _t0 = time.time()
                sync_result = st.session_state.pipeline.run_synchronous_phases(worker_input)
                _elapsed = round(time.time() - _t0, 1)
                st.session_state.selected_memories = sync_result.get("selected_memories", [])
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": sync_result["agent_response"], "elapsed_s": _elapsed}
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
    # Safeguard: clear stuck flag when no pending work remains
    if (st.session_state.get("background_task_running", False)
            and not st.session_state.get("pending_initial_reflection")
            and not st.session_state.get("pending_pipeline_run")
            and not st.session_state.get("pending_async_phases")):
        print("[Phase A] Clearing stuck background_task_running flag")
        st.session_state.background_task_running = False

    is_loading = st.session_state.get("background_task_running", False)
    if is_loading:
        placeholder = (
            "⏳ Loading dataset, please wait..."
            if not st.session_state.get("chat_history")
            else "⏳ Processing response, please wait..."
        )
    else:
        placeholder = "Ask the Minder Agent..."
    worker_input = st.chat_input(placeholder, disabled=is_loading)

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
