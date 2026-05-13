"""Local Vector Store for in-memory embeddings and similarity search"""

import json
import os
from typing import List, Dict

from config import EMBEDDING_MODEL, client


class LocalVectorStore:
    """In-memory vector store with simple cosine similarity search"""

    def __init__(self):
        self.records: List[Dict] = []

    def add_record(self, record: Dict):
        """Add a record to the store, computing embeddings if needed"""
        if "embedding" not in record or record["embedding"] is None:
            record["embedding"] = self._embed_text(record["text"])
        self.records.append(record)

    def _embed_text(self, text: str) -> List[float]:
        """Get embedding for text using text-embedding-v3"""
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return response.data[0].embedding

    def query(self, query_embedding: List[float], top_k: int = 10) -> List[Dict]:
        """Search by embedding and return top-k similar records"""
        from utils import cosine_similarity

        scored = []
        for record in self.records:
            score = cosine_similarity(query_embedding, record["embedding"])
            scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:top_k]]

    def persist(self, path: str):
        """Save records to JSONL file"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for record in self.records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load(self, path: str):
        """Load records from JSONL file"""
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.records.append(json.loads(line))
