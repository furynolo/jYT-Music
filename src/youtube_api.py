from googleapiclient.discovery import build
import urllib.parse
import re
from PySide6.QtCore import QThread, Signal

def parse_duration(duration_str):
    """Parses ISO 8601 duration string (e.g., PT3M15S) to MM:SS string."""
    if not duration_str:
        return "0:00"
        
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    
    if not match:
        return "0:00"
        
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"

class YouTubeAPI:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.youtube = None

    def build_service(self):
        if self.auth_manager.is_authenticated():
            self.youtube = build('youtube', 'v3', credentials=self.auth_manager.credentials)
            return True
        return False

    def get_user_playlists(self):
        if not self.build_service():
            return []
        
        playlists = []
        try:
            # Special entry for Liked Videos
            playlists.append({"id": "LL", "title": "Liked Songs (YouTube)"})

            request = self.youtube.playlists().list(
                part="snippet,contentDetails",
                mine=True,
                maxResults=50
            )
            response = request.execute()
            
            for item in response.get('items', []):
                snippet = item.get('snippet', {})
                thumbnails = snippet.get('thumbnails', {})
                high_res = thumbnails.get('high', {}).get('url', '')
                if not high_res:
                    high_res = thumbnails.get('standard', {}).get('url', '')
                if not high_res:
                    high_res = thumbnails.get('default', {}).get('url', '')
                    
                playlists.append({
                    "id": item['id'],
                    "title": snippet.get('title', 'Unknown'),
                    "item_count": item.get('contentDetails', {}).get('itemCount', 0),
                    "thumbnail_url": high_res,
                    "channel_title": snippet.get('channelTitle', 'Unknown')
                })
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            raise e
            
        return playlists

    def get_playlist_items(self, playlist_id, page_token=None):
        if not self.build_service():
            return [], None
        
        tracks = []
        next_page_token = None
        try:
            if playlist_id == "LL":
                # Liked videos (special handling)
                request = self.youtube.videos().list(
                    part="snippet,contentDetails",
                    myRating="like",
                    maxResults=50,
                    pageToken=page_token
                )
                response = request.execute()
                next_page_token = response.get('nextPageToken')
                for item in response.get('items', []):
                    snippet = item['snippet']
                    video_id = item['id']
                    content_details = item.get('contentDetails', {})
                    thumbnail_url = snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                    duration_str = content_details.get('duration', '')
                    
                    tracks.append({
                        "title": snippet['title'],
                        "author": snippet.get('channelTitle', 'Unknown Artist'),
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail_url": thumbnail_url,
                        "duration": parse_duration(duration_str)
                    })
            else:
                # Standard playlist fetching
                request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=page_token
                )
                response = request.execute()
                next_page_token = response.get('nextPageToken')
                
                video_ids = []
                temp_tracks = []
                
                for item in response.get('items', []):
                    snippet = item.get('snippet', {})
                    if not snippet: continue
                    
                    # Defensively find Video ID
                    resource = snippet.get('resourceId', {})
                    video_id = resource.get('videoId')
                    if not video_id: 
                        video_id = snippet.get('video_id') # Fallback
                    
                    if not video_id: continue
                    
                    thumbnail_url = snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                    
                    video_ids.append(video_id)
                    temp_tracks.append({
                        "title": snippet.get('title', 'Unknown Track'),
                        "author": snippet.get('videoOwnerChannelTitle', snippet.get('channelTitle', 'Unknown Artist')),
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail_url": thumbnail_url,
                        "duration": "0:00"
                    })
                    
                # Batch fetch durations
                if video_ids:
                    dur_request = self.youtube.videos().list(
                        part="contentDetails",
                        id=",".join(video_ids)
                    )
                    dur_response = dur_request.execute()
                    durations = {}
                    for v_item in dur_response.get('items', []):
                        dur_str = v_item.get('contentDetails', {}).get('duration', '')
                        durations[v_item['id']] = parse_duration(dur_str)
                    
                    for track in temp_tracks:
                        track['duration'] = durations.get(track['video_id'], "0:00")
                        tracks.append(track)
        except Exception as e:
            print(f"Error fetching playlist items: {e}")
            raise e
            
        return tracks, next_page_token

    def rate_video(self, video_id, rating="like"):
        """
        Rates a video. rating must be 'like', 'dislike', or 'none'.
        """
        if not self.build_service():
            return False
            
        try:
            request = self.youtube.videos().rate(
                id=video_id,
                rating=rating
            )
            request.execute()
            return True
        except Exception as e:
            print(f"Error rating video {video_id}: {e}")
            return False

    def get_video_rating(self, video_id):
        if not self.build_service():
            return "none"
        try:
            request = self.youtube.videos().getRating(id=video_id)
            response = request.execute()
            items = response.get("items", [])
            if items:
                return items[0].get("rating", "none")
            return "none"
        except Exception as e:
            print(f"Error checking rating for {video_id}: {e}")
            return "none"

    def search(self, query, filter_type=None):
        """
        Performs a search on YouTube.
        filter_type: 'Songs', 'Videos', 'Albums', 'Community Playlists', 'Artists', or None (All)
        """
        if not self.build_service():
            return []

        search_type = 'video,playlist,channel'
        video_category_id = None
        q = query

        if filter_type == 'Songs':
            search_type = 'video'
            video_category_id = '10'  # Music
        elif filter_type == 'Videos':
            search_type = 'video'
        elif filter_type == 'Albums' or filter_type == 'Community Playlists':
            search_type = 'playlist'
        elif filter_type == 'Artists':
            search_type = 'channel'

        try:
            request = self.youtube.search().list(
                part="snippet",
                q=q,
                type=search_type,
                videoCategoryId=video_category_id,
                maxResults=25
            )
            response = request.execute()

            results = []
            video_ids = []
            temp_results = []

            for item in response.get('items', []):
                snippet = item['snippet']
                kind = item['id']['kind']
                
                result = {
                    "title": snippet['title'],
                    "author": snippet.get('channelTitle', 'Unknown'),
                    "thumbnail_url": snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                    "kind": kind,
                    "id": item['id'].get('videoId', item['id'].get('playlistId', item['id'].get('channelId'))),
                    "result_type": ""
                }

                if kind == 'youtube#video':
                    result["url"] = f"https://www.youtube.com/watch?v={result['id']}"
                    video_ids.append(result['id'])
                    result["duration"] = "0:00"
                    result["result_type"] = "Son." if filter_type == "Songs" else "Vid."
                elif kind == 'youtube#playlist':
                    result["url"] = f"https://www.youtube.com/playlist?list={result['id']}"
                    result["duration"] = "Playlist"
                    if filter_type == "Albums":
                         result["result_type"] = "Alb."
                    else:
                         result["result_type"] = "Pla."
                elif kind == 'youtube#channel':
                    result["url"] = f"https://www.youtube.com/channel/{result['id']}"
                    result["duration"] = "Artist"
                    result["result_type"] = "Art."

                temp_results.append(result)

            # Batch fetch durations and categories for videos
            if video_ids:
                dur_request = self.youtube.videos().list(
                    part="contentDetails,snippet",
                    id=",".join(video_ids)
                )
                dur_response = dur_request.execute()
                video_data = {}
                for v_item in dur_response.get('items', []):
                    v_id = v_item['id']
                    dur_str = v_item.get('contentDetails', {}).get('duration', '')
                    cat_id = v_item.get('snippet', {}).get('categoryId', '')
                    video_data[v_id] = {
                        "duration": parse_duration(dur_str),
                        "is_music": cat_id == '10'
                    }
                
                for res in temp_results:
                    if res['kind'] == 'youtube#video':
                        v_info = video_data.get(res['id'], {})
                        res['duration'] = v_info.get("duration", "0:00")
                        # If "All" was selected, refine Vid vs Son. based on category
                        if filter_type == None or filter_type == "All":
                            res['result_type'] = "Son." if v_info.get("is_music") else "Vid."
            
            return temp_results

        except Exception as e:
            print(f"Error performing search: {e}")
            return []

