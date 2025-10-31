# Architecture Slide

## 🏗️ YouTube RAG Assistant - System Architecture

### System Flow
```
┌─────────────────┐
│ Chrome Extension │
│  (Frontend UI)   │
└────────┬────────┘
         │ HTTP API
         ▼
┌─────────────────┐
│  Flask Server    │ ◄── REST API Endpoints
│  (Python)       │     /api/index_youtube
└────────┬────────┘     /api/ask_youtube
         │              /health
         ├─────────────────┬─────────────────┐
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   YouTube    │  │    Ollama    │  │    FAISS     │
│ Transcript   │  │  Embeddings  │  │  Vector DB   │
│     API      │  │ (nomic-embed) │  │   (Index)    │
└──────────────┘  └──────────────┘  └──────────────┘
                                      
                                      ┌──────────────┐
                                      │   Google     │
                                      │   Gemini     │
                                      │  2.0 Flash   │
                                      │   (LLM)      │
                                      └──────────────┘
```

### Cognitive Architecture Layers

**Multi-Layer Cognitive Processing:**
```
┌─────────────────────────────────────────┐
│         Cognitive Agent                 │
│                                         │
│  ┌──────────┐  ┌──────────┐          │
│  │Perception│→ │ Decision  │          │
│  │  Layer   │  │  Layer    │          │
│  └────┬─────┘  └─────┬─────┘          │
│       │              │                 │
│       └──────┬───────┘                 │
│              ▼                         │
│       ┌──────────┐                    │
│       │  Action  │                    │
│       │  Layer   │                    │
│       └────┬────┘                    │
│            │                          │
└────────────┼─────────────────────────┘
             │
             ▼
      ┌──────────────┐
      │ Memory Layer │
      │  (FAISS)     │
      └──────────────┘
```

### Data Processing Pipeline

**1. Indexing Flow:**
```
Video URL
    ↓
Extract Video ID
    ↓
Fetch Transcript (YouTube API)
    ↓
Chunk into Full Sentences
    ↓
Generate Embeddings (Ollama)
    ↓
Store in FAISS Index
    ↓
Save Metadata
```

**2. Query Flow:**
```
User Question
    ↓
Generate Query Embedding
    ↓
FAISS Semantic Search
    ↓
Retrieve Top Contexts
    ↓
Expand with Surrounding Chunks
    ↓
Cognitive Layers Processing
  • Perception → Understand context
  • Decision → Choose best response
  • Action → Generate answer
    ↓
Return Answer + Timestamps
```

### Key Components

**Agent Module:**
- `ai_agent.py` - Orchestrates cognitive layers
- `memory.py` - FAISS vector store management
- `perception.py` - Context understanding
- `decision.py` - Response planning
- `action.py` - Answer generation

**Tools Module:**
- `tools_youtube.py` - Transcript processing & embeddings

**Frontend:**
- Chrome Extension - User interface
- Content scripts - Video detection
- Popup UI - Interaction layer

**Backend:**
- Flask API Server - REST endpoints
- Asynchronous indexing - Background processing
- Status tracking - Progress monitoring

