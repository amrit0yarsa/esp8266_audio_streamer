"""
HTTP request handler for ESP8266 Jukebox
"""
import http.server
import os
import shutil
import json
import urllib.parse
from email.parser import Parser
from io import BytesIO
from config import UPLOAD_DIR, CHUNK_SIZE, FFMPEG_PATH
import config
from mqtt_client import mqtt_manager
from templates import generate_html_page

import subprocess

class MP3StreamerHandler(http.server.SimpleHTTPRequestHandler):
    
    def handle_audio_stream(self):
        """Stream audio file to client."""
        current_path = config.CURRENT_TRACK
        if not current_path or not os.path.exists(current_path):
            self.send_response(404)
            self.end_headers()
            print("Streamer: No track selected or file not found. Closing connection.")
            return

        f = None
        try:
            f = open(current_path, 'rb')
            file_size = os.path.getsize(current_path)

            self.send_response(200)
            self.send_header('Content-type', 'audio/mp3')
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except BrokenPipeError:
                    print(f"Streamer: Client disconnected abruptly while streaming '{current_path}'.")
                    break

            print(f"Streamer: Finished streaming '{current_path}' (ID: {config.STREAM_ID}).")

        except ConnectionResetError:
            print(f"Streamer: Client disconnected while streaming '{current_path}' (ID: {config.STREAM_ID}).")
        except Exception as e:
            print(f"Streamer Error: {e}")
        finally:
            if f:
                f.close()
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/stream':
            self.handle_audio_stream()
            return

        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            track_name = os.path.basename(config.CURRENT_TRACK) if config.CURRENT_TRACK else "None"
            response = {
                "currentTrack": track_name,
                "streamId": config.STREAM_ID
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        if self.path == '/' or self.path == '/list':
            self.send_html_page()
            return
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        """Handle POST requests."""
        # Play Track
        if self.path.startswith('/play'):
            params = urllib.parse.parse_qs(self.path.split('?', 1)[1])
            filename = params.get('file', [''])[0]
            track_path = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(track_path):
                mqtt_manager.update_state(track_path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK: Play started.')
            else:
                self.send_error(404, 'File not found.')
            return

        # Stop/Clear Selection
        if self.path == '/stop':
            mqtt_manager.update_state(None)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK: Selection cleared.')
            return
            
        # Handle File Upload
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    # Extract boundary
                    boundary = content_type.split('boundary=')[1].strip()
                    boundary_bytes = ('--' + boundary).encode()
                    end_boundary = ('--' + boundary + '--').encode()
                    
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length)
                    
                    # Parse multipart data
                    parts = body.split(boundary_bytes)
                    
                    for part in parts:
                        if b'Content-Disposition' in part and b'filename=' in part:
                            # Extract filename
                            lines = part.split(b'\r\n')
                            for line in lines:
                                if b'Content-Disposition' in line:
                                    disposition = line.decode('utf-8', errors='ignore')
                                    if 'filename=' in disposition:
                                        filename = disposition.split('filename=')[1].strip().strip('"')
                                        filename_safe = os.path.basename(filename)
                                        
                                        # Find file data (after headers)
                                        data_start = part.find(b'\r\n\r\n') + 4
                                        data_end = part.rfind(b'\r\n')
                                        file_data = part[data_start:data_end]
                                        
                                        # Save uploaded file
                                        filepath = os.path.join(UPLOAD_DIR, filename_safe)
                                        with open(filepath, 'wb') as f:
                                            f.write(file_data)
                                        
                                        # --- OPTIMIZE MP3 to 64 kbps MONO ---
                                        optimized_path = os.path.join(UPLOAD_DIR, f"opt_{filename_safe}")
                                        try:
                                            subprocess.run([
                                                FFMPEG_PATH,
                                                "-y",               # overwrite
                                                "-i", filepath,     # input file
                                                "-ac", "1",         # mono
                                                "-ar", "22050",     # sample rate
                                                "-b:a", "64k",      # 64 kbps bitrate
                                                optimized_path
                                            ], check=True)

                                            # Replace original with optimized
                                            os.remove(filepath)
                                            os.rename(optimized_path, filepath)
                                            print(f"Upload optimized to 64kbps: {filepath}")

                                        except Exception as e:
                                            print(f"FFmpeg conversion failed: {e}")
                                        
                                        self.send_response(200)
                                        self.end_headers()
                                        self.wfile.write(json.dumps({"success": True, "filename": filename_safe}).encode('utf-8'))
                                        return
                        
            except Exception as e:
                print(f"Upload error: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return
            
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "No file selected or invalid request."}).encode('utf-8'))
            return
            
        # Handle File Delete
        if self.path.startswith('/delete'):
            params = urllib.parse.parse_qs(self.path.split('?', 1)[1])
            filename = params.get('file', [''])[0]
            track_path = os.path.join(UPLOAD_DIR, filename)

            if os.path.exists(track_path):
                if config.CURRENT_TRACK == track_path:
                    mqtt_manager.update_state(None)
                
                os.remove(track_path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK: File deleted.')
            else:
                self.send_error(404, 'File not found.')
            return

        self.send_error(404, 'Unknown POST endpoint.')

    def send_html_page(self):
        """Send the HTML page to the client."""
        html_content = generate_html_page(config.CURRENT_TRACK)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))