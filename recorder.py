"""
Audio recording receiver for MP3 Streamer
Handles audio data sent from browser and converts to MP3
"""
import subprocess
import os
from config import FFMPEG_PATH, UPLOAD_DIR

class AudioRecorder:
    def __init__(self):
        self.recording_active = False
    
    def save_recording(self, audio_data, filename):
        """
        Receive raw audio data from browser and convert to MP3.
        audio_data: raw WAV or audio bytes from browser
        filename: desired output filename
        """
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        
        filename_safe = os.path.basename(filename)
        output_path = os.path.join(UPLOAD_DIR, f"rec_{filename_safe}")
        
        try:
            # Save temporary WAV file
            temp_wav = os.path.join(UPLOAD_DIR, "temp_recording.wav")
            with open(temp_wav, 'wb') as f:
                f.write(audio_data)
            
            # Convert WAV to MP3 with 48kbps mono
            subprocess.run([
                FFMPEG_PATH,
                "-i", temp_wav,
                "-ac", "1",              # Mono
                "-ar", "22050",          # Sample rate
                "-b:a", "48k",           # 48 kbps bitrate
                "-y",                    # Overwrite
                output_path
            ], capture_output=True, check=True)
            
            # Clean up temp file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Recording saved: {output_path} ({file_size} bytes)")
                return True, f"Recording saved as '{filename_safe}'"
            else:
                return False, "Failed to create MP3 file"
        
        except Exception as e:
            print(f"Recording Error: {e}")
            # Clean up temp file on error
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            return False, f"Error saving recording: {str(e)}"

# Global recorder instance
recorder = AudioRecorder()