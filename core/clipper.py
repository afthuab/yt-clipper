import subprocess
import os
import threading

class Clipper:
    """Handles video clipping using FFmpeg."""

    def clip(self, input_path, output_path, start_time, end_time, output_format, progress_callback):
        """Clips the video/audio using FFmpeg in a separate thread."""
        def clip_in_thread():
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                if output_format == "MP4":
                    command = [
                        'ffmpeg', '-y', '-i', input_path, '-ss', start_time, '-to', end_time,
                        '-c', 'copy', '-avoid_negative_ts', '1', output_path
                    ]
                elif output_format == "MP3":
                    command = [
                        'ffmpeg', '-y', '-i', input_path, '-ss', start_time, '-to', end_time,
                        '-vn', '-q:a', '0', '-map', 'a', output_path
                    ]
                elif output_format == "GIF":
                    command = [
                        'ffmpeg', '-y', '-i', input_path, '-ss', start_time, '-to', end_time,
                        '-vf', 'fps=15,scale=480:-1:flags=lanczos', '-c', 'gif', output_path
                    ]
                else:
                    raise ValueError("Unsupported format")

                progress_callback({'status': 'clipping', 'message': f'Running FFmpeg for {output_format}...'})
                
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    progress_callback({'status': 'finished', 'message': f'Successfully created clip: {os.path.basename(output_path)}'})
                else:
                    progress_callback({'status': 'error', 'message': f'FFmpeg error: {stderr}'})

            except FileNotFoundError:
                progress_callback({'status': 'error', 'message': 'ffmpeg not found. Please ensure it is installed and in your system PATH.'})
            except Exception as e:
                progress_callback({'status': 'error', 'message': str(e)})
            finally:
                if os.path.exists(input_path):
                    try:
                        os.remove(input_path)
                    except OSError as e:
                        print(f"Error removing temporary file {input_path}: {e}")
        
        thread = threading.Thread(target=clip_in_thread)
        thread.start()