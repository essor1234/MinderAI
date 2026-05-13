"""Reflector for Phase 6: Reflection and Insight Synthesis"""

import json
import re
import uuid
from datetime import datetime
from typing import List, Dict

from memory import LocalVectorStore
from config import (
    REFLECTION_QUESTION_MODEL,
    REFLECTION_SYNTHESIS_MODEL,
    EMBEDDING_MODEL,
    make_client,
)


def _extract_json_text(text: str) -> str:
    """Strip <think> blocks and markdown code fences before JSON parsing."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    text = re.sub(r'```(?:json)?\s*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL).strip()
    return text


class Reflector:
    """Phase 6: Generate reflections and synthesize insights"""

    def __init__(
        self,
        vector_store: LocalVectorStore,
        question_model: str = REFLECTION_QUESTION_MODEL,
        synthesis_model: str = REFLECTION_SYNTHESIS_MODEL,
        embedding_model: str = EMBEDDING_MODEL,
        vector_store_path: str = "",
    ):
        self.vector_store = vector_store
        self.question_model = question_model
        self.synthesis_model = synthesis_model
        self.embedding_model = embedding_model
        self.vector_store_path = vector_store_path
        self._client = make_client()  # own instance — not shared with planner thread

    def reflect(
        self, selected_memories: List[Dict], agent_response: str, worker_input: str
    ) -> List[Dict]:
        """Run Phase 6: generate questions, retrieve, and synthesize reflections"""
        if not selected_memories:
            return []

        questions = self._generate_questions(selected_memories)
        if not questions:
            return []

        reflections = []
        for question in questions:
            records = self._retrieve_related_records(question)
            reflection = self._synthesize_reflection(records, question)
            reflections.append(reflection)

            self.vector_store.add_record({
                "id": reflection["id"],
                "type": "reflection",
                "text": reflection["summary"],
                "metadata": {
                    "question": reflection["question"],
                    "recommendation": reflection.get("recommendation", ""),
                    "takeaway": reflection.get("takeaway", ""),
                    "source_ids": reflection.get("source_ids", []),
                    "created_at": reflection.get("created_at", ""),
                },
            })

        if self.vector_store_path:
            self.vector_store.persist(self.vector_store_path)
        return reflections

    def _generate_questions(self, recent_memories: List[Dict], top_n: int = 2) -> List[str]:
        """Generate reflection questions from recent memories"""
        memory_snippets = "\n\n".join(
            f"{i+1}. {mem['timestamp_start']} - {mem['full_text'][:300].replace(chr(10), ' ')}"
            for i, mem in enumerate(recent_memories[:5])
        )
        prompt = f"""Based on these recent factory-floor memory excerpts, generate {top_n} reflection questions that would help identify important operational insights, unspoken safety knowledge, or procedure gaps.

Memory excerpts:
{memory_snippets}

Return only the questions as a JSON array of strings. Example: ["Question 1?", "Question 2?"]"""

        text = ""
        try:
            completion = self._client.chat.completions.create(
                model=self.question_model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0,
            )
            text = completion.choices[0].message.content.strip()
            clean = _extract_json_text(text)
            questions = json.loads(clean)
            if isinstance(questions, list):
                return [q for q in questions if isinstance(q, str) and q.strip()][:top_n]
        except Exception as e:
            print(f"[Reflector] _generate_questions error: {e}")

        # Fallback: treat non-empty lines as questions
        return [line.strip() for line in text.splitlines() if line.strip()][:top_n]

    def _retrieve_related_records(self, query: str, top_k: int = 10) -> List[Dict]:
        """Retrieve records similar to the query using embeddings"""
        try:
            query_embedding = self._client.embeddings.create(
                model=self.embedding_model, input=query, timeout=30.0
            ).data[0].embedding
            return self.vector_store.query(query_embedding, top_k=top_k)
        except Exception as e:
            print(f"[Reflector] Error retrieving related records: {e}")
            return []

    def _synthesize_reflection(self, records: List[Dict], question: str) -> Dict:
        """Synthesize a reflection from retrieved records"""
        summary = ""
        recommendation = ""
        takeaway = ""

        if not records:
            summary = "No related records were found for this reflection query."
        else:
            context = "\n\n".join(
                f"- [{rec['type']}] {rec['id']}: {rec['text'][:400].replace(chr(10), ' ')}"
                for rec in records
            )
            prompt = f"""Review the related records below and answer the reflection question clearly and concisely.

Reflection question:
{question}

Related records:
{context}

Respond with ONLY a JSON object using these exact keys:
{{"summary": "...", "recommendation": "...", "takeaway": "..."}}"""

            text = ""
            try:
                completion = self._client.chat.completions.create(
                    model=self.synthesis_model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30.0,
                )
                text = completion.choices[0].message.content.strip()
                clean = _extract_json_text(text)
                result = json.loads(clean)
                summary = result.get("summary", "").strip()
                recommendation = result.get("recommendation", "").strip()
                takeaway = result.get("takeaway", "").strip()
            except Exception as e:
                print(f"[Reflector] _synthesize_reflection error: {e}")
                summary = text or "Synthesis failed."

        return {
            "id": str(uuid.uuid4()),
            "type": "reflection",
            "question": question,
            "summary": summary,
            "recommendation": recommendation,
            "takeaway": takeaway,
            "source_ids": [rec["id"] for rec in records] if records else [],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
