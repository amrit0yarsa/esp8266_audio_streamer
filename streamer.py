"""
Real-time audio streaming manager with MP3 encoding
"""
import threading
import queue
import subprocess
import os
from config import FFMPEG_PATH, UPLOAD_DIR
from datetime import datetime

class AudioStreamer:
    def __init__(self):
        self.is_streaming = False
        self.stream_queue = queue.Queue()
        self.clients = []
        self.lock = threading.Lock()
        self.stream_id = 0
        self.stream_name = ""
        self.ffmpeg_process = None
        self.temp_wav_file = None
    
    def start_stream(self, stream_name):
        """Start a new real-time stream with MP3 encoding."""
        with self.lock:
            if self.is_streaming:
                return False, "Already streaming"
            
            self.is_streaming = True
            self.stream_id += 1
            self.stream_name = stream_name
            self.stream_queue = queue.Queue()
            self.clients = []
            
            # Start FFmpeg process to encode WAV to MP3
            self.temp_wav_file = os.path.join(UPLOAD_DIR, "stream_input.wav")
            mp3_output = "pipe:1"  # Output to stdout
            
            try:
                self.ffmpeg_process = subprocess.Popen([
                    FFMPEG_PATH,
                    "-f", "wav",
                    "-i", self.temp_wav_file,
                    "-ac", "1",           # Mono
                    "-ar", "22050",       # Sample rate
                    "-b:a", "48k",        # 48 kbps bitrate
                    "-f", "mp3",
                    "-loglevel", "error",
                    mp3_output
                ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                print(f"Stream started: {stream_name} (ID: {self.stream_id})")
                return True, f"Stream '{stream_name}' started"
            except Exception as e:
                print(f"FFmpeg error: {e}")
                self.is_streaming = False
                return False, f"Failed to start FFmpeg: {str(e)}"
    
    def add_stream_client(self):
        """Register a client listening to the stream."""
        with self.lock:
            if not self.is_streaming:
                return None
            
            client_queue = queue.Queue()
            self.clients.append(client_queue)
            print(f"Stream client connected (Total: {len(self.clients)})")
            return client_queue
    
    def push_audio_chunk(self, chunk):
        """Push audio chunk for MP3 encoding."""
        with self.lock:
            if not self.is_streaming or not self.ffmpeg_process:
                return
            
            try:
                # Write WAV data to FFmpeg stdin
                self.ffmpeg_process.stdin.write(chunk)
                self.ffmpeg_process.stdin.flush()
                
                # Read MP3 output from FFmpeg stdout
                try:
                    mp3_chunk = self.ffmpeg_process.stdout.read(4096)
                    if mp3_chunk:
                        # Send MP3 chunk to all connected clients
                        for client_queue in self.clients:
                            try:
                                client_queue.put_nowait(mp3_chunk)
                            except queue.Full:
                                pass
                except:
                    pass
            except Exception as e:
                print(f"Stream push error: {e}")
    
    def stop_stream(self):
        """Stop the current stream."""
        with self.lock:
            if not self.is_streaming:
                return False, "Not streaming"
            
            self.is_streaming = False
            stream_name = self.stream_name
            
            # Close FFmpeg process
            try:
                if self.ffmpeg_process:
                    self.ffmpeg_process.stdin.close()
                    self.ffmpeg_process.wait(timeout=2)
                    self.ffmpeg_process = None
            except:
                pass
            
            # Clean up temp file
            if self.temp_wav_file and os.path.exists(self.temp_wav_file):
                try:
                    os.remove(self.temp_wav_file)
                except:
                    pass
            
            # Send end-of-stream marker to all clients
            for client_queue in self.clients:
                try:
                    client_queue.put_nowait(None)  # None signals end of stream
                except queue.Full:
                    pass
            
            print(f"Stream stopped: {stream_name}")
            return True, f"Stream '{stream_name}' ended"
    
    def get_stream_status(self):
        """Get current stream status."""
        with self.lock:
            return {
                "is_streaming": self.is_streaming,
                "stream_id": self.stream_id,
                "stream_name": self.stream_name,
                "client_count": len(self.clients)
            }

# Global streamer instance
audio_streamer = AudioStreamer()