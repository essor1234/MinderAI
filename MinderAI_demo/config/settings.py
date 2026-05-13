"""Configuration and constants for Minder AI"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


# MinderAI_demo/ directory (absolute, regardless of CWD)
MINDER_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = MINDER_DIR / "data"

# Load .env from project root (3 levels up from config/)
ENV_PATH = MINDER_DIR.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# API Configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = os.getenv("DASHSCOPE_API_URL")

# Centralized OpenAI Client (main thread only)
client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_API_URL,
)


def make_client() -> OpenAI:
    """Create a fresh client instance — call once per thread for thread safety."""
    return OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_API_URL)

# File Paths (absolute, anchored to MinderAI_demo/data/)
DEFAULT_MEMORY_FILE = str(DATA_DIR / "topic1_construction_welding.csv")
VECTOR_STORE_PATH = str(DATA_DIR / "vector_memories.jsonl")
REFLECTIONS_PATH = str(DATA_DIR / "reflections.jsonl")

# Available pre-loaded datasets (display name → filename inside DATA_DIR)
AVAILABLE_DATASETS = {
    "Topic 1: Construction / Welding": "topic1_construction_welding.csv",
    "Topic 2: Hotel Laundry":          "topic2_hotel_laundry.csv",
    "Topic 3: Soccer Training":        "topic3_soccer_training.csv",
}

# Model Names
SCORE_MODEL = "qwen-max"                    # Phase 2: Memory Scoring
CHAT_MODEL = "qwen3.5-flash"                # Phase 5: Response Generation
REFLECTION_QUESTION_MODEL = "qwen3.5-flash" # Phase 6: Reflection Questions
REFLECTION_SYNTHESIS_MODEL = "qwen-max"     # Phase 6: Reflection Synthesis
EMBEDDING_MODEL = "text-embedding-v3"       # Phase 6: Embeddings, Vector Search

# Pipeline Configuration
DEFAULT_CONTEXT_WINDOW = 6000
DEFAULT_SYSTEM_PROMPT_TOKENS = 1500
DEFAULT_SCORE_THRESHOLD = 2.0
DEFAULT_TIME_GAP_THRESHOLD = 5
DEFAULT_REFLECTION_INTERVAL = 16

# UI Configuration
APP_TITLE = "Minder AI: Factory Floor Agent"
APP_ICON = "🏭"
