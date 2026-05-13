"""Default Pipeline Implementation"""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .base import BasePipeline
from memory import MemoryStream
from processors import MemoryProcessor, AgentResponder, Reflector, Planner
from config import (
    DATA_DIR,
    DEFAULT_MEMORY_FILE,
    SCORE_MODEL,
    CHAT_MODEL,
    EMBEDDING_MODEL,
    REFLECTION_SYNTHESIS_MODEL,
)


class DefaultPipeline(BasePipeline):
    """Default pipeline implementation using modular processor classes"""

    def __init__(
        self,
        memory_file: str = DEFAULT_MEMORY_FILE,
        score_model: str = SCORE_MODEL,
        chat_model: str = CHAT_MODEL,
        embedding_model: str = EMBEDDING_MODEL,
        reflection_model: str = REFLECTION_SYNTHESIS_MODEL,
        plan_model: str = SCORE_MODEL,
    ):
        self.score_model = score_model
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.reflection_model = reflection_model
        self.plan_model = plan_model

        # Per-dataset vector store path (must be computed before Reflector is built)
        memory_stem = Path(memory_file).stem
        self._vector_store_path = str(DATA_DIR / f"vectors_{memory_stem}.jsonl")

        # Initialize components
        self.memory_stream = MemoryStream(memory_file)
        self.memory_processor = MemoryProcessor(
            self.memory_stream, score_model=score_model
        )
        self.agent_responder = AgentResponder(chat_model=chat_model)
        self.reflector = Reflector(
            self.memory_stream.vector_store,
            question_model=chat_model,       # Phase 6 question gen — fast model
            synthesis_model=reflection_model, # Phase 6 synthesis — user-configurable
            embedding_model=embedding_model,
            vector_store_path=self._vector_store_path,
        )
        self.planner = Planner(plan_model=plan_model)  # Phase 7 — user-configurable

        # Load or build the vector store
        if os.path.exists(self._vector_store_path):
            self.memory_stream.vector_store.load(self._vector_store_path)
        else:
            self.memory_stream.index_memories_to_vector_store()
            self.memory_stream.vector_store.persist(self._vector_store_path)

    def get_stored_reflections(self) -> List[Dict]:
        """Extract reflection records persisted in the vector store."""
        result = []
        for rec in self.memory_stream.vector_store.records:
            if rec.get("type") == "reflection":
                meta = rec.get("metadata", {})
                result.append({
                    "id": rec.get("id", ""),
                    "type": "reflection",
                    "question": meta.get("question", ""),
                    "summary": rec.get("text", ""),
                    "recommendation": meta.get("recommendation", ""),
                    "takeaway": meta.get("takeaway", ""),
                    "source_ids": meta.get("source_ids", []),
                    "created_at": meta.get("created_at", ""),
                })
        return result

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
        """Phases 6-7: Plan and Reflect, order determined by execution_mode.

        plan_first  — Plan runs first (single call), then Reflect. Safe on free tier.
        concurrent  — Both run simultaneously via ThreadPoolExecutor (paid tier).
        """
        selected_memories = context.get("selected_memories", [])
        agent_response = context.get("agent_response", "")
        worker_input = context.get("worker_input", "")
        run_reflection = context.get("run_reflection", True)
        mode = context.get("execution_mode", "plan_first")

        reflections, plan = [], None

        if mode == "concurrent":
            executor = ThreadPoolExecutor(max_workers=2)
            try:
                futures = {}
                futures["plan"] = executor.submit(
                    self.planner.plan, worker_input, [], agent_response, selected_memories
                )
                if run_reflection:
                    futures["reflect"] = executor.submit(
                        self.reflector.reflect, selected_memories, agent_response, worker_input
                    )
                TIMEOUT = 90
                try:
                    plan = futures["plan"].result(timeout=TIMEOUT)
                except Exception as e:
                    print(f"[Pipeline] Planning error: {e}")
                    plan = f"Planning error: {e}"
                if "reflect" in futures:
                    try:
                        reflections = futures["reflect"].result(timeout=TIMEOUT)
                    except Exception as e:
                        print(f"[Pipeline] Reflection error: {e}")
            finally:
                executor.shutdown(wait=False)

        else:  # plan_first (default)
            try:
                plan = self.planner.plan(
                    worker_input, [], agent_response, selected_memories
                )
            except Exception as e:
                print(f"[Pipeline] Planning error: {e}")
                plan = f"Planning error: {e}"

            if run_reflection:
                try:
                    reflections = self.reflector.reflect(
                        selected_memories, agent_response, worker_input
                    )
                except Exception as e:
                    print(f"[Pipeline] Reflection error: {e}")

        self._persist_plan(plan, worker_input)
        return {"reflections": reflections, "plan": plan}

    def _persist_plan(self, plan, worker_input: str):
        """Save the plan to the vector store and flush to JSONL.
        Plans are stored WITHOUT embeddings so they are never returned by
        similarity search — only memories and reflections should be searchable.
        """
        if not plan or str(plan).startswith(("Planning error:", "Error")):
            return
        record = {
            "id": f"plan-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:22]}",
            "type": "plan",
            "text": plan,
            "metadata": {
                "worker_input": worker_input[:200],
                "created_at": datetime.now().isoformat(),
            },
            "embedding": [],  # intentionally empty — plans are not searchable
        }
        try:
            # Append directly (no API call) then persist
            self.memory_stream.vector_store.records.append(record)
            self.memory_stream.vector_store.persist(self._vector_store_path)
            print(f"[Pipeline] Plan saved to {self._vector_store_path}")
        except Exception as e:
            print(f"[Pipeline] Failed to save plan: {e}")
