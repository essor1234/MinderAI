"""Planner for Phase 7: Proactive Plan Generation"""

import re
from typing import List, Dict, Optional

from config import SCORE_MODEL, make_client


def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


class Planner:
    """Phase 7: Generate proactive conversational plans"""

    def __init__(self, plan_model: str = SCORE_MODEL):
        self.plan_model = plan_model
        self._client = make_client()  # own instance — not shared with reflector thread

    def plan(
        self,
        worker_input: str,
        recent_reflections: List[Dict],
        agent_response: str,
        selected_memories: Optional[List[Dict]] = None,
    ) -> Optional[str]:
        """Generate proactive plans based on Phase 5 output and reflections"""
        return self._generate_plan(
            worker_input,
            agent_response,
            recent_reflections,
            selected_memories or [],
        )

    def _generate_plan(
        self,
        worker_input: str,
        agent_response: str,
        recent_reflections: List[Dict],
        selected_memories: List[Dict],
    ) -> str:
        """Generate a plan using the LLM"""
        print(f"\n[Planner] ── Phase 7 start ──────────────────────────────")
        print(f"[Planner] Model        : {self.plan_model}")
        print(f"[Planner] Worker input : {worker_input[:120]!r}")
        print(f"[Planner] Memories     : {len(selected_memories)} selected")
        print(f"[Planner] Reflections  : {len(recent_reflections)} recent")

        reflections_text = "\n".join(
            [f"- {r['summary']}" for r in recent_reflections[-3:]]
        )

        memory_context = ""
        if selected_memories:
            snippets = "\n".join(
                f"  [{m['timestamp_start']}] {m['full_text'][:200].replace(chr(10), ' ')}"
                for m in selected_memories[:3]
            )
            memory_context = f"\nKey Memories (Phase 5 selection):\n{snippets}"

        prompt = f"""You are the Minder AI Agent, a voice-first conversational assistant on a factory floor. You do not have a physical body, and you cannot perform management tasks like scheduling training, rewriting manuals, or conducting drills. Your ONLY capability is talking to workers.

Given the context below, generate a MAXIMUM OF TWO proactive conversational plans. Each plan must state what you will ASK or SAY to a specific role in a future conversation to verify knowledge or surface issues.

Worker Input: {worker_input}
Agent Response (Phase 5): {agent_response[:400] if agent_response else "N/A"}{memory_context}
Recent Reflections: {reflections_text if reflections_text else "No recent reflections yet."}

Generate the plan(s) in this exact format:
"[Plan] The next time I speak with a [Role/Person], I will proactively ask/notify them about [Specific Issue]."
"""

        print(f"[Planner] Calling API...")
        try:
            completion = self._client.chat.completions.create(
                model=self.plan_model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0,
            )
            raw = completion.choices[0].message.content.strip()
            result = _strip_think_tags(raw)
            print(f"[Planner] API response received ({len(raw)} chars raw)")
            print(f"[Planner] Plan output  :\n{result}")
            print(f"[Planner] ── Phase 7 done ───────────────────────────────\n")
            return result
        except Exception as e:
            print(f"[Planner] ERROR: {e}")
            print(f"[Planner] ── Phase 7 failed ─────────────────────────────\n")
            return f"Error generating plan: {str(e)}"
