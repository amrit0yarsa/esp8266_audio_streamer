"""
HTML template generation for MP3 Streamer web interface - UPDATED WITH RECORDING.
"""
import os
from config import UPLOAD_DIR
from utils import escape_html

def generate_html_page(current_track):
    """Generate the web interface HTML."""
    current_filename = os.path.basename(current_track) if current_track else None
    
    files_html = "".join([
        f"""
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition duration-150 ease-in-out">
            <span class="text-gray-800 font-medium text-lg truncate pr-4">{escape_html(f)}</span>
            <div class="flex space-x-2 flex-shrink-0">
                {'<button class="stop-btn bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-full shadow-md transition duration-150 ease-in-out" onclick="controlAction(\'/stop\')"><i class="fas fa-stop mr-2"></i>Stop</button>' if f == current_filename else f'<button class="play-btn bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-full shadow-md transition duration-150 ease-in-out" onclick="controlAction(\'/play\', \'{escape_html(f)}\')"><i class="fas fa-play mr-2"></i>Play</button>'}
                <button class="delete-btn bg-gray-400 hover:bg-gray-500 text-white font-semibold py-2 px-4 rounded-full shadow-md transition duration-150 ease-in-out" onclick="controlAction(\'/delete\', \'{escape_html(f)}\')"><i class="fas fa-trash-alt"></i></button>
            </div>
        </div>
        """
        for f in os.listdir(UPLOAD_DIR) if f.endswith(".mp3")
    ])

    initial_track_display = 'None' if not current_filename else current_filename
    initial_status_class = "bg-yellow-50 border-yellow-500 text-yellow-700" if not current_filename else "bg-green-50 border-green-500 text-green-700"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Yarsa MP3 Streamer</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {{
                background-color: #f3f4f6;
                font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
            }}
            .recording-pulse {{
                animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
        </style>
    </head>
    <body class="p-4 sm:p-8">
        <div class="max-w-3xl mx-auto bg-white p-6 md:p-10 rounded-xl shadow-2xl space-y-8">
            
            <header class="text-center border-b pb-4">
                <h1 class="text-4xl font-extrabold text-blue-600 tracking-tight flex items-center justify-center space-x-3">
                    <i class="fas fa-wifi"></i> <span>Yarsa MP3 Streamer</span>
                </h1>
            </header>
            
            <div id="current-track-status" 
                 class="p-4 rounded-lg text-center font-bold text-lg border-2 {initial_status_class}"
                 data-current-track="{initial_track_display}">
                Current Track: <strong>{initial_track_display}</strong>
            </div>

            <section class="space-y-4">
                <h2 class="text-2xl font-semibold text-gray-700 border-l-4 border-blue-500 pl-3">
                    <i class="fas fa-list-music mr-2"></i> Track List ({len(os.listdir(UPLOAD_DIR))} total)
                </h2>
                <div class="track-list space-y-2">
                    {files_html}
                </div>
            </section>

            <section class="space-y-4 pt-4 border-t border-gray-200">
                <h2 class="text-2xl font-semibold text-gray-700 border-l-4 border-blue-500 pl-3">
                    <i class="fas fa-microphone mr-2"></i> Record Audio
                </h2>
                <div class="p-4 bg-gray-50 rounded-lg shadow-inner space-y-3">
                    <input type="text" id="recordingName" placeholder="Enter recording name (optional)" class="block w-full px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                    <button id="recordButton" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-lg shadow-md transition duration-150 ease-in-out flex items-center justify-center space-x-2">
                        <i class="fas fa-circle"></i>
                        <span id="recordButtonText">Start Recording</span>
                    </button>
                    <p id="recordingStatus" class="text-sm text-gray-500 text-center hidden">Recording in progress...</p>
                </div>
            </section>

            <section class="space-y-4 pt-4 border-t border-gray-200">
                <h2 class="text-2xl font-semibold text-gray-700 border-l-4 border-blue-500 pl-3">
                    <i class="fas fa-cloud-upload-alt mr-2"></i> Upload MP3
                </h2>
                <form id="uploadForm" onsubmit="handleUpload(event)" class="flex flex-col space-y-3 p-4 bg-gray-50 rounded-lg shadow-inner" enctype="multipart/form-data">
                    <input type="file" name="file" id="fileInput" accept="audio/mp3" required class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer">
                    <button type="submit" id="uploadButton" class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg shadow-md transition duration-150 ease-in-out">
                        <i class="fas fa-upload mr-2"></i> Upload File
                    </button>
                </form>
            </section>
            
        </div>
        
        <div id="modalOverlay" class="fixed inset-0 bg-gray-600 bg-opacity-75 hidden items-center justify-center z-50 transition-opacity duration-300">
            <div id="modalContent" class="bg-white rounded-lg shadow-2xl p-6 w-96 transform scale-95 transition-transform duration-300">
                <h3 id="modalTitle" class="text-xl font-bold mb-4"></h3>
                <p id="modalMessage" class="text-gray-600 mb-6"></p>
                <button id="modalCloseButton" class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 font-semibold" onclick="hideModal()">Close</button>
            </div>
        </div>

        <script>
            let isRecording = false;
            let mediaRecorder = null;
            let audioChunks = [];
            let audioStream = null;

            function showModal(title, message, isSuccess) {{
                const overlay = document.getElementById('modalOverlay');
                const content = document.getElementById('modalContent');
                const titleElement = document.getElementById('modalTitle');
                const closeButton = document.getElementById('modalCloseButton');

                titleElement.innerText = title;
                document.getElementById('modalMessage').innerHTML = message;

                if (isSuccess) {{
                    titleElement.className = 'text-xl font-bold mb-4 text-green-600';
                    closeButton.className = 'w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 font-semibold';
                }} else {{
                    titleElement.className = 'text-xl font-bold mb-4 text-red-600';
                    closeButton.className = 'w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 font-semibold';
                }}

                overlay.classList.remove('hidden');
                overlay.classList.add('flex');
                setTimeout(() => content.classList.add('scale-100'), 10);
            }}

            function hideModal() {{
                const overlay = document.getElementById('modalOverlay');
                const content = document.getElementById('modalContent');
                content.classList.remove('scale-100');
                setTimeout(() => {{
                    overlay.classList.remove('flex');
                    overlay.classList.add('hidden');
                    window.location.reload(); 
                }}, 300);
            }}

            async function handleRecordButton() {{
                const recordButton = document.getElementById('recordButton');
                const recordingStatus = document.getElementById('recordingStatus');
                const recordingName = document.getElementById('recordingName');
                const recordButtonText = document.getElementById('recordButtonText');

                if (!isRecording) {{
                    // Start Recording
                    try {{
                        audioStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        mediaRecorder = new MediaRecorder(audioStream);
                        audioChunks = [];

                        mediaRecorder.ondataavailable = (event) => {{
                            audioChunks.push(event.data);
                        }};

                        mediaRecorder.start();
                        isRecording = true;

                        recordButton.classList.add('recording-pulse');
                        recordButton.classList.remove('bg-red-600', 'hover:bg-red-700');
                        recordButton.classList.add('bg-red-800');
                        recordButtonText.innerHTML = '<i class="fas fa-stop-circle"></i> <span>Stop Recording</span>';
                        recordingStatus.classList.remove('hidden');
                        recordingName.disabled = true;
                    }} catch (error) {{
                        console.error('Microphone access error:', error);
                        showModal('Microphone Error', 'Unable to access microphone. Please check permissions.', false);
                    }}
                }} else {{
                    // Stop Recording
                    mediaRecorder.stop();
                    recordButton.disabled = true;
                    recordButtonText.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> <span>Saving...</span>';

                    mediaRecorder.onstop = async () => {{
                        try {{
                            const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                            const filename = recordingName.value.trim() || 'recording_' + Date.now();

                            const formData = new FormData();
                            formData.append('audio', audioBlob);

                            const response = await fetch(`/record/save?name=${{encodeURIComponent(filename)}}`, {{
                                method: 'POST',
                                body: audioBlob
                            }});

                            const result = await response.json();

                            if (result.success) {{
                                isRecording = false;
                                recordButton.classList.remove('recording-pulse');
                                recordButton.classList.add('bg-red-600', 'hover:bg-red-700');
                                recordButton.classList.remove('bg-red-800');
                                recordButtonText.innerHTML = '<i class="fas fa-circle"></i> <span>Start Recording</span>';
                                recordingStatus.classList.add('hidden');
                                recordingName.disabled = false;
                                recordingName.value = '';
                                
                                // Stop audio stream
                                audioStream.getTracks().forEach(track => track.stop());
                                
                                showModal('Recording Saved', result.message, true);
                            }} else {{
                                showModal('Save Failed', result.message, false);
                            }}
                        }} catch (error) {{
                            console.error('Error:', error);
                            showModal('Recording Error', 'Failed to save recording: ' + error.message, false);
                        }} finally {{
                            recordButton.disabled = false;
                            recordButtonText.innerHTML = '<i class="fas fa-circle"></i> <span>Start Recording</span>';
                        }}
                    }};
                }}
            }}

            async function handleUpload(event) {{
                event.preventDefault(); 

                const form = document.getElementById('uploadForm');
                const button = document.getElementById('uploadButton');
                const fileInput = document.getElementById('fileInput');

                if (fileInput.files.length === 0) return;

                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Uploading...';
                
                const formData = new FormData(form);

                try {{
                    const response = await fetch('/upload', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const result = await response.json();

                    if (response.ok && result.success) {{
                        showModal('Upload Successful!', `File <strong>${{result.filename}}</strong> has been uploaded.`, true);
                    }} else {{
                        showModal('Upload Failed!', `Error: ${{result.error || 'Unknown server error.'}}`, false);
                    }}
                }} catch (error) {{
                    console.error('Network Error:', error);
                    showModal('Upload Failed!', `A network error occurred: ${{error.message}}`, false);
                }} finally {{
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-upload mr-2"></i> Upload File';
                    fileInput.value = '';
                }}
            }}

            function updateStatus() {{
                fetch('/status')
                .then(response => response.json())
                .then(data => {{
                    const statusElement = document.getElementById('current-track-status');
                    const isPlaying = data.currentTrack !== 'None';
                    
                    statusElement.innerHTML = `Current Track: <strong>${{data.currentTrack}}</strong>`;
                    
                    const baseClasses = 'p-4 rounded-lg text-center font-bold text-lg border-2';
                    if (isPlaying) {{
                        statusElement.className = `${{baseClasses}} bg-green-50 border-green-500 text-green-700`;
                    }} else {{
                        statusElement.className = `${{baseClasses}} bg-yellow-50 border-yellow-500 text-yellow-700`;
                    }}

                    const currentTrackName = statusElement.getAttribute('data-current-track');
                    
                    if (currentTrackName != data.currentTrack) {{
                        statusElement.setAttribute('data-current-track', data.currentTrack);
                        window.location.reload(); 
                    }}
                }})
                .catch(error => console.error('Error fetching status:', error));
            }}

            function controlAction(endpoint, filename = null) {{
                let url = endpoint;
                if (filename) {{
                    url += `?file=${{encodeURIComponent(filename)}}`;
                }}
                fetch(url, {{method: 'POST'}})
                .then(response => response.text())
                .then(text => {{
                    console.log(text);
                    window.location.reload(); 
                }})
                .catch(error => console.error('Error during control action:', error));
            }}

            document.getElementById('recordButton').addEventListener('click', handleRecordButton);

            window.addEventListener('load', () => {{
                updateStatus();
                setInterval(updateStatus, 2000); 
            }});
        </script>
    </body>
    </html>
    """