"""Memory Stream for parsing and managing conversation memories"""

import csv
import os
import re
from datetime import datetime
from typing import List, Dict

from .vector_store import LocalVectorStore
from config import DEFAULT_TIME_GAP_THRESHOLD


class MemoryStream:
    """Manages memories, vector store, and persistence"""

    def __init__(self, memory_file: str):
        self.memory_file = memory_file
        self.raw_exchanges: List[Dict] = []
        self.memories: List[Dict] = []
        self.vector_store = LocalVectorStore()
        self._load_and_parse()

    def _load_and_parse(self):
        """Parse conversation file into exchanges and memories (supports .csv and .txt)"""
        if not os.path.exists(self.memory_file):
            return

        if self.memory_file.endswith(".csv"):
            self.raw_exchanges = self._parse_csv_file(self.memory_file)
        else:
            self.raw_exchanges = self._parse_conversation_file(self.memory_file)

        self.memories = self._group_memories(
            self.raw_exchanges, time_gap_threshold=DEFAULT_TIME_GAP_THRESHOLD
        )

    def _parse_csv_file(self, file_path: str) -> List[Dict]:
        """Parse CSV file with columns: Timestamp, Topic, Name, Role, Message"""
        exchanges = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = row.get("Timestamp", "").strip()
                speaker = row.get("Name", "").strip()
                role = row.get("Role", "").strip()
                message = row.get("Message", "").strip()
                if timestamp and speaker and message:
                    exchanges.append({
                        "timestamp": timestamp,
                        "speaker": speaker,
                        "role": role,
                        "message": message,
                    })
        return exchanges

    def _parse_conversation_file(self, file_path: str) -> List[Dict]:
        """Parse conversation file: HH:MM:SS - Name (Role): Message"""
        exchanges = []
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = re.match(
                    r"^(\d{2}:\d{2}:\d{2})\s*-\s*(.+?)\s*\((.+?)\)\s*:\s*(.+)$", line
                )
                if match:
                    timestamp, speaker, role, message = match.groups()
                    exchanges.append(
                        {
                            "timestamp": timestamp,
                            "speaker": speaker.strip(),
                            "role": role.strip(),
                            "message": message.strip(),
                        }
                    )
        return exchanges

    def _group_memories(
        self, exchanges: List[Dict], time_gap_threshold: int = 5
    ) -> List[Dict]:
        """Group exchanges into coherent memories by time proximity"""
        if not exchanges:
            return []

        memories = []
        current_group = [exchanges[0]]

        for i in range(1, len(exchanges)):
            prev_time = datetime.strptime(exchanges[i - 1]["timestamp"], "%H:%M:%S")
            curr_time = datetime.strptime(exchanges[i]["timestamp"], "%H:%M:%S")
            time_diff_seconds = (curr_time - prev_time).total_seconds()
            time_diff_minutes = time_diff_seconds / 60

            if time_diff_minutes > time_gap_threshold:
                memories.append(self._group_to_memory(current_group))
                current_group = [exchanges[i]]
            else:
                current_group.append(exchanges[i])

        if current_group:
            memories.append(self._group_to_memory(current_group))

        return memories

    def _group_to_memory(self, group: List[Dict]) -> Dict:
        """Convert a group of exchanges into a memory dict"""
        timestamp_start = group[0]["timestamp"]
        timestamp_end = group[-1]["timestamp"]
        speakers = list(set(ex["speaker"] for ex in group))
        full_text = "\n".join(
            [
                f"{ex['timestamp']} - {ex['speaker']} ({ex['role']}): {ex['message']}"
                for ex in group
            ]
        )

        return {
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "speakers": speakers,
            "full_text": full_text,
            "exchange_count": len(group),
        }

    def index_memories_to_vector_store(self):
        """Add all memories to the vector store"""
        for i, memory in enumerate(self.memories):
            self.vector_store.add_record(
                {
                    "id": f"memory-{i+1}",
                    "type": "memory",
                    "text": memory["full_text"],
                    "metadata": {
                        "timestamp_start": memory["timestamp_start"],
                        "timestamp_end": memory["timestamp_end"],
                        "speakers": memory["speakers"],
                        "exchange_count": memory["exchange_count"],
                    },
                }
            )
