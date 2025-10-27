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

logger.info("YouTube RAG Assistant server started")
logger.info(f"Memory file: {memory_file}")


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
    Index a YouTube video by fetching transcript, chunking, and embedding.
    
    Request body:
        {
            "video_id": "dQw4w9WgXcQ",  // OR
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    
    Response:
        {
            "success": true,
            "video_id": "dQw4w9WgXcQ",
            "chunks_indexed": 25,
            "message": "Successfully indexed video"
        }
    """
    logger.info("=" * 100)
    logger.info("🚀 STARTING YOUTUBE VIDEO INDEXING")
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
        
        logger.info(f"🎬 Starting indexing process for video: {video_id}")
        
        # Step 1: Fetch transcript
        logger.info("📝 STEP 1: Fetching YouTube transcript...")
        try:
            transcript = fetch_youtube_transcript(video_id)
            logger.info(f"✅ Transcript fetched successfully: {len(transcript)} segments")
        except Exception as e:
            logger.error(f"❌ Failed to fetch transcript: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Failed to fetch transcript: {str(e)}'
            }), 400
        
        # Step 2: Group into full sentences
        logger.info("🔄 STEP 2: Grouping transcript into complete sentences...")
        chunks = group_transcript_segments(transcript, max_duration=30, max_chars=500)
        
        if not chunks:
            logger.error("❌ No transcript chunks generated")
            return jsonify({
                'success': False,
                'message': 'No transcript chunks generated'
            }), 400
        
        logger.info(f"✅ Transcript grouped into {len(chunks)} complete sentence chunks")
        
        # Step 3: Generate embeddings for each chunk
        logger.info("🔮 STEP 3: Generating embeddings for each chunk...")
        embeddings_list = []
        youtube_chunks = []
        
        for idx, chunk in enumerate(chunks):
            logger.info(f"🔄 Processing chunk {idx+1}/{len(chunks)}: [{chunk['start_timestamp']:.1f}s-{chunk['end_timestamp']:.1f}s]")
            logger.debug(f"📝 Chunk text: {chunk['text']}")
            
            try:
                # Get embedding from Ollama
                embedding = get_ollama_embedding(chunk['text'])
                embeddings_list.append(embedding)
                
                # Create YouTubeTranscriptChunk object
                youtube_chunk = YouTubeTranscriptChunk(
                    video_id=video_id,
                    chunk_text=chunk['text'],
                    start_timestamp=chunk['start_timestamp'],
                    end_timestamp=chunk['end_timestamp'],
                    chunk_index=idx
                )
                youtube_chunks.append(youtube_chunk)
                
                logger.debug(f"✅ Chunk {idx+1} embedded successfully (dimension: {len(embedding)})")
                
            except Exception as e:
                logger.error(f"❌ Failed to embed chunk {idx+1}: {e}")
                continue
        
        if not embeddings_list:
            logger.error("❌ No embeddings generated. Check Ollama connection.")
            return jsonify({
                'success': False,
                'message': 'Failed to generate embeddings. Is Ollama running?'
            }), 500
        
        logger.info(f"✅ Generated {len(embeddings_list)} embeddings successfully")
        
        # Step 4: Add to FAISS index
        logger.info("🗄️ STEP 4: Adding chunks to FAISS vector store...")
        embeddings_array = np.stack(embeddings_list)
        logger.info(f"📊 Embeddings array shape: {embeddings_array.shape}")
        
        chunks_added = memory_layer.add_youtube_chunks(youtube_chunks, embeddings_array)
        logger.info(f"✅ Added {chunks_added} chunks to FAISS index")
        
        # Step 5: Save index
        logger.info("💾 STEP 5: Saving index to disk...")
        memory_layer.save_memory()
        logger.info("✅ Index saved successfully")
        
        # Get final stats
        stats = memory_layer.get_youtube_stats()
        logger.info(f"📊 Final index stats: {stats}")
        
        logger.info("=" * 100)
        logger.info(f"🎉 SUCCESSFULLY INDEXED VIDEO {video_id}")
        logger.info(f"📈 Total chunks indexed: {chunks_added}")
        logger.info(f"📊 Total chunks in index: {stats['total_chunks']}")
        logger.info(f"🎬 Total videos indexed: {stats['unique_videos']}")
        logger.info("=" * 100)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'chunks_indexed': chunks_added,
            'message': f'Successfully indexed {chunks_added} chunks'
        })
        
    except Exception as e:
        logger.error("=" * 100)
        logger.error(f"💥 ERROR INDEXING VIDEO: {str(e)}")
        logger.error("=" * 100)
        logger.error(traceback.format_exc())
        logger.error("=" * 100)
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
        
        # Step 4: Generate answer with Gemini
        # Build context string from top chunks
        context_text = "\n\n".join([
            f"[Video {ctx.video_id} at {int(ctx.timestamp)}s]\n{ctx.chunk_text}"
            for ctx in contexts
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
        
        # Step 5: Create YouTube links with timestamps
        youtube_links = [
            create_youtube_link(ctx.video_id, ctx.timestamp)
            for ctx in contexts
        ]
        
        logger.info(f"Generated answer with {len(contexts)} contexts")
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'contexts': [
                {
                    'video_id': ctx.video_id,
                    'chunk_text': ctx.chunk_text,
                    'timestamp': ctx.timestamp,
                    'relevance_score': ctx.relevance_score
                }
                for ctx in contexts
            ],
            'youtube_links': youtube_links
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
