# Tech Stack Slide

## 🛠️ YouTube RAG Assistant - Technology Stack

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

