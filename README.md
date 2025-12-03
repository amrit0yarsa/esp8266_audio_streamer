# ESP8266 MP3 Streamer

A simple HTTP server for streaming MP3 audio to ESP8266 devices and other clients. Upload music, control playback, and record audio through a web interface.

## Quick Start

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Install FFmpeg** - Download from https://ffmpeg.org/download.html

3. **Run server:**
   ```powershell
   python main.py
   ```

4. **Open browser:**
   ```
   http://localhost:8080
   ```



---

## Features

- 📁 Upload and manage MP3 files
- 🎵 Stream audio via HTTP
- 🎙️ Record audio from browser
- 📱 MQTT control for IoT devices
- 🌐 Web-based UI
- 🔄 Auto-converts any audio format to MP3  



---

## Configuration

Edit `config.py`:

```python
PORT = 8080                          # Server port
HOST = '0.0.0.0'                     # Bind address
MQTT_BROKER_IP = "broker.emqx.io"    # MQTT broker
FFMPEG_PATH = "./ffmpeg"             # FFmpeg location
```

Or use environment variables:
```powershell
$env:PORT = "9000"
$env:MQTT_BROKER = "192.168.1.50"
```



---

## Usage

### Web Interface
1. **Upload** - Add MP3 or other audio formats (auto-converts)
2. **Play** - Click a track to stream it
3. **Record** - Capture audio from microphone
4. **Delete** - Remove tracks
5. **Status** - See current track and stream ID

### Stream for Devices
```
http://<server-ip>:8080/stream
```

⚠️ **Use HTTP only (no HTTPS/SSL)**



---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/stream` | Get audio stream (HTTP only!) |
| GET | `/status` | Get current track info |
| POST | `/play?file=name` | Select a track |
| POST | `/stop` | Stop playback |
| POST | `/upload` | Upload audio file |
| POST | `/delete?file=name` | Delete file |
| POST | `/record/save?name=rec` | Save recording |



---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Server won't start | Check port 8080 not in use: `$env:PORT = "9000"` |
| FFmpeg error | Install FFmpeg, update `FFMPEG_PATH` in `config.py` |
| Audio won't stream | **Use HTTP, not HTTPS** ⚠️ / Check network: `Test-NetConnection -ComputerName <ip> -Port 8080` |
| Upload fails | Check `mp3s/` permissions, disk space |
| MQTT connection fails | Check broker IP/port, try `broker.emqx.io:1883` |


---

## ESP8266 Example

```cpp
HTTPClient http;
http.begin("http://<server-ip>:8080/stream");  // HTTP only!
int code = http.GET();
if (code == 200) {
  while (http.connected()) {
    uint8_t buffer[2048];
    size_t size = http.getStream().readBytes(buffer, sizeof(buffer));
    // Play audio...
  }
}
```

---

## File Structure

```
esp8266MP3Streamer/
├── main.py           # Server entry point
├── handler.py        # HTTP request handler
├── streamer.py       # Audio streaming
├── recorder.py       # Audio recording
├── mqtt_client.py    # MQTT connection
├── templates.py      # Web UI
├── config.py         # Configuration
├── utils.py          # Utilities
├── mp3s/             # MP3 files
└── requirements.txt  # Dependencies
```

---

## Tips

- Place MP3s directly in `mp3s/` folder
- Auto-converts to 48kbps mono MP3
- Multiple clients can stream at once
- Stream ID increments each track change

**Need help?** Check console output for error details.