# Workers
class PlaylistLoaderWorker(QThread):
    playlists_loaded = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, youtube_api, parent=None):
        super().__init__(parent)
        self.youtube_api = youtube_api

    def run(self):
        try:
            data = self.youtube_api.get_user_playlists()
            self.playlists_loaded.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class PlaylistItemsWorker(QThread):
    chunk_loaded = Signal(list)
    items_loaded = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, youtube_api, playlist_id, parent=None):
        super().__init__(parent)
        self.youtube_api = youtube_api
        self.playlist_id = playlist_id

    def run(self):
        try:
            all_items = []
            next_token = None
            while True:
                items, next_token = self.youtube_api.get_playlist_items(self.playlist_id, next_token)
                if not items:
                    break
                self.chunk_loaded.emit(items)
                all_items.extend(items)
                if not next_token:
                    break
            self.items_loaded.emit(all_items)
        except Exception as e:
            self.error_occurred.emit(str(e))

class RatingFetchWorker(QThread):
    rating_fetched = Signal(str, str) # video_id, rating
    def __init__(self, youtube_api, video_id, parent=None):
        super().__init__(parent)
        self.youtube_api = youtube_api
        self.video_id = video_id
    def run(self):
        try:
            rating = self.youtube_api.get_video_rating(self.video_id)
            self.rating_fetched.emit(self.video_id, rating)
        except:
            self.rating_fetched.emit(self.video_id, "none")

class SearchWorker(QThread):
    results_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, youtube_api, query, filter_type=None, parent=None):
        super().__init__(parent)
        self.youtube_api = youtube_api
        self.query = query
        self.filter_type = filter_type

    def run(self):
        try:
            results = self.youtube_api.search(self.query, self.filter_type)
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))
