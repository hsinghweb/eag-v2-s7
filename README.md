# YouTube Transcript RAG Assistant 🎥

A Chrome Extension + Flask backend project that helps you understand YouTube videos better by letting you ask questions about any video you're watching using **RAG (Retrieval-Augmented Generation)** with local embeddings.

---

## ✨ Features

### 🎯 Core Capabilities
- **📹 Video Indexing**: One-click indexing of YouTube video transcripts
- **✅ Auto-Detection**: Automatically detects if the current video is already indexed
- **🎯 Focused Search**: Option to restrict questions to the current video only (faster searches)
- **🔍 Semantic Search**: Find relevant content using meaning, not just keywords
- **💬 Smart Q&A**: Ask questions and get answers with exact timestamp references
- **🔗 Direct Links**: Click to jump directly to the relevant part of the video (opens in same tab)
- **🏠 Runs Locally**: Privacy-first with local Ollama embeddings
- **📝 Full Sentences**: Intelligent transcript chunking with complete statements
- **🚀 Fast & Accurate**: FAISS vector search + Google Gemini answers

---

## 💡 How It Works

### The Flow

1. **Watch** a YouTube video
2. **Click** "Index This Video" in the Chrome extension
3. **Backend** fetches transcript → chunks into full sentences → embeds with Nomic → stores in FAISS
4. **Extension automatically detects** if the video is indexed (shows ✓ Indexed badge)
5. **Ask** any question about the video (optionally restrict to current video only)
6. **Get** a detailed answer + YouTube links with timestamps
7. **Click** the timestamp link to jump right to that part of the video (opens in same tab)

### The Tech Stack

```
Chrome Extension
    ↓
Flask Server (Python)
    ↓
YouTube Transcript API → Fetch transcripts
    ↓
Ollama (nomic-embed-text) → Generate embeddings (768-dim vectors)
    ↓
FAISS Vector Database → Semantic search
    ↓
Google Gemini 2.0 → Generate answers with context
    ↓
Return: Answer + YouTube timestamp links
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.12+**
2. **Ollama** with `nomic-embed-text` model
3. **Google Gemini API key**
4. **Google Chrome** browser

### 1. Install Ollama & Pull Model

```bash
# Install Ollama from https://ollama.ai/

# Pull the nomic embedding model
ollama pull nomic-embed-text

# Start Ollama service
ollama serve
```

### 2. Clone & Setup Project

```bash
# Clone repository
git clone [your-repository-url]
cd eag-v2-s7

# Create virtual environment (recommended: use uv)
uv venv
uv pip install -e .

# Or use standard venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# Required: Get your API key from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

### 4. Start the Flask Server

```bash
python server.py
```

The server will start on `http://localhost:5000`

### 5. Install Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **"Load unpacked"**
4. Select the `chrome-extension` directory from this project
5. The YouTube RAG Assistant icon should appear in your extensions toolbar

---

## 📖 Usage Guide

### Indexing a Video

