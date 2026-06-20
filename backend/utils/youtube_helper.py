from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse

def get_video_id(url: str) -> str:
    """Extracts the YouTube Video ID from standard and shortened URLs."""
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            p = urllib.parse.parse_qs(parsed_url.query)
            return p['v'][0]
        if parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    return None

def extract_transcript(url: str) -> str:
    """Fetches the transcript of a YouTube video as plain text."""
    video_id = get_video_id(url)
    if not video_id:
        return ""
        
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # Try to find a manual or generated transcript in English
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'en-CA', 'en-AU'])
        except:
            # Fallback to the first available transcript if no english ones
            transcript = next(iter(transcript_list))
            
        data = transcript.fetch()
        transcript_text = " ".join([s.text for s in data.snippets])
        return transcript_text
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        return ""
