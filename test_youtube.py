#!/usr/bin/env python3
"""
Test Script for YouTube RAG Assistant
Tests transcript fetching, chunking, and FAISS indexing
"""

import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
from server_mcp.tools_youtube import (
    extract_video_id,
    fetch_youtube_transcript,
    group_transcript_segments,
    get_ollama_embedding,
    format_timestamp,
    create_youtube_link
)

from agent.memory import MemoryLayer
from agent.models import YouTubeTranscriptChunk
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_youtube_indexing(video_id: str):
    """
    Test complete YouTube indexing pipeline
    """
    logger.info("=" * 100)
    logger.info(f"🧪 TESTING YOUTUBE INDEXING FOR VIDEO: {video_id}")
    logger.info("=" * 100)
    
    try:
        # Step 1: Test video ID extraction
        logger.info("🔍 STEP 1: Testing video ID extraction...")
        extracted_id = extract_video_id(video_id)
        if extracted_id:
            logger.info(f"✅ Video ID extracted: {extracted_id}")
            video_id = extracted_id
        else:
            logger.info(f"ℹ️ Using provided video ID: {video_id}")
        
        # Step 2: Test transcript fetching
        logger.info("📝 STEP 2: Testing transcript fetching...")
        transcript = fetch_youtube_transcript(video_id)
        logger.info(f"✅ Transcript fetched: {len(transcript)} segments")
        
        # Step 3: Test chunking
        logger.info("🔄 STEP 3: Testing transcript chunking...")
        chunks = group_transcript_segments(transcript, max_duration=30, max_chars=500)
        logger.info(f"✅ Transcript chunked: {len(chunks)} complete sentence chunks")
        
        # Step 4: Test embedding generation (first chunk only)
        logger.info("🔮 STEP 4: Testing embedding generation...")
        if chunks:
            first_chunk = chunks[0]
            logger.info(f"📝 Testing with first chunk: '{first_chunk['text'][:100]}...'")
            
            try:
                embedding = get_ollama_embedding(first_chunk['text'])
                logger.info(f"✅ Embedding generated: dimension {len(embedding)}")
            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
                logger.error("💡 Make sure Ollama is running: ollama serve")
                return False
        
        # Step 5: Test FAISS indexing (first 3 chunks only for speed)
        logger.info("🗄️ STEP 5: Testing FAISS indexing...")
        test_chunks = chunks[:3]  # Test with first 3 chunks only
        
        # Generate embeddings for test chunks
        embeddings_list = []
        youtube_chunks = []
        
        for idx, chunk in enumerate(test_chunks):
            try:
                embedding = get_ollama_embedding(chunk['text'])
                embeddings_list.append(embedding)
                
                youtube_chunk = YouTubeTranscriptChunk(
                    video_id=video_id,
                    chunk_text=chunk['text'],
                    start_timestamp=chunk['start_timestamp'],
                    end_timestamp=chunk['end_timestamp'],
                    chunk_index=idx
                )
                youtube_chunks.append(youtube_chunk)
                
                logger.info(f"✅ Chunk {idx+1} processed")
                
            except Exception as e:
                logger.error(f"❌ Failed to process chunk {idx+1}: {e}")
                continue
        
        if not embeddings_list:
            logger.error("❌ No embeddings generated for FAISS test")
            return False
        
        # Test FAISS indexing
        embeddings_array = np.stack(embeddings_list)
        logger.info(f"📊 Embeddings array shape: {embeddings_array.shape}")
        
        # Initialize memory layer for testing
        memory_layer = MemoryLayer(memory_file="test_memory.json", load_existing=False)
        
        chunks_added = memory_layer.add_youtube_chunks(youtube_chunks, embeddings_array)
        logger.info(f"✅ Added {chunks_added} chunks to FAISS index")
        
        # Test search
        logger.info("🔍 STEP 6: Testing FAISS search...")
        test_query = "What is this video about?"
        query_embedding = get_ollama_embedding(test_query)
        
        results = memory_layer.search_youtube_content(query_embedding, top_k=2)
        logger.info(f"✅ Search completed: {len(results)} results")
        
        for i, result in enumerate(results):
            logger.info(f"📄 Result {i+1}: [{result.timestamp:.1f}s] {result.chunk_text[:100]}...")
            logger.info(f"🎯 Relevance score: {result.relevance_score:.4f}")
        
        # Cleanup test files
        if os.path.exists("test_memory.json"):
            os.remove("test_memory.json")
        if os.path.exists("youtube_faiss.index"):
            os.remove("youtube_faiss.index")
        if os.path.exists("youtube_metadata.pkl"):
            os.remove("youtube_metadata.pkl")
        
        logger.info("=" * 100)
        logger.info("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        logger.info("=" * 100)
        return True
        
    except Exception as e:
        logger.error("=" * 100)
        logger.error(f"💥 TEST FAILED: {str(e)}")
        logger.error("=" * 100)
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 100)
        return False

def main():
    """
    Main test function
    """
    # Test with a well-known video that has captions
    test_videos = [
        "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up (classic test)
        "jNQXAC9IVRw",  # Me at the zoo (first YouTube video)
    ]
    
    print("🧪 YouTube RAG Assistant Test Suite")
    print("=" * 50)
    
    for video_id in test_videos:
        print(f"\n🎬 Testing with video: {video_id}")
        success = test_youtube_indexing(video_id)
        
        if success:
            print(f"✅ Test PASSED for video {video_id}")
        else:
            print(f"❌ Test FAILED for video {video_id}")
            break
    
    print("\n🏁 Test suite completed!")

if __name__ == "__main__":
    main()