1. Navigate to any YouTube video (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
2. Click the **YouTube RAG Assistant** icon in your toolbar
3. You'll see the video ID detected
4. Click **"Index This Video"**
5. Wait for confirmation (usually 10-30 seconds depending on video length)
6. Once indexed, you'll see a **✓ Indexed** badge next to the video ID

### Asking Questions

Once a video is indexed, you can ask questions like:

```
What is the main topic of this video?

Explain the concept mentioned at 2:30

What are the key takeaways?

How does the speaker define [specific term]?

Summarize the conclusion
```

**New Features:**

- **Auto-Detection**: If you're on a video that's already indexed, the extension automatically shows a **✓ Indexed** badge
- **Restrict to Current Video**: When viewing an indexed video, you'll see a checkbox option "Search only in current video". Check this to:
  - Get faster search results (searches only one video instead of all)
  - Focus answers on the specific video you're watching
  - Perfect for when you have many videos indexed but want to ask about just one
- **Same-Tab Navigation**: Clicking timestamp links now opens them in the same tab, making it feel like you're asking YouTube and quickly jumping to the answer

The assistant will:
- Search through all indexed videos (or just the current video if restricted)
- Find the most relevant transcript chunks
- Generate a detailed answer using Gemini
- Provide timestamp links to the exact moments in the video

---

## 🏗️ Project Structure

```
eag-v2-s7/
├── agent/                          # Cognitive architecture modules
│   ├── __init__.py                 # Module exports
│   ├── ai_agent.py                 # Cognitive agent orchestrator
│   ├── memory.py                   # FAISS vector store for YouTube transcripts
│   ├── models.py                   # Pydantic models for YouTube RAG
│   ├── perception.py                # Perception layer (cognitive layer)
│   ├── decision.py                 # Decision layer (cognitive layer)
│   ├── action.py                   # Action layer (cognitive layer)
│   └── prompts.py                  # Cognitive layer prompts
│
├── tools/                          # Tools and utilities
│   ├── __init__.py                 # Module exports
│   └── tools_youtube.py            # YouTube transcript fetching, chunking, embedding
│
├── chrome-extension/               # Chrome extension frontend
│   ├── manifest.json               # Extension configuration
│   ├── content.js                  # Detects YouTube videos
│   ├── popup.html                  # Extension UI
│   ├── popup.js                    # Extension logic
│   └── images/                     # Extension icons
│       ├── icon16.png              # 16x16 icon
│       ├── icon48.png              # 48x48 icon
│       └── icon128.png             # 128x128 icon
│
├── logs/                           # Generated at runtime
│   ├── youtube_memory.json         # Memory state
│   ├── youtube_faiss.index         # FAISS vector index
│   ├── youtube_metadata.pkl        # Video chunk metadata
│   └── cognitive_agent_*.log        # Cognitive agent logs
│
├── server.py                       # Flask API server
├── pyproject.toml                  # Project dependencies and configuration
├── uv.lock                         # Dependency lock file (uv package manager)
└── README.md                       # This file
```

---

## 🔧 Technical Details

### Transcript Chunking Strategy

The system groups transcript segments into **full sentences** using:
- **Punctuation detection**: Groups end when encountering `.`, `!`, or `?`
- **Max duration**: 30 seconds per chunk
- **Max characters**: 500 characters per chunk

This ensures coherent, complete statements rather than fragments.

**Example**:
```
❌ Bad: "The concept of artificial intelligence is"
✅ Good: "The concept of artificial intelligence is fascinating because it allows machines to learn from data."
```

### Embedding Model

- **Model**: `nomic-embed-text` (768 dimensions)
- **Provider**: Ollama (runs locally)
- **Why**: Privacy-first, no data sent to external APIs for embeddings

### Vector Search

- **Engine**: FAISS (Facebook AI Similarity Search)
- **Index Type**: IndexFlatL2 (exact L2 distance search)
- **Similarity**: Converts L2 distance to similarity score: `1 / (1 + distance)`

### Answer Generation

- **Model**: Google Gemini 2.0 Flash Exp
- **Architecture**: Cognitive layers (Perception → Decision → Action)
- **Context**: Top relevant chunks from FAISS search (with surrounding context expansion)
- **Prompt**: Includes transcript context + user question processed through cognitive layers

---

## 📊 API Endpoints

### `POST /api/index_youtube`

Index a YouTube video (asynchronous).

**Request**:
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

**Response**:
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

**Response**:
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "status": "completed",
  "progress": 100,
  "total_chunks": 42,
  "message": "Successfully indexed 42 chunks",
  "start_time": "2025-01-27T20:15:00",
  "end_time": "2025-01-27T20:18:00"
}
```

### `GET /api/video_indexed/<video_id>`

Check if a specific video is indexed.

**Response**:
```json
{
  "indexed": true,
  "video_id": "dQw4w9WgXcQ",
  "chunk_count": 42
}
```

### `POST /api/ask_youtube`

Ask a question about indexed videos using cognitive layers.

**Request**:
```json
{
  "question": "What is the main topic?",
  "video_id": "dQw4w9WgXcQ"
}
```

The `video_id` parameter is **optional**. If provided:
- Search will be restricted to only the specified video
- Faster search performance
- Useful when you want to focus on a specific video

**Request (search all videos)**:
```json
{
  "question": "What is the main topic?"
}
```

**Response**:
```json
{
  "success": true,
  "question": "What is the main topic?",
  "answer": "The video discusses...",
  "contexts": [
    {
      "video_id": "dQw4w9WgXcQ",
      "chunk_text": "...",
      "timestamp": 45.2,
      "relevance_score": 0.95
    }
  ],
  "youtube_links": [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=45s"
  ],
  "cognitive_analysis": {
    "perception": {...},
    "decision": {...},
    "action": {...}
  }
}
```

### `GET /health`

Check server status.

**Response**:
```json
{
  "status": "healthy",
  "youtube_index": {
    "total_chunks": 150,
    "unique_videos": 3,
    "video_ids": ["dQw4w9WgXcQ", "..."]
  }
}
```

---

## 🐛 Troubleshooting

### "Failed to connect to server"
- Ensure Flask server is running: `python server.py`
- Check server is on port 5000: `http://localhost:5000/health`

