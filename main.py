#!/usr/bin/env python3
"""
ESP8266 Jukebox DJ - Main Server
"""
import socketserver
import os
from config import PORT, HOST, UPLOAD_DIR
import config
from mqtt_client import mqtt_manager
from handler import JukeboxHandler
from utils import get_local_ip

class ThreadingSimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threading server to handle multiple simultaneous connections."""
    allow_reuse_address = True
    daemon_threads = True

def main():
    """Main entry point for the server."""
    # Ensure upload directory exists
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    # Connect to MQTT broker
    mqtt_manager.connect()
    
    # Initialize server
    socketserver.TCPServer.allow_reuse_address = True
    
    with ThreadingSimpleServer((HOST, PORT), JukeboxHandler) as httpd:
        print(f"--- ESP8266 DJ Station (MQTT Control) ---")
        print(f"1. Put MP3s in the '{UPLOAD_DIR}' folder OR upload via web.")
        print(f"2. Web UI: http://{get_local_ip()}:{PORT}")
        print(f"3. MQTT Broker: {config.MQTT_BROKER_IP}:{config.MQTT_PORT} | Topic: {config.MQTT_TOPIC}")
        print("-" * 50)
        
        # Initialize state
        mqtt_manager.update_state(config.CURRENT_TRACK)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            mqtt_manager.disconnect()

if __name__ == '__main__':
    main()