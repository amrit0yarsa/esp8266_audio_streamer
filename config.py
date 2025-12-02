"""
Configuration settings for ESP8266 Jukebox
"""
import os

# Server Configuration
PORT = int(os.environ.get('PORT', 8080))
HOST = os.environ.get('HOST', '0.0.0.0')
UPLOAD_DIR = "mp3s"
CHUNK_SIZE = 2048

# MQTT Configuration
MQTT_BROKER_IP = os.environ.get('MQTT_BROKER', "broker.emqx.io")
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_TOPIC = "jukebox/control/stream_id"

# Global State
CURRENT_TRACK = None
STREAM_ID = 0