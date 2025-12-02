"""
HTTP request handler for ESP8266 Jukebox
"""
import http.server
import os
import cgi
import shutil
import json
import urllib.parse
from config import UPLOAD_DIR, CHUNK_SIZE
import config
from mqtt_client import mqtt_manager
from templates import generate_html_page

class JukeboxHandler(http.server.SimpleHTTPRequestHandler):
    
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
                ctype, pdict = cgi.parse_header(self.headers['content-type'])
                if ctype == 'multipart/form-data':
                    pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
                    content_length = int(self.headers.get('Content-Length', 0))
                    environ = {
                        'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type'],
                        'CONTENT_LENGTH': str(content_length)
                    }
                               
                    form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
                    fileitem = form['file']
                    
                    if fileitem.filename:
                        filename_safe = os.path.basename(fileitem.filename)
                        filepath = os.path.join(UPLOAD_DIR, filename_safe)
                        with open(filepath, 'wb') as f:
                            shutil.copyfileobj(fileitem.file, f)
                        
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, "filename": filename_safe}).encode('utf-8'))
                        return
                        
            except Exception as e:
                print(f"Upload error: {e}")
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