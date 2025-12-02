"""
MQTT client management for MP3 Streamer
"""
import paho.mqtt.client as mqtt
from config import MQTT_BROKER_IP, MQTT_PORT, MQTT_TOPIC
import config

class MQTTManager:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            self.connected = True
            print(f"MQTT: Connected successfully to broker at {MQTT_BROKER_IP}:{MQTT_PORT}")
        else:
            print(f"MQTT: Connection failed with code {rc}. Trying to reconnect...")
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT Error: Could not connect to broker. Check your network: {e}")
    
    def publish_stream_id(self, stream_id):
        """Publish stream ID to MQTT topic."""
        payload = str(stream_id)
        self.client.publish(MQTT_TOPIC, payload, qos=0, retain=True)
        print(f"MQTT: Published ID {stream_id} to topic '{MQTT_TOPIC}'")
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        
    def update_state(self, track_path):
        """Update global state and notify via MQTT."""
        config.CURRENT_TRACK = track_path
        config.STREAM_ID += 1
        
        self.publish_stream_id(config.STREAM_ID)
        
        print(f"State Updated: Track={config.CURRENT_TRACK}, New ID={config.STREAM_ID}")

# Global MQTT manager instance
mqtt_manager = MQTTManager()