from flask import Flask, request, send_file
from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

transcriptor = PianoTranscription(device='cpu')    # 'cuda' | 'cpu'


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

        return send_file(
            output_path,
            mimetype='audio/midi',
            as_attachment=True,
            download_name='transcribed.mid'
        )

    except Exception as e:
        return f'Error during transcription: {str(e)}', 500


if __name__ == '__main__':
    app.run(debug=True)
