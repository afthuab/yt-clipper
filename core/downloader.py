import yt_dlp
import os
import threading

class Downloader:
    """Handles fetching metadata and downloading YouTube videos using yt-dlp."""

    def __init__(self, progress_hook=None):
        self.progress_hook = progress_hook

    def fetch_video_info(self, url):
        """Fetches video metadata without downloading the video."""
        ydl_opts = {'noplaylist': True, 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'N/A'),
                    'duration': info.get('duration', 0),
                    'thumbnail_url': info.get('thumbnail', None)
                }
        except yt_dlp.utils.DownloadError as e:
            print(f"Error fetching video info: {e}")
            return None

    def download_video(self, url, output_path):
        """Downloads the best quality video and audio to the specified path."""
        self.stop_download = False
        
        def download_in_thread():
            temp_filename = "downloaded_video"
            temp_filepath = os.path.join(output_path, temp_filename)
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': temp_filepath,
                'noplaylist': True,
                'progress_hooks': [self._on_progress],
                'noprogress': True,
                'quiet': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    
                # Find the actual downloaded file name
                for file in os.listdir(output_path):
                    if file.startswith(temp_filename):
                        actual_filepath = os.path.join(output_path, file)
                        if self.progress_hook:
                             self.progress_hook({'status': 'finished_download', 'filepath': actual_filepath})
                        return

                if self.progress_hook:
                    self.progress_hook({'status': 'error', 'error': 'Downloaded file not found.'})

            except Exception as e:
                if "Interrupted by user" not in str(e):
                    if self.progress_hook:
                        self.progress_hook({'status': 'error', 'error': str(e)})

        thread = threading.Thread(target=download_in_thread)
        thread.start()

    def _on_progress(self, d):
        """Callback for yt-dlp progress updates."""
        if self.stop_download:
             raise yt_dlp.utils.DownloadError("Interrupted by user")

        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                percent = (downloaded_bytes / total_bytes) * 100
                if self.progress_hook:
                    self.progress_hook({
                        'status': 'downloading',
                        'percent': percent,
                        'total_bytes': total_bytes
                    })

    def cancel_download(self):
        self.stop_download = True