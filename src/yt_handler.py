import yt_dlp
import os
import urllib.parse

class YTHandler:
    def __init__(self):
        ffmpeg_dir = os.path.join(os.path.dirname(__file__), 'bin')
        ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        if os.path.exists(ffmpeg_exe):
            self.ydl_opts['ffmpeg_location'] = ffmpeg_dir
        else:
            # Let yt-dlp find it in the system PATH
            pass

    def _is_url(self, text):
        parsed = urllib.parse.urlparse(text)
        return bool(parsed.scheme and parsed.netloc)

    def extract_info(self, query):
        """
        Extract stream information using a URL or a search query.
        Returns a tuple: (stream_url, title) or (None, None)
        """
        raw_query = query.strip()
        search_target = raw_query if self._is_url(raw_query) else f"ytsearch1:{raw_query}"
        
        print(f"yt-dlp processing: {search_target}")
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(search_target, download=False)
                
                # If it was a search, the actual video is inside the 'entries' array
                if 'entries' in info and len(info['entries']) > 0:
                    info = info['entries'][0]
                
                stream_url = info.get('url', None)
                return {
                    "url": stream_url,
                    "title": info.get('title', 'Unknown Track'),
                    "author": info.get('uploader', info.get('channel', 'Unknown Artist')),
                    "thumbnail_url": info.get('thumbnail', None),
                    "video_id": info.get('id', None)
                }
            except Exception as e:
                print(f"Error extracting info: {e}")
                return None
