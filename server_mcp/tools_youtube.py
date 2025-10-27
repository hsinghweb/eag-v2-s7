"""
YouTube Tools
Tools for fetching, chunking, and embedding YouTube transcripts with full sentences
"""
import logging
import re
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import numpy as np

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL or video ID
        
    Returns:
        11-character video ID or None if invalid
    """
    # If already a video ID (11 characters)
    if len(url) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', url):
        return url
    
    # Extract from URL
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def fetch_youtube_transcript(video_id: str, languages: List[str] = ['en']) -> List[Dict]:
    """
    Fetch transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        languages: List of language codes to try (default: ['en'])
        
    Returns:
        List of transcript segments with 'text', 'start', 'duration'
        
    Raises:
        Exception: If transcript cannot be fetched
    """
    logger.info(f"🎬 Fetching transcript for video: {video_id}")
    logger.info(f"🌐 Trying languages: {languages}")
    
    try:
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=languages)
        
        # Convert to list of dicts
        segments = []
        for item in transcript_data:
            segments.append({
                'text': item.text,
                'start': item.start,
                'duration': item.duration
            })
        
        logger.info(f"✅ Successfully fetched {len(segments)} transcript segments")
        
        # DEBUG: Print complete transcript data
        logger.debug("=" * 80)
        logger.debug("📝 COMPLETE TRANSCRIPT DATA:")
        logger.debug("=" * 80)
        for i, segment in enumerate(segments):
            logger.debug(f"Segment {i+1:3d}: [{segment['start']:6.1f}s] {segment['text']}")
        logger.debug("=" * 80)
        
        return segments
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch transcript for {video_id}: {e}")
        logger.error("💡 Make sure the video has English captions available")
        raise


def group_transcript_segments(
    transcript_data: List[Dict], 
    max_duration: float = 30.0, 
    max_chars: int = 500
) -> List[Dict]:
    """
    Group transcript segments into complete statements/sentences.
    Based on session-7/youtube.py implementation.
    
    Args:
        transcript_data: List of transcript segments from YouTube API
        max_duration: Maximum duration for a group in seconds (default: 30)
        max_chars: Maximum characters for a group (default: 500)
        
    Returns:
        List of grouped chunks with 'text', 'start_timestamp', 'end_timestamp'
    """
    if not transcript_data:
        logger.warning("⚠️ No transcript data provided for grouping")
        return []
    
    logger.info(f"🔄 Grouping {len(transcript_data)} segments into complete sentences")
    logger.info(f"📏 Max duration: {max_duration}s, Max chars: {max_chars}")
    
    grouped = []
    current_group = []
    start_time = None
    current_text = ""
    
    for item in transcript_data:
        if start_time is None:
            start_time = item['start']
        
        current_group.append(item)
        current_text += " " + item['text'] if current_text else item['text']
        
        # Calculate duration of current group
        duration = item['start'] - start_time
        ends_with_punctuation = current_text.rstrip().endswith(('.', '!', '?'))
        
        # Group by: ending punctuation, max duration, or max characters
        if ends_with_punctuation or duration >= max_duration or len(current_text) >= max_chars:
            end_time = item['start'] + item['duration']
            grouped.append({
                'text': current_text.strip(),
                'start_timestamp': start_time,
                'end_timestamp': end_time
            })
            
            # DEBUG: Log each chunk creation
            logger.debug(f"📦 Created chunk {len(grouped)}: [{start_time:.1f}s-{end_time:.1f}s] {current_text.strip()[:100]}...")
            
            current_group = []
            current_text = ""
            start_time = None
    
    # Add any remaining text
    if current_text:
        end_time = transcript_data[-1]['start'] + transcript_data[-1]['duration']
        grouped.append({
            'text': current_text.strip(),
            'start_timestamp': start_time,
            'end_timestamp': end_time
        })
        logger.debug(f"📦 Created final chunk {len(grouped)}: [{start_time:.1f}s-{end_time:.1f}s] {current_text.strip()[:100]}...")
    
    logger.info(f"✅ Grouped {len(transcript_data)} segments into {len(grouped)} complete chunks")
    
    # DEBUG: Print all chunks
    logger.debug("=" * 80)
    logger.debug("📦 ALL GROUPED CHUNKS:")
    logger.debug("=" * 80)
    for i, chunk in enumerate(grouped):
        logger.debug(f"Chunk {i+1:3d}: [{chunk['start_timestamp']:6.1f}s-{chunk['end_timestamp']:6.1f}s] {chunk['text']}")
    logger.debug("=" * 80)
    
    return grouped


def get_ollama_embedding(text: str, model: str = "nomic-embed-text") -> np.ndarray:
    """
    Get embedding from Ollama API.
    
    Args:
        text: Text to embed
        model: Ollama model name (default: nomic-embed-text)
        
    Returns:
        Numpy array of embeddings (768 dimensions for nomic-embed-text)
        
    Raises:
        Exception: If Ollama API fails
    """
    logger.debug(f"🔮 Getting embedding for text: '{text[:100]}...' (model: {model})")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": model,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        
        embedding = response.json()["embedding"]
        embedding_array = np.array(embedding, dtype=np.float32)
        
        logger.debug(f"✅ Got embedding with dimension: {len(embedding_array)}")
        logger.debug(f"📊 Embedding stats: min={embedding_array.min():.4f}, max={embedding_array.max():.4f}, mean={embedding_array.mean():.4f}")
        
        return embedding_array
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to Ollama. Is it running? (Try: ollama serve)")
        raise Exception("Ollama is not running. Please start Ollama service.")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed to Ollama: {e}")
        raise Exception(f"Ollama request failed: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to get embedding from Ollama: {e}")
        raise


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to YouTube timestamp format (HH:MM:SS or MM:SS).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def create_youtube_link(video_id: str, timestamp: float) -> str:
    """
    Create a YouTube link with timestamp.
    
    Args:
        video_id: YouTube video ID
        timestamp: Time in seconds
        
    Returns:
        YouTube URL with timestamp parameter
    """
    timestamp_int = int(timestamp)
    return f"https://www.youtube.com/watch?v={video_id}&t={timestamp_int}s"


# Test function
if __name__ == "__main__":
    # Test with a sample video
    test_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    print(f"Testing with video ID: {test_video_id}")
    
    try:
        # Fetch transcript
        transcript = fetch_youtube_transcript(test_video_id)
        print(f"✅ Fetched {len(transcript)} segments")
        
        # Group into full sentences
        chunks = group_transcript_segments(transcript, max_duration=30, max_chars=500)
        print(f"✅ Created {len(chunks)} complete sentence chunks")
        
        # Show first chunk
        if chunks:
            first_chunk = chunks[0]
            print("\n📝 First chunk:")
            print(f"   Start: {format_timestamp(first_chunk['start_timestamp'])}")
            print(f"   Text: {first_chunk['text'][:150]}...")
            
            # Test embedding
            embedding = get_ollama_embedding(first_chunk['text'])
            print(f"✅ Got embedding with dimension: {len(embedding)}")
            
            # Test link creation
            link = create_youtube_link(test_video_id, first_chunk['start_timestamp'])
            print(f"🔗 YouTube link: {link}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

