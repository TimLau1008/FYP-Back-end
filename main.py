from flask import Flask, Response, request, send_file
from flask_cors import CORS
from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
from music21 import converter
import os
from threading import Lock

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'temp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

transcriptor = PianoTranscription(device='cpu')    # 'cuda' | 'cpu'

# Lock to prevent file overwriting
lock = Lock()

@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
        <body>
            <h1>Piano Transcription System</h1>
            <form action="/transcribe" method="post" enctype="multipart/form-data">
                <input type="file" name="audio" accept=".wav">
                <input type="submit" value="Start Transcription">
            </form>
        </body>
    </html>
    '''


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return 'No file uploaded', 400

    file = request.files['audio']
    if file.filename == '':
        return 'No file selected', 400

    input_path = os.path.join(UPLOAD_FOLDER, 'input.wav')
    output_path = os.path.join(UPLOAD_FOLDER, 'output.mid')
    file.save(input_path)

    try:
        (audio, _) = load_audio(input_path, sr=sample_rate, mono=True)

        transcribed_dict = transcriptor.transcribe(audio, output_path)

        if not os.path.exists(output_path):
            return "Error: MIDI file not created", 500
        
        with open(output_path, "rb") as f:
            midi_data = f.read()

        os.remove(input_path)
        os.remove(output_path)
        return Response(midi_data, mimetype="audio/midi")

    except Exception as e:
        return f'Error during transcription: {str(e)}', 500

@app.route('/midi2mucicxml', methods=['POST'])
def midi2musicxml():
    midi_path = 'temp/midi_file.mid'
    musicxml_path = 'temp/musicxml.musicxml'

    if 'midi' not in request.files:
        return 'No file uploaded', 400
    
    midi_file = request.files['midi']
    try:
        midi_file.save(midi_path)

        sheet = converter.parse(midi_path, format='midi')

        sheet.write('musicxml', musicxml_path)

        with open(musicxml_path, 'r', encoding='utf-8') as f:
            musicxml_content = f.read()

        if not os.path.exists(musicxml_path):
            print("Error: MusicXML file not created")
        if os.path.exists(midi_path):
            os.remove(midi_path)
        if os.path.exists(musicxml_path):
            os.remove(musicxml_path)
        else: 
            print("Error: MusicXML file not created")

        return Response(musicxml_content, mimetype="application/xml")
    
        

    except Exception as e:
        return f'Error during conversion: {e}', 500

if __name__ == '__main__':
    app.run(debug=True)
