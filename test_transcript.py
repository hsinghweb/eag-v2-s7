#!/usr/bin/env python3
"""
Simple YouTube Transcript Test
Tests just the transcript fetching functionality
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
from server_mcp.tools_youtube import (
    extract_video_id,
    fetch_youtube_transcript,
    group_transcript_segments,
    format_timestamp
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_transcript_only(video_id: str):
    """
    Test only transcript fetching and chunking (no embeddings)
    """
    logger.info("=" * 80)
    logger.info(f"🧪 TESTING TRANSCRIPT FETCHING FOR: {video_id}")
    logger.info("=" * 80)
    
    try:
        # Extract video ID if needed
        extracted_id = extract_video_id(video_id)
        if extracted_id:
            logger.info(f"✅ Video ID: {extracted_id}")
            video_id = extracted_id
        else:
            logger.info(f"ℹ️ Using provided ID: {video_id}")
        
        # Fetch transcript
        logger.info("📝 Fetching transcript...")
        transcript = fetch_youtube_transcript(video_id)
        logger.info(f"✅ Fetched {len(transcript)} segments")
        
        # Show first few segments
        logger.info("📄 First 5 segments:")
        for i, segment in enumerate(transcript[:5]):
            timestamp = format_timestamp(segment['start'])
            logger.info(f"  {i+1}. [{timestamp}] {segment['text']}")
        
        # Group into chunks
        logger.info("🔄 Grouping into complete sentences...")
        chunks = group_transcript_segments(transcript, max_duration=30, max_chars=500)
        logger.info(f"✅ Created {len(chunks)} complete sentence chunks")
        
        # Show first few chunks
        logger.info("📦 First 3 chunks:")
        for i, chunk in enumerate(chunks[:3]):
            start_time = format_timestamp(chunk['start_timestamp'])
            end_time = format_timestamp(chunk['end_timestamp'])
            logger.info(f"  {i+1}. [{start_time}-{end_time}] {chunk['text'][:100]}...")
        
        logger.info("=" * 80)
        logger.info("🎉 TRANSCRIPT TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"💥 TRANSCRIPT TEST FAILED: {str(e)}")
        logger.error("=" * 80)
        return False

if __name__ == "__main__":
    # Test with Rick Astley video (has captions)
    test_video = "dQw4w9WgXcQ"
    print(f"🎬 Testing transcript fetching for: {test_video}")
    
    success = test_transcript_only(test_video)
    
    if success:
        print("✅ Transcript test PASSED!")
    else:
        print("❌ Transcript test FAILED!")
        sys.exit(1)
