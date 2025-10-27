# 🧪 YouTube RAG Assistant - Testing Guide

This guide will help you test the YouTube transcript fetching and FAISS indexing functionality step by step.

## 📋 Prerequisites

### 1. Install Ollama and Pull Model
```bash
# Install Ollama from https://ollama.ai/
# Then pull the embedding model:
ollama pull nomic-embed-text

# Start Ollama service:
ollama serve
```

### 2. Install Python Dependencies
```bash
# Install dependencies
uv pip install -e .

# Or with pip:
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=DEBUG
```

## 🧪 Testing Steps

### Step 1: Test Transcript Fetching Only
```bash
python test_transcript.py
```

This will:
- ✅ Test YouTube transcript API connection
- ✅ Fetch transcript for a test video
- ✅ Group segments into complete sentences
- ✅ Show detailed DEBUG logs with timestamps and text
- ❌ Skip embeddings (no Ollama required)

**Expected Output:**
```
🧪 TESTING TRANSCRIPT FETCHING FOR: dQw4w9WgXcQ
📝 Fetching transcript...
✅ Fetched 45 segments
📄 First 5 segments:
  1. [0:00] We're no strangers to love
  2. [0:03] You know the rules and so do I
  3. [0:06] A full commitment's what I'm thinking of
  ...
🔄 Grouping into complete sentences...
✅ Created 12 complete sentence chunks
📦 First 3 chunks:
  1. [0:00-0:15] We're no strangers to love You know the rules and so do I...
  2. [0:15-0:30] A full commitment's what I'm thinking of You wouldn't get this from any other guy...
  ...
🎉 TRANSCRIPT TEST COMPLETED SUCCESSFULLY!
```

### Step 2: Test Complete Pipeline (with Ollama)
```bash
python test_youtube.py
```

This will:
- ✅ Test transcript fetching
- ✅ Test chunking
- ✅ Test Ollama embedding generation
- ✅ Test FAISS indexing
- ✅ Test semantic search
- ✅ Show comprehensive DEBUG logs

**Expected Output:**
```
🧪 TESTING YOUTUBE INDEXING FOR VIDEO: dQw4w9WgXcQ
🔍 STEP 1: Testing video ID extraction...
✅ Video ID extracted: dQw4w9WgXcQ
📝 STEP 2: Testing transcript fetching...
✅ Transcript fetched: 45 segments
🔄 STEP 3: Testing transcript chunking...
✅ Transcript chunked: 12 complete sentence chunks
🔮 STEP 4: Testing embedding generation...
✅ Embedding generated: dimension 768
🗄️ STEP 5: Testing FAISS indexing...
✅ Added 3 chunks to FAISS index
🔍 STEP 6: Testing FAISS search...
✅ Search completed: 2 results
🎉 ALL TESTS PASSED SUCCESSFULLY!
```

### Step 3: Test Flask Server
```bash
# Start the server
python server.py
```

In another terminal, test the API:
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test indexing endpoint
curl -X POST http://localhost:5000/api/index_youtube \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ"}'
```

## 🔍 Debug Information

### Log Files
- **Console**: Real-time DEBUG logs with emojis
- **File**: `youtube_rag_debug.log` - Complete log file
- **Test logs**: Detailed output from test scripts

### Key Debug Points

#### 1. Transcript Fetching
Look for these log entries:
```
🎬 Fetching transcript for video: dQw4w9WgXcQ
🌐 Trying languages: ['en']
✅ Successfully fetched 45 transcript segments
📝 COMPLETE TRANSCRIPT DATA:
Segment   1: [   0.0s] We're no strangers to love
Segment   2: [   3.0s] You know the rules and so do I
...
```

#### 2. Chunking Process
Look for these log entries:
```
🔄 Grouping 45 segments into complete sentences
📏 Max duration: 30.0s, Max chars: 500
📦 Created chunk 1: [0.0s-15.0s] We're no strangers to love You know the rules...
📦 Created chunk 2: [15.0s-30.0s] A full commitment's what I'm thinking of...
✅ Grouped 45 segments into 12 complete chunks
📦 ALL GROUPED CHUNKS:
Chunk   1: [   0.0s-  15.0s] We're no strangers to love You know the rules and so do I...
```

#### 3. Embedding Generation
Look for these log entries:
```
🔮 Getting embedding for text: 'We're no strangers to love You know the rules...' (model: nomic-embed-text)
✅ Got embedding with dimension: 768
📊 Embedding stats: min=-0.1234, max=0.5678, mean=0.0123
```

#### 4. FAISS Indexing
Look for these log entries:
```
🗄️ STEP 4: Adding chunks to FAISS vector store...
📊 Embeddings array shape: (12, 768)
✅ Added 12 chunks to FAISS index
📊 Final index stats: {'total_chunks': 12, 'unique_videos': 1, 'video_ids': ['dQw4w9WgXcQ']}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Failed to fetch transcript"
- **Cause**: Video has no English captions
- **Solution**: Try a different video with captions
- **Test videos**: `dQw4w9WgXcQ`, `jNQXAC9IVRw`

#### 2. "Cannot connect to Ollama"
- **Cause**: Ollama not running
- **Solution**: Run `ollama serve`
- **Check**: `curl http://localhost:11434/api/tags`

#### 3. "No transcript chunks generated"
- **Cause**: Empty transcript or chunking error
- **Solution**: Check transcript content in logs

#### 4. "Failed to generate embeddings"
- **Cause**: Ollama model not installed
- **Solution**: Run `ollama pull nomic-embed-text`

### Debug Commands

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check if model is available
ollama list

# Test Ollama embedding directly
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

## 📊 Expected Results

### Successful Test Results
- ✅ Transcript fetched: 20-100 segments (varies by video)
- ✅ Chunks created: 5-30 complete sentences (varies by video)
- ✅ Embeddings: 768 dimensions each
- ✅ FAISS index: All chunks indexed successfully
- ✅ Search: Relevant results returned

### Performance Benchmarks
- **Transcript fetching**: 1-3 seconds
- **Chunking**: <1 second
- **Embedding generation**: 0.5-2 seconds per chunk
- **FAISS indexing**: <1 second
- **Total indexing time**: 10-60 seconds (depends on video length)

## 🎯 Next Steps

After successful testing:
1. ✅ Transcript fetching works
2. ✅ Chunking creates complete sentences
3. ✅ Embeddings generated successfully
4. ✅ FAISS indexing works
5. ✅ Ready for Chrome extension testing

The system is now ready for full YouTube RAG functionality!
