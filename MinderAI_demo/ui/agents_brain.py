"""Agent's Brain Debug Panel (Right Column)"""

import streamlit as st


def render_agents_brain():
    """Render right column: Agent's Brain (debug panel)"""
    st.subheader("🧠 Agent's Brain")

    # Tab interface
    tab1, tab2, tab3 = st.tabs(["📌 Memories", "🔍 Reflections", "📋 Plans"])

    with tab1:
        _render_memories_tab()

    with tab2:
        _render_reflections_tab()

    with tab3:
        _render_plans_tab()


def _render_memories_tab():
    """Render selected memories tab"""
    st.markdown("### Selected Memories (Phase 4)")
    if st.session_state.selected_memories:
        for i, mem in enumerate(st.session_state.selected_memories, 1):
            with st.expander(
                f"Memory {i} (Score: {mem.get('final_score', 0):.3f})"
            ):
                st.write(f"**Time:** {mem.get('timestamp_start')} - {mem.get('timestamp_end')}")
                st.write(f"**Speakers:** {', '.join(mem.get('speakers', []))}")
                st.write(f"**Content:**")
                st.write(mem.get("full_text", ""))

                # Show normalized scores
                if "normalized_scores" in mem:
                    norm = mem["normalized_scores"]
                    cols = st.columns(3)
                    cols[0].metric("Recency", f"{norm.get('recency_norm', 0):.2f}")
                    cols[1].metric("Importance", f"{norm.get('importance_norm', 0):.2f}")
                    cols[2].metric("Relevance", f"{norm.get('relevance_norm', 0):.2f}")
    else:
        st.info("No memories selected yet. Start a conversation.")


def _render_reflections_tab():
    """Render reflections tab"""
    st.markdown("### Reflections (Phase 6)")
    if st.session_state.reflections:
        for i, reflection in enumerate(st.session_state.reflections, 1):
            with st.expander(
                f"Reflection {i}: {reflection.get('question', 'Untitled')}"
            ):
                st.write(f"**Question:** {reflection.get('question', 'N/A')}")
                st.write(f"**Summary:** {reflection.get('summary', 'N/A')}")
                if reflection.get("recommendation"):
                    st.write(f"**Recommendation:** {reflection.get('recommendation', '')}")
                if reflection.get("takeaway"):
                    st.write(f"**Takeaway:** {reflection.get('takeaway', '')}")
    elif st.session_state.background_task_running:
        st.info("⏳ Reflections processing in background...")
    else:
        st.info("No reflections yet. Continue the conversation.")


def _render_plans_tab():
    """Render plans tab"""
    st.markdown("### Plans (Phase 7)")
    if st.session_state.plan:
        st.write(st.session_state.plan)
    elif st.session_state.background_task_running:
        st.info("⏳ Plans processing in background...")
    else:
        st.info("No plans generated yet.")
