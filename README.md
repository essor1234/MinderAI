# MinderAI Demo

A demo application replicating the memory pipeline from the Stanford research paper on generative agents, applied to the capture and verification of unwritten operational knowledge from workers.

> **Research Paper:** https://doi.org/10.1145/3586183.3606763

---

## Part 1 — How This Demo Works

### Overview

MinderAI is a co-worker agent that acquires, verifies, and documents tribal knowledge from daily workplace conversations. It replicates the memory pipeline described in the Stanford research, adapted for industrial and operational settings where unwritten know-how lives only in the heads of experienced workers.

### Pipeline Structure

<img width="600" alt="MinderAI Pipeline" src="https://github.com/user-attachments/assets/1809cb34-f9fc-4abb-86e9-3830a2671a61" />
_

The pipeline runs in 7 phases each time the user sends a message:

| Phase | Name                | What it does                                                                                 |
| ----- | ------------------- | -------------------------------------------------------------------------------------------- |
| 1     | Parse & Group       | Reads the conversation dataset and groups messages by time gap                               |
| 2     | Score               | Scores each memory on recency, importance, and relevance                                     |
| 3     | Normalize & Filter  | Applies mathematical thresholding to remove low-signal memories                              |
| 4     | Context Selection   | Selects the highest-ranked memories that fit the token window                                |
| 5     | Response Generation | Generates the agent's reply using only the selected memories                                 |
| 6     | Reflection          | Runs in the background — forms questions, searches for related records, synthesizes insights |
| 7     | Planning            | Runs in the background — detects issues and prepares proactive questions for future turns    |

### Key Capabilities

**Consistency of information across conversations**
The agent does not treat each message in isolation. It scores and retrieves memories from the full conversation history, so facts introduced early in a dialogue are carried forward and reconciled with later statements. Contradictions are surfaced and resolved rather than silently overwritten.

**Proactive questioning through planning**
After each response, the agent runs a planning phase that scans the conversation for unresolved issues or knowledge gaps. It builds a set of proactive questions ready to raise in future turns, so the agent drives the knowledge-capture process rather than just reacting to what the user says.

**Noise and false data removal**
The scoring pipeline is designed to distinguish factual operational information from jokes, venting, and off-topic remarks. Low-relevance and low-importance messages are filtered out before the context is assembled, preventing noise from polluting the agent's knowledge base or its responses.

---

> **Notice:** This is a demo application. Voice input is not yet supported — all interaction happens through the text chat interface.

---

## Part 2 — Clone, Download, and Run

### Prerequisites

- Python 3.10 or higher
- A [DashScope API key](https://dashscope.aliyuncs.com) (Alibaba's LLM service)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/MinderAI.git
cd MinderAI
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r MinderAI_demo/requirements.txt
```

### 4. Configure your API key

Create a `.env` file at the project root:

```
DASHSCOPE_API_KEY=your_api_key_here
```

### 5. Run the app

```bash
streamlit run MinderAI_demo/app.py
```

The app opens in your browser at `http://localhost:8501`.

### 6. Using the demo

1. **Select a dataset** from the sidebar — three pre-loaded topics are available (construction/welding, hotel laundry, soccer training), or provide a path to your own CSV file.
2. **Ask a question** in the chat panel on the left.
3. **Inspect the agent's reasoning** in the "Agent's Brain" panel on the right — it shows which memories were selected, what reflections were generated, and what proactive plans are queued.
