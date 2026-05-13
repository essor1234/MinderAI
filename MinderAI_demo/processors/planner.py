"""Planner for Phase 7: Proactive Plan Generation"""

from typing import List, Dict, Optional

from config import SCORE_MODEL, client


class Planner:
    """Phase 7: Generate proactive conversational plans"""

    def __init__(self, plan_model: str = SCORE_MODEL):
        self.plan_model = plan_model
        self.issue_keywords = [
            "overheat",
            "overheating",
            "broken",
            "not working",
            "issue",
            "problem",
            "recurring",
            "fail",
            "error",
        ]

    def plan(
        self,
        worker_input: str,
        recent_reflections: List[Dict],
        agent_response: str,
    ) -> Optional[str]:
        """Generate proactive plans based on worker input and reflections"""
        if not self._should_trigger_planning(worker_input):
            return None

        plan = self._generate_plan(worker_input, recent_reflections)
        return plan

    def _should_trigger_planning(self, worker_input: str) -> bool:
        """Check if planning should be triggered based on keywords"""
        return any(keyword in worker_input.lower() for keyword in self.issue_keywords)

    def _generate_plan(self, worker_input: str, recent_reflections: List[Dict]) -> str:
        """Generate a plan using the LLM"""
        reflections_text = "\n".join(
            [f"- {r['summary']}" for r in recent_reflections[-3:]]
        )

        prompt = f"""You are the Minder AI Agent, a voice-first conversational assistant on a factory floor. You do not have a physical body, and you cannot perform management tasks like scheduling training, rewriting manuals, or conducting drills. Your ONLY capability is talking to workers.

Given the worker's input and recent reflections, generate a MAXIMUM OF TWO proactive conversational plans. The plans must dictate what you will ASK or SAY to specific personnel in future conversations to verify knowledge or report issues.

Worker Input: {worker_input}
Recent Reflections: {reflections_text if reflections_text else "No recent reflections yet."}

Generate the plan(s) in this exact format: 
"[Plan] The next time I speak with a [Role/Person], I will proactively ask/notify them about [Specific Issue]."
"""

        try:
            completion = client.chat.completions.create(
                model=self.plan_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating plan: {str(e)}"
