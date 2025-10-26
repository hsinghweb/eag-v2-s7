from youtube_transcript_api import YouTubeTranscriptApi

video_id = "L3wOHuaE4Jc"

try:
    # 1. Instantiate the class
    api = YouTubeTranscriptApi()
    
    # 2. Call the fetch() method on the instance
    transcript_data = api.fetch(video_id)

    print("--- Transcription with Timestamps ---")
    # 3. Display each segment with its timestamp
    for item in transcript_data:
        timestamp = item.start  # Start time in seconds
        text = item.text
        
        # Convert seconds to MM:SS format
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        
        print(f"[{minutes:02d}:{seconds:02d}] {text}")
    
    print("-------------------------------------")

except Exception as e:
    import traceback
    print("An error occurred:")
    traceback.print_exc()