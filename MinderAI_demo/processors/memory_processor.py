"""Memory Processor for Phases 1-4: Parse, Score, Normalize, Select memories"""

from typing import List, Dict, Tuple, Optional
import streamlit as st

from memory import MemoryStream
from config import (
    SCORE_MODEL,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_SYSTEM_PROMPT_TOKENS,
    DEFAULT_SCORE_THRESHOLD,
    client,
)
from utils import estimate_tokens


class MemoryProcessor:
    """Phases 1-4: Parse, Score, Normalize, Select memories"""

    def __init__(
        self,
        memory_stream: MemoryStream,
        score_model: str = SCORE_MODEL,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        system_prompt_tokens: int = DEFAULT_SYSTEM_PROMPT_TOKENS,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ):
        self.memory_stream = memory_stream
        self.score_model = score_model
        self.context_window = context_window
        self.system_prompt_tokens = system_prompt_tokens
        self.score_threshold = score_threshold
        self.current_time = self._get_current_time()

    def _get_current_time(self) -> str:
        """Get latest timestamp from memories"""
        if self.memory_stream.memories:
            return self.memory_stream.memories[-1]["timestamp_end"]
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def process(self, worker_input: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Run Phases 1-4: parse, score, normalize, and select memories.
        Returns: (selected_memories, normalized_memories)
        """
        memories = self.memory_stream.memories

        current_situation = (
            "Filter factory floor conversations to identify meaningful operational/safety knowledge"
        )
        scored_memories = self._score_memories(memories, worker_input, current_situation)

        normalized_memories = self._normalize_scores(scored_memories)
        filtered_memories = self._filter_memories(
            normalized_memories, threshold=self.score_threshold
        )

        selected_memories, tokens_used = self._select_for_context(filtered_memories)

        return selected_memories, normalized_memories

    def _build_scoring_prompt(
        self, memory: Dict, current_situation: str, worker_input: str
    ) -> str:
        """Build prompt for scoring a single memory (removed Experience criterion)"""
        prompt = f"""Given the current situation and a worker's question, rate this memory on a scale of 1 to 10 for three criteria: Recency, Importance, and Relevance.

Current Time: {self.current_time}
Current Situation/Worker Question: {worker_input}
Context: {current_situation}

Memory Timestamp: {memory['timestamp_start']}
Memory Record:
{memory['full_text']}

Scoring Criteria:
1. Recency: How recent is this memory relative to the Current Time? (1 = very old/outdated, 10 = just happened)
2. Importance: How critical is this operational knowledge? (1 = mundane noise, venting, or personal complaints, 10 = highly critical unwritten tribal wisdom, safety hazards, or SOP contradictions)
3. Relevance: How closely does this memory relate to the worker's question? (1 = completely unrelated, 10 = directly answers or provides context to the question)

Output your response in the following EXACT format (one score per line):
Recency: [Score]
Importance: [Score]
Relevance: [Score]"""
        return prompt

    def _extract_scores(self, response_text: str) -> Optional[Dict]:
        """Extract three scores from LLM response"""
        lines = response_text.strip().split("\n")
        scores = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                try:
                    value = int(value.strip())
                    if key in ["recency", "importance", "relevance"]:
                        scores[key] = value
                except ValueError:
                    pass

        if len(scores) == 3 and all(
            k in scores for k in ["recency", "importance", "relevance"]
        ):
            return scores
        return None

    def _score_memories(
        self, memories: List[Dict], worker_input: str, current_situation: str
    ) -> List[Dict]:
        """Score all memories using qwen-max (Phase 2)"""
        scored_memories = []

        for memory in memories:
            prompt = self._build_scoring_prompt(memory, current_situation, worker_input)
            try:
                completion = client.chat.completions.create(
                    model=self.score_model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30.0,
                )
                response_text = completion.choices[0].message.content
                scores = self._extract_scores(response_text)

                if scores:
                    memory["scores"] = scores
                    memory["raw_response"] = response_text
                    scored_memories.append(memory)
            except Exception as e:
                st.warning(f"Error scoring memory: {str(e)}")

        return scored_memories

    def _normalize_scores(self, scored_memories: List[Dict]) -> List[Dict]:
        """Apply min-max normalization to scores (Phase 3)"""
        if not scored_memories:
            return []

        criteria = ["recency", "importance", "relevance"]
        raw_scores = {crit: [] for crit in criteria}

        for memory in scored_memories:
            for crit in criteria:
                raw_scores[crit].append(memory["scores"][crit])

        min_max = {}
        for crit in criteria:
            min_val = min(raw_scores[crit])
            max_val = max(raw_scores[crit])
            min_max[crit] = (min_val, max_val)

        normalized_memories = []
        for memory in scored_memories:
            normalized = {}
            final_score = 0

            for crit in criteria:
                raw = memory["scores"][crit]
                min_val, max_val = min_max[crit]

                if max_val == min_val:
                    norm = 0.5
                else:
                    norm = (raw - min_val) / (max_val - min_val)

                normalized[f"{crit}_raw"] = raw
                normalized[f"{crit}_norm"] = norm
                final_score += norm

            memory["normalized_scores"] = normalized
            memory["final_score"] = final_score  # Max 3.0 with 3 criteria
            normalized_memories.append(memory)

        return normalized_memories

    def _filter_memories(
        self, normalized_memories: List[Dict], threshold: float = 2.0
    ) -> List[Dict]:
        """Filter memories by score threshold and sort (Phase 3 cont.)"""
        filtered = [mem for mem in normalized_memories if mem["final_score"] >= threshold]
        sorted_memories = sorted(filtered, key=lambda x: x["final_score"], reverse=True)
        return sorted_memories

    def _select_for_context(
        self, filtered_memories: List[Dict]
    ) -> Tuple[List[Dict], int]:
        """Select top memories that fit context window (Phase 4)"""
        available_tokens = self.context_window - self.system_prompt_tokens
        selected = []
        tokens_used = 0

        for memory in filtered_memories:
            mem_tokens = estimate_tokens(memory["full_text"])
            if tokens_used + mem_tokens <= available_tokens:
                selected.append(memory)
                tokens_used += mem_tokens

        return selected, tokens_used
