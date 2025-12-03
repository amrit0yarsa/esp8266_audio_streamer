"""
HTTP request handler for ESP8266 Jukebox - UPDATED WITH RECORDING
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
from recorder import recorder

import re

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
        
        # Save Recording (receive audio from browser)
        if self.path.startswith('/record/save'):
            params = urllib.parse.parse_qs(self.path.split('?', 1)[1])
            filename = params.get('name', ['recording'])[0]
            
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                audio_data = self.rfile.read(content_length)
                
                success, message = recorder.save_recording(audio_data, filename)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": success,
                    "message": message
                }).encode('utf-8'))
            except Exception as e:
                print(f"Save recording error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": f"Error: {str(e)}"
                }).encode('utf-8'))
            return
            
        # Handle File Upload
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    # Extract boundary
                    boundary = content_type.split('boundary=')[1].strip()
                    boundary_bytes = ('--' + boundary).encode()
                    # Parsing multipart body
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length)
                    
                    parts = body.split(boundary_bytes)
                    
                    for part in parts:
                        if b'Content-Disposition' in part and b'filename=' in part:
                            # Extract filename
                            lines = part.split(b'\r\n')
                            for line in lines:
                                if b'Content-Disposition' in line:
                                    disposition = line.decode('utf-8', errors='ignore')
                                    if 'filename=' in disposition:
                                        original_filename = disposition.split('filename=')[1].strip().strip('"')
                                        
                                        # --- FILENAME SANITIZATION START ---
                                        # Split name and extension
                                        base_name, original_ext = os.path.splitext(original_filename)
                                        if not original_ext:
                                            original_ext = "" # Handle files without extension
                                            
                                        # Replace special chars with space, keep alphanumeric
                                        sanitized_base = re.sub(r'[^a-zA-Z0-9]', ' ', base_name)
                                        # Remove double spaces and strip
                                        sanitized_base = re.sub(r'\s+', ' ', sanitized_base).strip()
                                        
                                        # Fallback if filename becomes empty
                                        if not sanitized_base:
                                            sanitized_base = "uploaded_track"

                                        # Create new filename with .mp3 extension
                                        filename_safe = f"{sanitized_base}.mp3"
                                        # --- FILENAME SANITIZATION END ---

                                        # Find file data (after headers)
                                        data_start = part.find(b'\r\n\r\n') + 4
                                        data_end = part.rfind(b'\r\n')
                                        file_data = part[data_start:data_end]
                                        
                                        # Save TEMP file (with original extension to help ffmpeg detect format)
                                        temp_filename = f"temp_{original_filename}"
                                        temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)
                                        
                                        with open(temp_filepath, 'wb') as f:
                                            f.write(file_data)
                                        
                                        # Define Final MP3 Path
                                        final_mp3_path = os.path.join(UPLOAD_DIR, filename_safe)

                                        # --- CONVERT ANY FORMAT TO MP3 (64 kbps MONO) ---
                                        try:
                                            print(f"Converting {temp_filepath} to {final_mp3_path}...")
                                            subprocess.run([
                                                FFMPEG_PATH,
                                                "-y",               # overwrite if exists
                                                "-i", temp_filepath,# input file (any format)
                                                "-ac", "1",         # mono
                                                "-ar", "22050",     # sample rate
                                                "-b:a", "64k",      # 64 kbps bitrate
                                                "-f", "mp3",        # Force mp3 format
                                                final_mp3_path
                                            ], check=True)

                                            print(f"Conversion successful: {final_mp3_path}")
                                            
                                            # Clean up temp file
                                            if os.path.exists(temp_filepath):
                                                os.remove(temp_filepath)

                                        except Exception as e:
                                            print(f"FFmpeg conversion failed: {e}")
                                            # Clean up temp file on failure
                                            if os.path.exists(temp_filepath):
                                                os.remove(temp_filepath)
                                            raise e # Re-raise to send error response
                                        
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