### "Ollama is not running"
- Start Ollama: `ollama serve`
- Verify model is installed: `ollama list` (should show `nomic-embed-text`)

### "Failed to fetch transcript"
- Video might not have English captions
- Try a different video with available transcripts
- Check YouTube video is publicly accessible

### "No YouTube content indexed yet"
- You need to index at least one video first
- Click "Index This Video" on any YouTube video page

### Extension not detecting video
- Refresh the YouTube page
- Check you're on a `/watch?v=` URL (not homepage or search)
- Reload the extension in `chrome://extensions/`

---

## 🎯 Example Queries

### Educational Videos
```
"Explain the three main principles discussed"
"What example does the speaker give at 5:30?"
"Summarize the conclusion"
```

### Tutorial Videos
```
"What are the steps to set this up?"
"What command is used at 3:15?"
"What are the prerequisites mentioned?"
```

### Lecture Videos
```
"Define [specific term] as explained in this video"
"What are the key differences between X and Y?"
"What evidence is provided for this claim?"
```

---

## 📈 Statistics

| Metric | Value |
|--------|-------|
| **Embedding Model** | nomic-embed-text |
| **Vector Dimension** | 768 |
| **LLM** | Google Gemini 2.0 Flash Exp |
| **Chunking Strategy** | Full sentences (30s / 500 chars max) |
| **Vector Store** | FAISS IndexFlatL2 |
| **Privacy** | Local embeddings (Ollama) |
| **Average Index Time** | 15-30 seconds per video |

---

## 🚧 Future Enhancements

- [ ] Support for multiple languages
- [ ] Video thumbnail display
- [ ] Conversation history
- [ ] Export Q&A to notes
- [ ] Batch video indexing
- [ ] Video content summarization
- [ ] Highlight keywords in chunks
- [ ] Dark mode for extension

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **Google Gemini** for powerful LLM capabilities
- **Ollama** for local embedding models
- **FAISS** for efficient vector search
- **YouTube Transcript API** for easy transcript access
- **FastMCP** for tool orchestration patterns

---

## 📚 Learn More

- [YouTube Transcript API Documentation](https://github.com/jdepoix/youtube-transcript-api)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Google Gemini API](https://ai.google.dev/)

---

**Built with ❤️ for better YouTube learning**

**Version**: 1.1  
**Last Updated**: January 2025  
**Status**: ✅ Production Ready

### What's New in v1.1

- ✨ **Auto-Detection**: Automatically detects if current video is indexed
- 🎯 **Focused Search**: Option to restrict questions to current video only
- 🔗 **Same-Tab Links**: Timestamp links now open in the same tab for seamless navigation
