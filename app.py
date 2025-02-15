import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
import whisper
from flask_cors import CORS
import torch
import multiprocessing
from flask_socketio import SocketIO, emit

# Set environment variables to prevent OMP and semaphore warnings
os.environ["OMP_NUM_THREADS"] = "1"
torch.set_num_threads(1)
multiprocessing.set_start_method("spawn", force=True)

app = Flask(__name__, static_folder='static')
CORS(app)
socketio = SocketIO(app)

# Load the Whisper model
model = whisper.load_model("base")

# Ensure uploads directory exists
UPLOAD_FOLDER = './static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store user sessions
users = {}

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/transcribe/<session_id>', methods=['POST'])
def transcribe_audio(session_id):
    audio_file = request.files.get('audio')

    if audio_file:
        try:
            unique_filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            audio_file.save(audio_path)
            print(f"File saved to {audio_path}")

            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            options = whisper.DecodingOptions(fp16=False)
            result = whisper.decode(model, mel, options)

            latest_transcription = result.text.strip()

            os.remove(audio_path)  # Clean up the file after processing
            
            # Emit the transcription to all connected clients
            socketio.emit('new_transcription', {'session_id': session_id, 'transcription': latest_transcription})

            return jsonify({'transcription': latest_transcription})

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': f'Error during transcription: {str(e)}'}), 500

    return jsonify({'error': 'No audio file provided.'}), 400

@socketio.on('user_joined')
def handle_user_joined(session_id):
    users[session_id] = {'joined': True}
    emit('user_joined', session_id, broadcast=True)

@socketio.on('user_left')
def handle_user_left(session_id):
    if session_id in users:
        del users[session_id]
        emit('user_left', session_id, broadcast=True)

@app.route('/static/uploads')
def list_audio_files():
    audio_files = os.listdir(UPLOAD_FOLDER)
    audio_files = [f for f in audio_files if f.endswith('.wav')]
    return jsonify({'files': audio_files})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
