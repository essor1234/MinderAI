Minder AI: Generative Agent Pipeline & Demo Architecture

1. Project Overview & Purpose
   We are building a text-simulated prototype for Minder AI, a voice-first co-worker agent designed to live inside factory systems. The core objective of this agent is to safely acquire, verify, and document unwritten tribal knowledge from factory workers (e.g., knowing a specific machine overheats on Tuesdays and needs a 5% current drop)
   .
   This is not a standard RAG chatbot. The system must solve three core problems:
   Knowledge Acquisition: Turn raw conversational data into structured, retrievable knowledge
   .
   Consistency & Integration: Reconcile contradictions and filter out noise/jokes to prevent system poisoning
   .
   Feedback Loop: Prove the agent learns by using integrated knowledge to proactively improve future conversations
   .
   Project Location: All code must be contained within a new directory named MinderAI_demo to prevent interference with existing Jupyter Notebook experiments.
2. UI Design (The Streamlit Web App)
   The web interface is built using Streamlit and divided into a two-column layout with an added configuration sidebar:
   Sidebar (Pipeline Switcher): A dropdown menu allowing the developer to seamlessly swap between different pipeline implementations (e.g., "Baseline Pipeline", "GraphRAG Pipeline"). This is crucial for A/B testing and comparing different architectural approaches at this early stage.
   Left Column (The Factory Floor): A standard chat interface (st.chat_message and st.chat_input). The user types here to simulate a worker speaking to the agent.
   Right Column (The Agent's Brain): A live-updating debug panel that displays the internal pipeline results after every chat:
   Phase 4 Context: The exact top-filtered memories selected.
   Phase 6 Reflections: New operational rules synthesized post-response.
   Phase 7 Plans: Proactive conversational plans generated post-response.
3. The 7-Phase Execution Flow
   The system processes data in 7 distinct phases. Phases 1 through 5 run synchronously to generate the immediate answer for the user. Phases 6 and 7 run concurrently (in parallel) in the background after the response is delivered, saving overall processing time.
   Synchronous Flow (Immediate User Response):
   Phase 1: Parse & Group Memories: Reads the raw file/input and groups exchanges into memories.
   Phase 2: Score Memories: Sends memory chunks to the qwen-max model to rate Recency, Importance, Relevance, and Experience.
   Phase 3: Normalize & Filter: Converts scores to normalized values and mathematically filters out low-value memories (noise).
   Phase 4: Context Selection: Picks the top filtered memories that fit the context window to prepare the final prompt.
   Phase 5: Response Generation: Builds the final prompt using the selected memories and the worker input, calling the qwen3.5-flash model to generate the agent's reply. The user receives their answer here.
   Asynchronous Flow (Post-Response Analysis):
   Phase 6: Reflection (Concurrent with 7): Generates reflection questions using qwen3.5-flash
   , retrieves related records using text-embedding-v3
   , and synthesizes high-level insights using qwen-max
   .
   Phase 7: Planning (Concurrent with 6): Scans the input for anomaly keywords (e.g., "overheat", "issue")
   and generates proactive conversational plans based on the new reflection and issue recurrence.
4. OOP Architecture & Model Organization
   The code must be built using Object-Oriented Programming (OOP) and the Strategy Pattern to allow the UI to switch between different pipelines.
   BasePipeline (Abstract Class): Defines the required run_synchronous_phases and run_asynchronous_phases methods.
   MemoryStream Class: Manages the LocalVectorStore and .jsonl databases.
   MemoryProcessor Class (Phases 1-4): Encapsulates the parsing, scoring (qwen-max), normalizing, and context selection.
   AgentResponder Class (Phase 5): Handles prompt building and response generation (qwen3.5-flash).
   Reflector Class (Phase 6): Encapsulates the reflection trigger logic and the three-step synthesis using the specific models designated for this phase.
   Planner Class (Phase 7): Encapsulates the planning trigger logic and plan generation
   .
   To ensure flexibility, all models (qwen-max, qwen3.5-flash, text-embedding-v3) must be defined as class attributes or passed during initialization so they can be easily swapped or updated in future pipeline versions.
