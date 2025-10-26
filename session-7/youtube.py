from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS or MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    else:
        return f"[{minutes:02d}:{secs:02d}]"

def group_transcript_segments(transcript_data, max_duration=10, max_chars=200):
    """Group transcript segments into more complete statements"""
    grouped = []
    current_group = []
    start_time = None
    current_text = ""
    
    for item in transcript_data:
        if start_time is None:
            start_time = item.start
        
        current_group.append(item)
        current_text += " " + item.text if current_text else item.text
        
        # Check if we should create a new group
        duration = item.start - start_time
        ends_with_punctuation = current_text.rstrip().endswith(('.', '!', '?'))
        
        # Group by: ending punctuation, max duration, or max characters
        if ends_with_punctuation or duration >= max_duration or len(current_text) >= max_chars:
            grouped.append({
                'timestamp': start_time,
                'text': current_text.strip()
            })
            current_group = []
            current_text = ""
            start_time = None
    
    # Add any remaining text
    if current_text:
        grouped.append({
            'timestamp': start_time,
            'text': current_text.strip()
        })
    
    return grouped

def test_youtube_with_timestamps():
    url = "https://www.youtube.com/watch?v=ZGwQoRw7mh8"
    video_id = extract_video_id(url)
    
    if not video_id:
        print("Invalid YouTube URL")
        return
    
    try:
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=['en'])
        
        # Group segments into complete statements
        grouped_segments = group_transcript_segments(transcript_data)
        
        print("--- YouTube Transcription with Timestamps ---")
        for segment in grouped_segments:
            timestamp_str = format_timestamp(segment['timestamp'])
            print(f"{timestamp_str} {segment['text']}")
            print()  # Add blank line for readability
        
        print("----------------------------------------------")
        
    except Exception as e:
        import traceback
        print("An error occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    test_youtube_with_timestamps()