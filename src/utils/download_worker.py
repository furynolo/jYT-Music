from PySide6.QtCore import QThread, Signal
import yt_dlp
import os

class DownloadWorker(QThread):
    download_finished = Signal(str, bool) # filepath or message, success

    def __init__(self, target_url, output_dir, parent=None):
        super().__init__(parent)
        self.target_url = target_url
        self.output_dir = output_dir

    def run(self):
        if not self.output_dir:
            self.download_finished.emit("No local directory configured. Please browse a local folder first.", False)
            return

        try:
            ffmpeg_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'bin'))
            ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            if os.path.exists(ffmpeg_exe):
                ydl_opts['ffmpeg_location'] = ffmpeg_dir
            else:
                # Let yt-dlp find it in the system PATH
                pass
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.target_url, download=True)
                download_path = os.path.join(self.output_dir, f"{info['title']}.mp3")
                
            self.download_finished.emit(f"Downloaded: {info['title']}", True)
        except Exception as e:
            err_msg = str(e)
            if "ffmpeg not found" in err_msg.lower():
                err_msg += "\n(Please install FFmpeg and add it to your system PATH to enable downloads.)"
            self.download_finished.emit(err_msg, False)
        except BaseException as e:
            self.download_finished.emit(f"Fatal error during download: {str(e)}", False)
