"""Agent Responder for Phase 5: Response Generation"""

from typing import List, Dict

from config import CHAT_MODEL, client


class AgentResponder:
    """Phase 5: Build prompt and generate response using qwen3.5-flash"""

    def __init__(self, chat_model: str = CHAT_MODEL):
        self.chat_model = chat_model

    def generate_response(
        self, selected_memories: List[Dict], worker_input: str, current_time: str
    ) -> str:
        """Generate agent response using selected memories and worker input"""
        final_prompt = self._build_final_prompt(selected_memories, worker_input, current_time)

        try:
            completion = client.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": final_prompt}],
                timeout=30.0,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def _build_final_prompt(
        self, selected_memories: List[Dict], worker_input: str, current_time: str
    ) -> str:
        """Build the final prompt for the agent"""
        agent_description = """[Agent's Summary Description]
Name: Minder Agent
Core Directive: Assist factory floor workers with Standard Operating Procedures (SOPs) and safely acquire, verify, and document unwritten tribal knowledge. Ignore venting, noise, and jokes."""

        memories_text = "Summary of relevant context from the Agent's memory:"
        for i, mem in enumerate(selected_memories):
            memories_text += f"\n\nMemory {i+1} (Score: {mem['final_score']:.3f}):\n{mem['full_text']}"

        final_prompt = f"""{agent_description}

Current Time: {current_time}

Worker Input (Question/Observation): {worker_input}

{memories_text}

Given the worker's input and the relevant context retrieved from memory, how should the Minder Agent respond? If there is a contradiction in the memory context, ask the worker for clarification or escalate to a manager."""

        return final_prompt
