# Minder AI: Streamlit Demo

A voice-first co-worker agent designed to safely acquire, verify, and document unwritten tribal knowledge from factory workers.

## Project Structure

```
MinderAI_demo/
├── app.py                          # Main Streamlit entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── config/                         # Configuration & Constants
│   ├── __init__.py
│   └── settings.py                 # API keys, default values, model names
│
├── utils/                          # Utility Functions
│   ├── __init__.py
│   └── helpers.py                  # Token estimation, cosine similarity
│
├── memory/                         # Memory Management
│   ├── __init__.py
│   ├── vector_store.py             # LocalVectorStore class
│   └── stream.py                   # MemoryStream class (Phase 1: Parse & Group)
│
├── processors/                     # Processing Pipeline Phases
│   ├── __init__.py
│   ├── memory_processor.py         # Phases 1-4: Parse, Score, Normalize, Select
│   ├── agent_responder.py          # Phase 5: Response Generation
│   ├── reflector.py                # Phase 6: Reflection & Insights
│   └── planner.py                  # Phase 7: Proactive Planning
│
├── pipeline/                       # Pipeline Architecture
│   ├── __init__.py
│   ├── base.py                     # BasePipeline abstract class
│   └── default.py                  # DefaultPipeline implementation
│
└── ui/                             # Streamlit UI Components
    ├── __init__.py
    ├── utils.py                    # Session state management
    ├── sidebar.py                  # Configuration sidebar
    ├── factory_floor.py            # Left column (chat interface)
    └── agents_brain.py             # Right column (debug panel)
```

## OOP Architecture

### Strategy Pattern

- **BasePipeline** (abstract): Defines pipeline interface
- **DefaultPipeline** (concrete): Implements the 7-phase execution flow
- Future: Easy to add new pipeline variants (e.g., GraphRAGPipeline)

### Modular Classes

- **MemoryStream**: Parses conversation files and groups into memories
- **LocalVectorStore**: In-memory embeddings with cosine similarity search
- **MemoryProcessor**: Phases 1-4 (parse, score, normalize, select)
- **AgentResponder**: Phase 5 (prompt building and response generation)
- **Reflector**: Phase 6 (reflection questions and synthesis)
- **Planner**: Phase 7 (proactive plan generation)

## 7-Phase Execution Flow

### Synchronous (Immediate Response)

1. **Phase 1**: Parse & Group Memories (MemoryStream)
2. **Phase 2**: Score Memories (MemoryProcessor using qwen-max)
3. **Phase 3**: Normalize & Filter (MemoryProcessor)
4. **Phase 4**: Context Selection (MemoryProcessor)
5. **Phase 5**: Response Generation (AgentResponder using qwen3.5-flash)

### Asynchronous (Background)

6. **Phase 6**: Reflection (Reflector using qwen3.5-flash, text-embedding-v3, qwen-max)
7. **Phase 7**: Planning (Planner using qwen-max)

## Configuration

### Models

- **Scoring Model** (Phase 2): `qwen-max`
- **Chat Model** (Phase 5): `qwen3.5-flash`
- **Reflection Question Model** (Phase 6): `qwen3.5-flash`
- **Reflection Synthesis Model** (Phase 6): `qwen-max`
- **Embedding Model** (Phase 6): `text-embedding-v3`

All models are configurable via `config/settings.py` or the Streamlit UI sidebar.

### Scoring System

- **Recency**: How recent is the memory?
- **Importance**: How critical is this operational knowledge?
- **Relevance**: How closely does it relate to the worker's question?
- ~~**Experience**~~: Removed (we don't know identities in conversations)

## Running the Demo

### Install Dependencies

```bash
cd MinderAI_demo
pip install -r requirements.txt
```

### Set Environment Variables

Create a `.env` file in the workspace root:

```
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_API_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

### Run Streamlit App

```bash
streamlit run MinderAI_demo/app.py
```

## UI Layout

- **Sidebar**: Pipeline selector, memory file path, model configuration
- **Left Column (Factory Floor)**: Chat interface with worker input and agent responses
- **Right Column (Agent's Brain)**: Debug panel with three tabs:
  - **📌 Memories**: Selected memories from Phase 4 with normalized scores
  - **🔍 Reflections**: Reflections generated in Phase 6
  - **📋 Plans**: Proactive plans generated in Phase 7

## How to Extend

### Adding a New Pipeline

1. Create a new class inheriting from `BasePipeline` in `pipeline/`
2. Implement `run_synchronous_phases()` and `run_asynchronous_phases()`
3. Add to `get_available_pipelines()` in `ui/sidebar.py`

### Swapping Models

Edit `config/settings.py` to change default models, or use the UI sidebar to swap models per pipeline.

### Custom Processors

1. Create a new processor class (e.g., `CustomReflector`) in `processors/`
2. Inherit from existing processor or define new logic
3. Compose into pipeline class

## Data Files

- **Memory Source**: `data/topic1_construction_welding.txt`
- **Vector Store**: `data/vector_memories.jsonl` (persisted embeddings)
- **Reflections**: `data/reflections.jsonl` (stored reflections)

## License

Internal project for Minder AI demonstration.
