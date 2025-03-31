from flask import Flask, render_template, request, redirect, url_for, jsonify
from scipy.io.wavfile import read
from scipy.signal import find_peaks
from scipy.fft import fft
import numpy as np
import os
import tempfile

app = Flask(__name__)

# DTMF Frequencies mapping
DTMF_FREQUENCIES = {
    (697, 1209): '1', (697, 1336): '2', (697, 1477): '3', (697, 1633): 'A',
    (770, 1209): '4', (770, 1336): '5', (770, 1477): '6', (770, 1633): 'B',
    (852, 1209): '7', (852, 1336): '8', (852, 1477): '9', (852, 1633): 'C',
    (941, 1209): '*', (941, 1336): '0', (941, 1477): '#', (941, 1633): 'D'
}
row_freqs = [697, 770, 852, 941]
col_freqs = [1209, 1336, 1477, 1633]

def detect_dtmf_tone(segment, Fs):
    N = len(segment)
    freqs = np.fft.fftfreq(N, 1/Fs)
    spectrum = np.abs(fft(segment))[:N//2]
    freqs = freqs[:N//2]
    peaks, _ = find_peaks(spectrum, height=1000)
    detected = freqs[peaks]

    found_row, found_col = None, None
    for f in detected:
        for r in row_freqs:
            if abs(f - r) < 10:
                found_row = r
        for c in col_freqs:
            if abs(f - c) < 10:
                found_col = c
    return DTMF_FREQUENCIES.get((found_row, found_col), '?') if found_row and found_col else '?'

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', result='No file provided')
        file = request.files['file']
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            file.save(tmp.name)
            Fs, signal = read(tmp.name)
            os.unlink(tmp.name)

        tone_duration = 0.5
        pause_duration = 0.1
        step = int(Fs * (tone_duration + pause_duration))
        tone_samples = int(Fs * tone_duration)

        decoded = []
        for i in range(0, len(signal), step):
            segment = signal[i:i+tone_samples]
            if len(segment) < tone_samples:
                break
            key = detect_dtmf_tone(segment, Fs)
            decoded.append(key)

        result = ''.join(decoded)
    return render_template('index.html', result=result)

@app.route('/decode', methods=['POST'])
def decode():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        file.save(tmp.name)
        Fs, signal = read(tmp.name)
        os.unlink(tmp.name)

    tone_duration = 0.5
    pause_duration = 0.1
    step = int(Fs * (tone_duration + pause_duration))
    tone_samples = int(Fs * tone_duration)

    decoded = []
    for i in range(0, len(signal), step):
        segment = signal[i:i+tone_samples]
        if len(segment) < tone_samples:
            break
        key = detect_dtmf_tone(segment, Fs)
        decoded.append(key)

    return jsonify({'decoded': ''.join(decoded)})

if __name__ == '__main__':
    app.run(debug=True)
