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
from tools.tools_youtube import (
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

# Import cognitive layers for YouTube questions
from agent.ai_agent import CognitiveAgent
from agent.perception import PerceptionLayer
from agent.decision import DecisionLayer
from agent.action import ActionLayer

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

# Initialize cognitive layers for YouTube questions
perception_layer = PerceptionLayer(gemini_model)
decision_layer = DecisionLayer(gemini_model)
action_layer = ActionLayer(session=None, tools=[])  # No MCP tools needed for YouTube

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
        
        try:
            transcript = fetch_youtube_transcript(video_id)
        except Exception as e:
            logger.error(f"Transcript fetch failed for {video_id}: {e}")
            with indexing_lock:
                indexing_status[video_id] = {
                    'status': 'failed',
                    'progress': 0,
                    'total_chunks': 0,
                    'message': 'No English transcript available for this video',
                    'start_time': indexing_status[video_id].get('start_time'),
                    'end_time': datetime.now().isoformat(),
                    'error': 'no_transcript'
                }
            return
        
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


@app.route('/api/video_indexed/<video_id>', methods=['GET'])
def check_video_indexed(video_id):
    """
    Check if a specific video is indexed.
    
    Response:
        {
            "indexed": true/false,
            "video_id": "dQw4w9WgXcQ",
            "chunk_count": 42
        }
    """
    try:
        stats = memory_layer.get_youtube_stats()
        indexed_videos = set(stats.get('video_ids', []))
        is_indexed = video_id in indexed_videos
        
        # Count chunks for this specific video
        chunk_count = 0
        if memory_layer.youtube_metadata:
            chunk_count = sum(1 for meta in memory_layer.youtube_metadata if meta.get('video_id') == video_id)
        
        return jsonify({
            'indexed': is_indexed,
            'video_id': video_id,
            'chunk_count': chunk_count
        })
        
    except Exception as e:
        logger.error(f"Error checking video index status: {str(e)}")
        return jsonify({
            'indexed': False,
            'video_id': video_id,
            'chunk_count': 0,
            'error': str(e)
        }), 500


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
        
        # Check if video is already indexed
        logger.info(f"🔍 Checking if video {video_id} is already indexed...")
        indexed_videos = set()
        for metadata in memory_layer.youtube_metadata:
            indexed_videos.add(metadata['video_id'])
        
        if video_id in indexed_videos:
            logger.info(f"✅ Video {video_id} is already indexed")
            return jsonify({
                'success': True,
                'video_id': video_id,
                'message': 'Video is already indexed and ready for questions',
                'status': 'already_indexed'
            })
        
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
            'status': status_data.get('status'),
            'progress': status_data.get('progress', 0),
            'total_chunks': status_data.get('total_chunks', 0),
            'message': status_data.get('message', ''),
            'start_time': status_data.get('start_time'),
            'end_time': status_data.get('end_time'),
            'error': status_data.get('error')
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
    Ask a question about indexed YouTube content using cognitive layers.
    
    Request body:
        {
            "question": "What is the main topic?"
        }
    
    Response:
        {
            "success": true,
            "question": "What is the main topic?",
            "answer": "The video discusses...",
            "contexts": [...],
            "youtube_links": [...],
            "cognitive_analysis": {
                "perception": {...},
                "decision": {...},
                "action": {...}
            }
        }
    """
    try:
        data = request.get_json()
        question = data.get('question')
        video_id = data.get('video_id')  # Optional: restrict to specific video
        
        if not question:
            return jsonify({
                'success': False,
                'message': 'Question is required'
            }), 400
        
        # If video_id is provided, validate it's indexed
        if video_id:
            stats = memory_layer.get_youtube_stats()
            indexed_videos = set(stats.get('video_ids', []))
            if video_id not in indexed_videos:
                return jsonify({
                    'success': False,
                    'message': f'Video {video_id} is not indexed yet. Please index it first.'
                }), 400
            logger.info(f"🎬 Processing YouTube question restricted to video: {video_id}")
        else:
            logger.info(f"🎬 Processing YouTube question with cognitive layers (all videos): {question}")
        
        # Check if index is empty
        stats = memory_layer.get_youtube_stats()
        if stats['total_chunks'] == 0:
            return jsonify({
                'success': False,
                'message': 'No YouTube videos indexed yet. Please index a video first.'
            }), 400
        
        # Use cognitive layers to process the question
        import asyncio
        
        # Create cognitive agent instance
        cognitive_agent = CognitiveAgent(
            session=None,  # No MCP session needed
            tools=[],      # No MCP tools needed
            preferences={},
            memory_file=memory_file
        )
        
        # Process question using cognitive layers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                cognitive_agent.process_youtube_question(question, memory_layer, gemini_model, video_id=video_id)
            )
        finally:
            loop.close()
        
        logger.info("✅ Cognitive processing completed successfully")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in cognitive YouTube question processing: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Make sure the server is accessible from the Chrome extension
    app.run(host='0.0.0.0', port=5000, debug=True)
