"""Reflector for Phase 6: Reflection and Insight Synthesis"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from memory import LocalVectorStore
from config import (
    REFLECTION_QUESTION_MODEL,
    REFLECTION_SYNTHESIS_MODEL,
    EMBEDDING_MODEL,
    VECTOR_STORE_PATH,
    client,
)


class Reflector:
    """Phase 6: Generate reflections and synthesize insights"""

    def __init__(
        self,
        vector_store: LocalVectorStore,
        question_model: str = REFLECTION_QUESTION_MODEL,
        synthesis_model: str = REFLECTION_SYNTHESIS_MODEL,
        embedding_model: str = EMBEDDING_MODEL,
    ):
        self.vector_store = vector_store
        self.question_model = question_model
        self.synthesis_model = synthesis_model
        self.embedding_model = embedding_model

    def reflect(
        self, selected_memories: List[Dict], agent_response: str, worker_input: str
    ) -> List[Dict]:
        """Run Phase 6: generate questions, retrieve, and synthesize reflections"""
        recent_memories = selected_memories
        if not recent_memories:
            return []

        questions = self._generate_questions(recent_memories)

        reflections = []
        for question in questions:
            records = self._retrieve_related_records(question)
            reflection = self._synthesize_reflection(records, question)
            reflections.append(reflection)

            self.vector_store.add_record(
                {
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
                }
            )

        self.vector_store.persist(VECTOR_STORE_PATH)
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

Return only the questions as a JSON array of strings."""

        try:
            completion = client.chat.completions.create(
                model=self.question_model,
                messages=[{"role": "user", "content": prompt}],
            )
            text = completion.choices[0].message.content.strip()
            questions = json.loads(text)
            if isinstance(questions, list):
                return questions[:top_n]
        except Exception:
            pass

        return [line.strip() for line in text.splitlines() if line.strip()][:top_n]

    def _retrieve_related_records(self, query: str, top_k: int = 10) -> List[Dict]:
        """Retrieve records similar to the query using embeddings"""
        try:
            query_embedding = client.embeddings.create(
                model=self.embedding_model, input=query
            ).data[0].embedding
            return self.vector_store.query(query_embedding, top_k=top_k)
        except Exception as e:
            print(f"[Reflector] Error retrieving related records: {e}")
            return []

    def _synthesize_reflection(self, records: List[Dict], question: str) -> Dict:
        """Synthesize a reflection from retrieved records"""
        if not records:
            summary = "No related records were found for this reflection query."
            recommendation = ""
            takeaway = ""
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

Provide a JSON response with these keys:
- summary: A short summary of the key operational insight
- recommendation: Any safety / procedure recommendation
- takeaway: The most important takeaway
"""
            try:
                completion = client.chat.completions.create(
                    model=self.synthesis_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = completion.choices[0].message.content.strip()
                result = json.loads(text)
                summary = result.get("summary", "").strip()
                recommendation = result.get("recommendation", "").strip()
                takeaway = result.get("takeaway", "").strip()
            except Exception:
                summary = text
                recommendation = ""
                takeaway = ""

        reflection = {
            "id": str(uuid.uuid4()),
            "type": "reflection",
            "question": question,
            "summary": summary,
            "recommendation": recommendation,
            "takeaway": takeaway,
            "source_ids": [rec["id"] for rec in records] if records else [],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        return reflection
