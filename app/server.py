from flask import Flask, render_template, request
from acmi_parser import parse_acmi
import os

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()
    stats = parse_acmi(content)
    return render_template('result.html', stats=stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
