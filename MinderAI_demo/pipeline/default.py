"""Default Pipeline Implementation"""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict

from .base import BasePipeline
from memory import MemoryStream
from processors import MemoryProcessor, AgentResponder, Reflector, Planner
from config import (
    DATA_DIR,
    DEFAULT_MEMORY_FILE,
    SCORE_MODEL,
    CHAT_MODEL,
    EMBEDDING_MODEL,
)


class DefaultPipeline(BasePipeline):
    """Default pipeline implementation using modular processor classes"""

    def __init__(
        self,
        memory_file: str = DEFAULT_MEMORY_FILE,
        score_model: str = SCORE_MODEL,
        chat_model: str = CHAT_MODEL,
        embedding_model: str = EMBEDDING_MODEL,
    ):
        self.score_model = score_model
        self.chat_model = chat_model
        self.embedding_model = embedding_model

        # Initialize components
        self.memory_stream = MemoryStream(memory_file)
        self.memory_processor = MemoryProcessor(
            self.memory_stream, score_model=score_model
        )
        self.agent_responder = AgentResponder(chat_model=chat_model)
        self.reflector = Reflector(
            self.memory_stream.vector_store,
            question_model=chat_model,
            synthesis_model=score_model,
            embedding_model=embedding_model,
        )
        self.planner = Planner(plan_model=score_model)

        # Per-dataset vector store (avoids cross-topic cache collisions)
        memory_stem = Path(memory_file).stem
        self._vector_store_path = str(DATA_DIR / f"vectors_{memory_stem}.jsonl")

        if os.path.exists(self._vector_store_path):
            self.memory_stream.vector_store.load(self._vector_store_path)
        else:
            self.memory_stream.index_memories_to_vector_store()
            # Persist immediately so future startups skip re-embedding
            self.memory_stream.vector_store.persist(self._vector_store_path)

    def run_synchronous_phases(self, worker_input: str) -> Dict:
        """Phases 1-5: Process memories and generate response"""
        selected_memories, all_normalized = self.memory_processor.process(worker_input)

        current_time = self.memory_processor.current_time
        agent_response = self.agent_responder.generate_response(
            selected_memories, worker_input, current_time
        )

        return {
            "worker_input": worker_input,
            "agent_response": agent_response,
            "selected_memories": selected_memories,
            "all_normalized_memories": all_normalized,
            "current_time": current_time,
        }

    def run_asynchronous_phases(self, context: Dict) -> Dict:
        """Phases 6-7: Reflect and plan concurrently via ThreadPoolExecutor"""
        selected_memories = context.get("selected_memories", [])
        agent_response = context.get("agent_response", "")
        worker_input = context.get("worker_input", "")
        previous_reflections = context.get("previous_reflections", [])
        run_reflection = context.get("run_reflection", True)

        reflections = []
        plan = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            if run_reflection:
                futures["reflect"] = executor.submit(
                    self.reflector.reflect, selected_memories, agent_response, worker_input
                )
            futures["plan"] = executor.submit(
                self.planner.plan, worker_input, previous_reflections, agent_response
            )

            if "reflect" in futures:
                reflections = futures["reflect"].result()
            plan = futures["plan"].result()

        return {"reflections": reflections, "plan": plan}
