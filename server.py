"""
Flask Server for YouTube RAG Assistant
Provides API endpoints for indexing YouTube videos and asking questions
"""
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import numpy as np
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import threading
import time
from datetime import datetime

# Import YouTube tools
from server_mcp.tools_youtube import (
    extract_video_id,
    fetch_youtube_transcript,
    group_transcript_segments,
    get_ollama_embedding,
    create_youtube_link
)

# Import models
from agent.models import (
    IndexYouTubeInput,
    IndexYouTubeOutput,
    AskYouTubeInput,
    AskYouTubeOutput,
    YouTubeTranscriptChunk,
    YouTubeContext
)

# Import memory layer
from agent.memory import MemoryLayer

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging with DEBUG level for comprehensive debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('youtube_rag_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize memory layer for YouTube
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
memory_file = os.path.join(log_dir, "youtube_memory.json")
memory_layer = MemoryLayer(memory_file=memory_file, load_existing=True)

# Global indexing status tracking
indexing_status = {}
indexing_lock = threading.Lock()

logger.info("YouTube RAG Assistant server started")
logger.info(f"Memory file: {memory_file}")


def expand_context_with_surrounding_chunks(top_contexts, memory_layer):
    """
    Expand the top matching chunks with their previous and next chunks for better context.
    
    Args:
        top_contexts: List of YouTubeContext objects from FAISS search
        memory_layer: MemoryLayer instance to access chunk metadata
        
    Returns:
        List of YouTubeContext objects including surrounding chunks
    """
    expanded_contexts = []
    processed_chunks = set()  # To avoid duplicates
    
    logger.debug("🔍 Expanding context with surrounding chunks...")
    
    for ctx in top_contexts:
        # Add the original chunk if not already processed
        chunk_key = f"{ctx.video_id}_{ctx.timestamp}"
        if chunk_key not in processed_chunks:
            expanded_contexts.append(ctx)
            processed_chunks.add(chunk_key)
            logger.debug(f"✅ Added original chunk: [{ctx.timestamp:.1f}s] {ctx.chunk_text[:50]}...")
        
        # Find previous and next chunks for this video
        video_chunks = []
        for metadata in memory_layer.youtube_metadata:
            if metadata['video_id'] == ctx.video_id:
                video_chunks.append(metadata)
        
        # Sort chunks by timestamp
        video_chunks.sort(key=lambda x: x['start_timestamp'])
        
        # Find current chunk index
        current_idx = None
        for i, chunk in enumerate(video_chunks):
            if abs(chunk['start_timestamp'] - ctx.timestamp) < 1.0:  # Within 1 second
                current_idx = i
                break
        
        if current_idx is not None:
            # Add previous chunk
            if current_idx > 0:
                prev_chunk = video_chunks[current_idx - 1]
                prev_key = f"{prev_chunk['video_id']}_{prev_chunk['start_timestamp']}"
                if prev_key not in processed_chunks:
                    prev_context = YouTubeContext(
                        video_id=prev_chunk['video_id'],
                        chunk_text=prev_chunk['chunk_text'],
                        timestamp=prev_chunk['start_timestamp'],
                        relevance_score=0.5  # Lower relevance for context chunks
                    )
                    expanded_contexts.append(prev_context)
                    processed_chunks.add(prev_key)
                    logger.debug(f"📝 Added previous chunk: [{prev_chunk['start_timestamp']:.1f}s] {prev_chunk['chunk_text'][:50]}...")
            
            # Add next chunk
            if current_idx < len(video_chunks) - 1:
                next_chunk = video_chunks[current_idx + 1]
                next_key = f"{next_chunk['video_id']}_{next_chunk['start_timestamp']}"
                if next_key not in processed_chunks:
                    next_context = YouTubeContext(
                        video_id=next_chunk['video_id'],
                        chunk_text=next_chunk['chunk_text'],
                        timestamp=next_chunk['start_timestamp'],
                        relevance_score=0.5  # Lower relevance for context chunks
                    )
                    expanded_contexts.append(next_context)
                    processed_chunks.add(next_key)
                    logger.debug(f"📝 Added next chunk: [{next_chunk['start_timestamp']:.1f}s] {next_chunk['chunk_text'][:50]}...")
    
    # Sort expanded contexts by timestamp for better readability
    expanded_contexts.sort(key=lambda x: x.timestamp)
    
    logger.info(f"🔍 Context expansion: {len(top_contexts)} → {len(expanded_contexts)} chunks")
    logger.debug(f"📊 Expanded context includes {len(expanded_contexts)} total chunks")
    
    return expanded_contexts


def index_video_async(video_id: str):
    """
    Asynchronous function to index a YouTube video.
    Updates global indexing_status with progress.
    """
    global indexing_status
    
    try:
        with indexing_lock:
            indexing_status[video_id] = {
                'status': 'started',
                'progress': 0,
                'total_chunks': 0,
                'message': 'Starting transcript fetch...',
                'start_time': datetime.now().isoformat(),
                'error': None
            }
        
        logger.info(f"🚀 Starting async indexing for video: {video_id}")
        
        # Step 1: Fetch transcript
        with indexing_lock:
            indexing_status[video_id]['message'] = 'Fetching transcript...'
        
        transcript = fetch_youtube_transcript(video_id)
        
        # DEBUG: Print complete transcript data with timestamps
        logger.debug("=" * 100)
        logger.debug("📝 COMPLETE YOUTUBE TRANSCRIPT WITH TIMESTAMPS:")
        logger.debug("=" * 100)
        for i, segment in enumerate(transcript):
            timestamp_formatted = f"{int(segment['start']//60):02d}:{int(segment['start']%60):02d}"
            logger.debug(f"Segment {i+1:3d}: [{timestamp_formatted}] {segment['text']}")
        logger.debug("=" * 100)
        logger.debug(f"📊 Total transcript segments: {len(transcript)}")
        logger.debug("=" * 100)
        
        with indexing_lock:
            indexing_status[video_id]['message'] = f'Fetched {len(transcript)} segments, grouping...'
        
        # Step 2: Group into full sentences
        chunks = group_transcript_segments(transcript, max_duration=30, max_chars=500)
        
        # DEBUG: Print all grouped chunks with timestamps
        logger.debug("=" * 100)
        logger.debug("📦 ALL GROUPED CHUNKS WITH TIMESTAMPS:")
        logger.debug("=" * 100)
        for i, chunk in enumerate(chunks):
            start_time = f"{int(chunk['start_timestamp']//60):02d}:{int(chunk['start_timestamp']%60):02d}"
            end_time = f"{int(chunk['end_timestamp']//60):02d}:{int(chunk['end_timestamp']%60):02d}"
            logger.debug(f"Chunk {i+1:3d}: [{start_time}-{end_time}] {chunk['text']}")
        logger.debug("=" * 100)
        logger.debug(f"📊 Total chunks created: {len(chunks)}")
        logger.debug("=" * 100)
        
        if not chunks:
            with indexing_lock:
                indexing_status[video_id] = {
                    'status': 'failed',
                    'error': 'No transcript chunks generated',
                    'message': 'Failed to generate chunks'
                }
            return
        
        with indexing_lock:
            indexing_status[video_id]['total_chunks'] = len(chunks)
            indexing_status[video_id]['message'] = f'Generated {len(chunks)} chunks, creating embeddings...'
        
        # Step 3: Generate embeddings for each chunk
        embeddings_list = []
        youtube_chunks = []
        
        logger.info("🔮 Starting embedding generation process...")
        logger.debug("=" * 100)
        logger.debug("🔮 EMBEDDING GENERATION PROGRESS:")
        logger.debug("=" * 100)
        
        for idx, chunk in enumerate(chunks):
            try:
                # Update progress
                progress = int((idx / len(chunks)) * 100)
                with indexing_lock:
                    indexing_status[video_id]['progress'] = progress
                    indexing_status[video_id]['message'] = f'Embedding chunk {idx+1}/{len(chunks)}...'
                
                # Log detailed embedding progress
                start_time = f"{int(chunk['start_timestamp']//60):02d}:{int(chunk['start_timestamp']%60):02d}"
                end_time = f"{int(chunk['end_timestamp']//60):02d}:{int(chunk['end_timestamp']%60):02d}"
                logger.info(f"🔄 Processing chunk {idx+1}/{len(chunks)}: [{start_time}-{end_time}]")
                logger.debug(f"📝 Chunk text: {chunk['text'][:100]}...")
                
                # Get embedding from Ollama
                embedding = get_ollama_embedding(chunk['text'])
                embeddings_list.append(embedding)
                
                # Log embedding success with stats
                logger.debug(f"✅ Chunk {idx+1} embedded successfully (dimension: {len(embedding)})")
                logger.debug(f"📊 Embedding stats: min={embedding.min():.4f}, max={embedding.max():.4f}, mean={embedding.mean():.4f}")
                
                # Create YouTubeTranscriptChunk object
                youtube_chunk = YouTubeTranscriptChunk(
                    video_id=video_id,
                    chunk_text=chunk['text'],
                    start_timestamp=chunk['start_timestamp'],
                    end_timestamp=chunk['end_timestamp'],
                    chunk_index=idx
                )
                youtube_chunks.append(youtube_chunk)
                
            except Exception as e:
                logger.error(f"❌ Failed to embed chunk {idx+1}: {e}")
                continue
        
        logger.debug("=" * 100)
        logger.debug(f"🎉 Embedding generation completed: {len(embeddings_list)}/{len(chunks)} chunks")
        logger.debug("=" * 100)
        
        if not embeddings_list:
            with indexing_lock:
                indexing_status[video_id] = {
                    'status': 'failed',
                    'error': 'Failed to generate embeddings. Is Ollama running?',
                    'message': 'Embedding generation failed'
                }
            return
        
        # Step 4: Add to FAISS index
        with indexing_lock:
            indexing_status[video_id]['message'] = 'Adding to FAISS index...'
        
        logger.info("🗄️ Adding chunks to FAISS vector store...")
        embeddings_array = np.stack(embeddings_list)
        logger.info(f"📊 Embeddings array shape: {embeddings_array.shape}")
        
        chunks_added = memory_layer.add_youtube_chunks(youtube_chunks, embeddings_array)
        logger.info(f"✅ Added {chunks_added} chunks to FAISS index")
        
        # Step 5: Save index
        logger.info("💾 Saving index to disk...")
        memory_layer.save_memory()
        logger.info("✅ Index saved successfully")
        
        # Get final stats
        stats = memory_layer.get_youtube_stats()
        logger.info(f"📊 Final index stats: {stats}")
        
        # Final success status
        with indexing_lock:
            indexing_status[video_id] = {
                'status': 'completed',
                'progress': 100,
                'total_chunks': chunks_added,
                'message': f'Successfully indexed {chunks_added} chunks',
                'end_time': datetime.now().isoformat(),
                'error': None
            }
        
        logger.info("=" * 100)
        logger.info(f"🎉 ASYNC INDEXING COMPLETED FOR VIDEO {video_id}")
        logger.info(f"📈 Total chunks indexed: {chunks_added}")
        logger.info(f"📊 Total chunks in index: {stats['total_chunks']}")
        logger.info(f"🎬 Total videos indexed: {stats['unique_videos']}")
        logger.info("=" * 100)
        
    except Exception as e:
        logger.error(f"💥 Async indexing failed for {video_id}: {str(e)}")
        with indexing_lock:
            indexing_status[video_id] = {
                'status': 'failed',
                'error': str(e),
                'message': f'Indexing failed: {str(e)}',
                'end_time': datetime.now().isoformat()
            }


@app.route('/health')
def health_check():
    """Health check endpoint"""
    stats = memory_layer.get_youtube_stats()
    return jsonify({
        'status': 'healthy',
        'youtube_index': stats
    })


@app.route('/api/index_youtube', methods=['POST'])
def index_youtube():
    """
    Start asynchronous indexing of a YouTube video.
    
    Request body:
        {
            "video_id": "dQw4w9WgXcQ",  // OR
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    
    Response:
        {
            "success": true,
            "video_id": "dQw4w9WgXcQ",
            "message": "Indexing started",
            "status": "started"
        }
    """
    logger.info("=" * 100)
    logger.info("🚀 STARTING ASYNC YOUTUBE VIDEO INDEXING")
    logger.info("=" * 100)
    
    try:
        data = request.get_json()
        logger.info(f"📥 Received request data: {data}")
        
        # Extract video ID
        video_id = data.get('video_id')
        video_url = data.get('video_url')
        
        if not video_id and not video_url:
            logger.error("❌ No video_id or video_url provided")
            return jsonify({
                'success': False,
                'message': 'Either video_id or video_url is required'
            }), 400
        
        if video_url:
            logger.info(f"🔗 Extracting video ID from URL: {video_url}")
            video_id = extract_video_id(video_url)
            if not video_id:
                logger.error(f"❌ Failed to extract video ID from URL: {video_url}")
                return jsonify({
                    'success': False,
                    'message': 'Invalid YouTube URL'
                }), 400
        
        # Check if already indexing
        with indexing_lock:
            if video_id in indexing_status:
                current_status = indexing_status[video_id]['status']
                if current_status in ['started', 'in_progress']:
                    logger.info(f"ℹ️ Video {video_id} is already being indexed")
                    return jsonify({
                        'success': True,
                        'video_id': video_id,
                        'message': 'Indexing already in progress',
                        'status': current_status
                    })
        
        logger.info(f"🎬 Starting async indexing for video: {video_id}")
        
        # Start async indexing in background thread
        thread = threading.Thread(target=index_video_async, args=(video_id,))
        thread.daemon = True
        thread.start()
        
        # Return immediately with started status
        return jsonify({
            'success': True,
            'video_id': video_id,
            'message': 'Indexing started in background',
            'status': 'started'
        })
        
    except Exception as e:
        logger.error("=" * 100)
        logger.error(f"💥 ERROR STARTING INDEXING: {str(e)}")
        logger.error("=" * 100)
        logger.error(traceback.format_exc())
        logger.error("=" * 100)
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500
    

@app.route('/api/indexing_status/<video_id>', methods=['GET'])
def get_indexing_status(video_id):
    """
    Get the current indexing status for a video.
    
    Response:
        {
            "video_id": "dQw4w9WgXcQ",
            "status": "started|in_progress|completed|failed",
            "progress": 45,
            "total_chunks": 100,
            "message": "Embedding chunk 45/100...",
            "start_time": "2025-01-27T20:15:00",
            "end_time": "2025-01-27T20:18:00" (if completed/failed),
            "error": "Error message" (if failed)
        }
    """
    try:
        with indexing_lock:
            if video_id not in indexing_status:
                logger.error(f"No indexing found for video {video_id}")
                return jsonify({
                    'success': False,
                    'message': 'No indexing found for this video'
                }), 404
        
        status_data = indexing_status[video_id].copy()
        status_data['video_id'] = video_id
        return jsonify({
            'success': True,
            'video_id': video_id,
            'status': status_data['status'],
            'progress': status_data['progress'],
            'total_chunks': status_data['total_chunks'],
            'message': status_data['message'],
            'start_time': status_data['start_time'],
            'end_time': status_data['end_time'],
            'error': status_data['error']
        })
    except Exception as e:
        logger.error(f"Error getting indexing status for video {video_id} - {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/ask_youtube', methods=['POST'])
def ask_youtube():
    """
    Ask a question about indexed YouTube content.
    
    Request body:
        {
            "question": "What is the main topic?",
            "video_id": "dQw4w9WgXcQ",  // Optional: restrict to specific video
            "top_k": 3  // Optional: number of chunks to retrieve
        }
    
    Response:
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
            ]
        }
    """
    try:
        data = request.get_json()
        
        question = data.get('question')
        video_id = data.get('video_id')
        top_k = data.get('top_k', 3)
        
        if not question:
            return jsonify({
                'success': False,
                'message': 'Question is required'
            }), 400
        
        logger.info(f"Question: {question}")
        
        # Step 1: Check if index is empty
        stats = memory_layer.get_youtube_stats()
        if stats['total_chunks'] == 0:
            return jsonify({
                'success': False,
                'message': 'No YouTube videos indexed yet. Please index a video first.'
            }), 400
        
        # Step 2: Embed the question
        try:
            question_embedding = get_ollama_embedding(question)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to embed question. Is Ollama running? Error: {str(e)}'
            }), 500
        
        # Step 3: Search for relevant chunks
        contexts = memory_layer.search_youtube_content(
            query_embedding=question_embedding,
            top_k=top_k,
            video_id_filter=video_id
        )
        
        if not contexts:
            return jsonify({
                'success': False,
                'message': 'No relevant content found'
            }), 404
        
        # Step 4: Expand context with previous and next chunks
        expanded_contexts = expand_context_with_surrounding_chunks(contexts, memory_layer)
        
        logger.info(f"🔍 Found {len(contexts)} top chunks, expanded to {len(expanded_contexts)} chunks with context")
        
        # Step 5: Generate answer with Gemini
        # Build context string from expanded chunks
        context_text = "\n\n".join([
            f"[Video {ctx.video_id} at {int(ctx.timestamp)}s]\n{ctx.chunk_text}"
            for ctx in expanded_contexts
        ])
        
        # Create prompt for Gemini
        prompt = f"""You are a helpful assistant that answers questions about YouTube videos based on their transcripts.

Context from video transcript(s):
{context_text}

Question: {question}

Please provide a detailed answer based on the context above. If the context doesn't contain enough information to fully answer the question, say so."""
        
        try:
            response = gemini_model.generate_content(prompt)
            answer = response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to generate answer: {str(e)}'
            }), 500
        
        logger.info(f"Generated answer with {len(expanded_contexts)} expanded contexts for LLM (original top-3: {len(contexts)})")
        
        # Create YouTube links for ORIGINAL top-3 matching chunks only (not expanded context)
        youtube_links = [
            create_youtube_link(ctx.video_id, ctx.timestamp)
            for ctx in contexts  # Use original top-3 contexts for links
        ]
        
        # Return only the original top-3 contexts for display, but LLM used expanded context
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,  # Generated using expanded context (up to 9 chunks)
            'contexts': [
                {
                    'video_id': ctx.video_id,
                    'chunk_text': ctx.chunk_text,
                    'timestamp': ctx.timestamp,
                    'relevance_score': ctx.relevance_score
                }
                for ctx in contexts  # Return only original top-3 for display
            ],
            'youtube_links': youtube_links,  # Links for top-3 matching chunks only
            'context_info': {
                'original_chunks': len(contexts),
                'expanded_chunks': len(expanded_contexts),
                'expansion_ratio': f"{len(expanded_contexts)}/{len(contexts)}",
                'note': 'Answer generated using expanded context, links show top-3 matches only'
            }
        })
        
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Make sure the server is accessible from the Chrome extension
    app.run(host='0.0.0.0', port=5000, debug=True)
