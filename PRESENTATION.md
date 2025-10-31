# YouTube Video RAG Agent - Presentation

---

## 📋 Project Overview

### Project Idea: YouTube Video RAG Agent

**Concept:**
Build an AI system that indexes YouTube video transcriptions with timestamps for efficient retrieval and question-answering.

**Key Value Proposition:**
- One-click video indexing from Chrome extension
- Semantic search through video content
- AI-powered Q&A with exact timestamp references
- Privacy-first with local embeddings

---

## 🔄 Workflow

### Indexing Process
1. **Extract and Index**: Extract transcriptions of YouTube videos with precise timestamps
2. **Chunk Creation**: Group transcript segments into complete sentences
3. **Embedding Generation**: Create vector embeddings for semantic search
4. **Storage**: Store embeddings in FAISS vector database with metadata

### Question-Answering Process
1. **Question Input**: User asks a question related to any indexed video
2. **Retrieval**: System retrieves the Top-3 most relevant chunks from the indexed data
3. **Context Expansion**: Expand retrieved chunks with surrounding context
4. **Response Generation**: Send chunks along with question through cognitive layers to LLM
5. **Result Display**: Show the final answer with clickable YouTube links pointing to exact timestamps

---

## 🏗️ System Architecture

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
         │              /api/indexing_status/<video_id>
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

**Cognitive Layers Purpose:**
- **Perception Layer**: Understand context and extract key information
- **Decision Layer**: Choose best response strategy
- **Action Layer**: Generate comprehensive answer
- **Memory Layer**: Store and retrieve relevant video chunks

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
Save Metadata with Timestamps
```

**2. Query Flow:**
```
User Question
    ↓
Generate Query Embedding
    ↓
FAISS Semantic Search
    ↓
Retrieve Top-3 Contexts
    ↓
Expand with Surrounding Chunks
    ↓
Cognitive Layers Processing
  • Perception → Understand context
  • Decision → Choose best response
  • Action → Generate answer
    ↓
Return Answer + Timestamp Links
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

---

## 🛠️ Technology Stack

### Frontend Technologies
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Browser Extension** | Chrome Extension API | User interface & interaction |
| **UI** | HTML5, JavaScript | Popup interface & content scripts |
| **Styling** | CSS3 | Extension UI design |

### Backend Technologies
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Flask | 2.0.1+ | REST API server |
| **CORS** | Flask-CORS | 3.0.10+ | Cross-origin requests |
| **Language** | Python | 3.12+ | Core backend |

### AI & ML Technologies
| Component | Technology | Details | Purpose |
|-----------|-----------|---------|---------|
| **Embedding Model** | Ollama (nomic-embed-text) | 768 dimensions | Local text embeddings |
| **Vector Database** | FAISS | IndexFlatL2 | Semantic similarity search |
| **LLM** | Google Gemini | 2.0 Flash Exp | Answer generation |
| **Architecture** | Cognitive Layers | 4-layer system | Structured AI processing |

### Data Processing
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Transcript API** | youtube-transcript-api | Fetch video captions |
| **Data Models** | Pydantic | Type-safe data structures |
| **Numerical Computing** | NumPy | Vector operations |

### Infrastructure & Tools
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Package Manager** | UV | Fast Python package management |
| **Environment Config** | python-dotenv | Configuration management |
| **HTTP Client** | requests | API communication |
| **Logging** | Python logging | Debug & monitoring |

### Cognitive Architecture Stack
```
┌─────────────────────────────────────┐
│     Cognitive Agent Framework       │
├─────────────────────────────────────┤
│ • Perception Layer                   │
│ • Decision Layer                     │
│ • Action Layer                       │
│ • Memory Layer (FAISS)               │
└─────────────────────────────────────┘
```

### Technology Highlights

**🔒 Privacy-First:**
- Local embeddings (Ollama)
- No transcript data sent to external APIs for embeddings
- Only final queries sent to Gemini

**⚡ Performance:**
- FAISS for fast vector search
- Async indexing for non-blocking operations
- Efficient chunking strategy (30s/500 chars)

**🧠 AI Capabilities:**
- Semantic search (not keyword-based)
- Context-aware responses
- Multi-layer cognitive processing

### Version & Requirements
- **Python**: 3.12+
- **Node.js**: Not required (Chrome extension is pure JS)
- **Ollama**: Latest version with nomic-embed-text model
- **Dependencies**: Managed via pyproject.toml & uv.lock

### API Integration
- **YouTube Transcript API**: Public video captions
- **Ollama API**: Local embedding generation (localhost:11434)
- **Google Gemini API**: Cloud-based LLM inference

---

## 🎯 Key Features

### Core Capabilities
- **📹 Video Indexing**: One-click indexing of YouTube video transcripts
- **🔍 Semantic Search**: Find relevant content using meaning, not just keywords
- **💬 Smart Q&A**: Ask questions and get answers with exact timestamp references
- **🔗 Direct Links**: Click to jump directly to the relevant part of the video
- **🏠 Runs Locally**: Privacy-first with local Ollama embeddings
- **📝 Full Sentences**: Intelligent transcript chunking with complete statements
- **🚀 Fast & Accurate**: FAISS vector search + Google Gemini answers

### Technical Specifications
- **Embedding Model**: nomic-embed-text (768 dimensions)
- **Vector Dimension**: 768
- **LLM**: Google Gemini 2.0 Flash Exp
- **Chunking Strategy**: Full sentences (30s / 500 chars max)
- **Vector Store**: FAISS IndexFlatL2
- **Privacy**: Local embeddings (Ollama)
- **Average Index Time**: 15-30 seconds per video

---

## 📊 API Endpoints

### `POST /api/index_youtube`
Index a YouTube video (asynchronous).

**Request:**
```json
{
  "video_id": "dQw4w9WgXcQ"
}
```
or
```json
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "message": "Indexing started in background",
  "status": "started"
}
```

### `GET /api/indexing_status/<video_id>`
Get the current indexing status for a video.

### `POST /api/ask_youtube`
Ask a question about indexed videos using cognitive layers.

**Request:**
```json
{
  "question": "What is the main topic?"
}
```

**Response:**
```json
{
  "success": true,
  "question": "What is the main topic?",
  "answer": "The video discusses...",
  "contexts": [...],
  "youtube_links": [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=45s"
  ],
  "cognitive_analysis": {...}
}
```

### `GET /health`
Check server status and index statistics.

---

## 💡 Use Cases

**Educational Videos:**
- "Explain the three main principles discussed"
- "What example does the speaker give at 5:30?"
- "Summarize the conclusion"

**Tutorial Videos:**
- "What are the steps to set this up?"
- "What command is used at 3:15?"
- "What are the prerequisites mentioned?"

**Lecture Videos:**
- "Define [specific term] as explained in this video"
- "What are the key differences between X and Y?"
- "What evidence is provided for this claim?"

---

## ✅ Summary

The YouTube Video RAG Agent combines:
- **Efficient Indexing** with precise timestamp tracking
- **Semantic Search** for intelligent content retrieval
- **Cognitive AI Processing** through multi-layer architecture
- **Privacy-First Design** with local embeddings
- **User-Friendly Interface** via Chrome extension

**Result**: A powerful system that makes YouTube videos searchable and question-answerable with direct links to relevant timestamps.

