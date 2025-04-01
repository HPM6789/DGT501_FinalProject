import sys
import numpy as np
import wave
import struct
from scipy.fft import fft
from scipy.io import wavfile
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QTextEdit, QFileDialog, QVBoxLayout, QGridLayout, QWidget, QHBoxLayout

# Bảng định nghĩa tần số DTMF: mỗi phím được biểu diễn bằng cặp tần số (low, high)
DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477), 'D': (941, 1633)
}
# Hàm tạo âm DTMF cho một phím nhất định
def generate_tone(key, duration=0.5, fs=8000):
    """Tạo tín hiệu âm thanh DTMF từ phím nhập vào."""
    low_freq, high_freq = DTMF_FREQS[key]  # Lấy tần số thấp và cao từ bảng DTMF
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)  # Tạo khoảng thời gian tín hiệu
    tone = np.sin(2 * np.pi * low_freq * t) + np.sin(2 * np.pi * high_freq * t)  # Tổng hợp hai tần số
    tone = tone * (32767 / np.max(np.abs(tone)))  # Chuẩn hóa giá trị âm thanh về mức 16-bit
    return tone.astype(np.int16)  # Chuyển đổi về kiểu dữ liệu int16 để lưu tệp WAV

# Hàm tạo chuỗi tín hiệu DTMF từ một dãy ký tự
def generate_dtmf_sequence(sequence, tone_duration=0.5, pause_duration=0.1, fs=8000):
    """Tạo chuỗi tín hiệu DTMF từ một chuỗi ký tự đầu vào."""
    signal = np.array([], dtype=np.int16)
    pause = np.zeros(int(fs * pause_duration), dtype=np.int16)  # Tạo khoảng lặng giữa các phím
    for key in sequence:
        if key in DTMF_FREQS:
            tone = generate_tone(key, duration=tone_duration, fs=fs)  # Sinh tín hiệu âm
            signal = np.concatenate((signal, tone, pause))  # Ghép tín hiệu với khoảng lặng
    return signal

# Hàm lưu tín hiệu thành tệp WAV
def save_wave(filename, signal, fs=8000):
    wavfile.write(filename, fs, signal)

# Hàm phát lại tệp WAV
def play_wave(filename):
    fs, data = wavfile.read(filename)
    import sounddevice as sd
    sd.play(data, fs)
    sd.wait()

# Hàm giải mã tín hiệu DTMF từ tín hiệu âm thanh
def decode_dtmf_from_signal(signal, fs=8000, tone_duration=0.5, pause_duration=0.1):
    """Giải mã tín hiệu DTMF từ tín hiệu âm thanh WAV."""
    samples_per_tone = int(fs * tone_duration)  # Số mẫu trên mỗi tín hiệu DTMF
    samples_per_pause = int(fs * pause_duration)  # Số mẫu của khoảng lặng
    index = 0
    decoded = ""
    low_freqs = [697, 770, 852, 941]  # Danh sách các tần số thấp DTMF
    high_freqs = [1209, 1336, 1477, 1633]  # Danh sách các tần số cao DTMF
    
    while index + samples_per_tone <= len(signal):
        chunk = signal[index:index + samples_per_tone]  # Trích xuất đoạn tín hiệu tương ứng
        fft_vals = np.abs(np.fft.rfft(chunk))  # Biến đổi Fourier để xác định tần số
        freqs = np.fft.rfftfreq(len(chunk), 1 / fs)
        peak_indices = np.argsort(fft_vals)[-10:]  # Lấy 10 giá trị tần số có cường độ cao nhất
        detected_low = None
        detected_high = None
        for idx in peak_indices:
            freq = freqs[idx]
            for lf in low_freqs:
                if abs(freq - lf) < 15:  # So khớp tần số thấp
                    detected_low = lf
                    break
            for hf in high_freqs:
                if abs(freq - hf) < 15:  # So khớp tần số cao
                    detected_high = hf
                    break
        for key, (lf, hf) in DTMF_FREQS.items():
            if detected_low == lf and detected_high == hf:
                decoded += key  # Thêm ký tự vào kết quả giải mã
                break
        index += samples_per_tone + samples_per_pause  # Chuyển sang đoạn tiếp theo
    return decoded

class DTMFApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DTMF Encoder/Decoder")
        self.setGeometry(100, 100, 600, 400)
        self.initUI()
    
    def initUI(self):
        main_layout = QHBoxLayout()
        encode_layout = QVBoxLayout()
        encode_label = QLabel("Mã hóa DTMF", self)
        encode_layout.addWidget(encode_label)
        
        self.text_encode = QTextEdit(self)
        self.text_encode.setReadOnly(True)
        encode_layout.addWidget(self.text_encode)
        
        self.btn_clear = QPushButton("Xóa", self)
        self.btn_clear.clicked.connect(self.clear_text)
        encode_layout.addWidget(self.btn_clear)
        
        self.btn_encode = QPushButton("Mã hóa DTMF", self)
        self.btn_encode.clicked.connect(self.encode_dtmf)
        encode_layout.addWidget(self.btn_encode)
        
        self.btn_play = QPushButton("Phát lại WAV", self)
        self.btn_play.clicked.connect(lambda: play_wave("dtmf_encoded.wav"))
        encode_layout.addWidget(self.btn_play)
        
        self.initKeypad(encode_layout)
        
        decode_layout = QVBoxLayout()
        # decode_label = QLabel("Giải mã DTMF", self)
        # decode_layout.addWidget(decode_label)
        
        self.text_decode = QTextEdit(self)
        decode_layout.addWidget(self.text_decode)
        
        self.btn_open = QPushButton("Mở tệp WAV và giải mã DTMF", self)
        self.btn_open.clicked.connect(self.open_file)
        decode_layout.addWidget(self.btn_open)
        
        # self.btn_decode = QPushButton("Giải mã DTMF", self)
        # self.btn_decode.clicked.connect(self.decode_dtmf)
        # decode_layout.addWidget(self.btn_decode)
        
        main_layout.addLayout(encode_layout)
        main_layout.addLayout(decode_layout)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
    
    def initKeypad(self, parent_layout):
        keypad_layout = QGridLayout()
        buttons = list(DTMF_FREQS.keys())
        for i, key in enumerate(buttons):
            btn = QPushButton(key, self)
            btn.clicked.connect(lambda checked, t=key: self.keypad_input(t))
            keypad_layout.addWidget(btn, i // 4, i % 4)
        parent_layout.addLayout(keypad_layout)
    
    def keypad_input(self, key):
        current_text = self.text_encode.toPlainText()
        self.text_encode.setText(current_text + key)
    
    def clear_text(self):
        self.text_encode.clear()
    
    def encode_dtmf(self):
        digits = self.text_encode.toPlainText()
        if not digits:
            self.text_encode.setText("Vui lòng nhập số để mã hóa!")
            return
        signal = generate_dtmf_sequence(digits)
        save_wave("dtmf_encoded.wav", signal)
        self.text_encode.append("DTMF đã được mã hóa và lưu vào 'dtmf_encoded.wav'")
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn tệp WAV", "", "WAV Files (*.wav)")
        if file_path:
            self.text_decode.setText(f"Đã mở tệp: {file_path}")
            self.decode_dtmf(file_path)
    
    def decode_dtmf(self, file_path=None):
        if not file_path:
            self.text_decode.setText("Chưa chọn tệp WAV!")
            return
        fs, signal = wavfile.read(file_path)
        decoded_digits = decode_dtmf_from_signal(signal)
        self.text_decode.setText(f"Chuỗi DTMF giải mã: {decoded_digits}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DTMFApp()
    window.show()
    sys.exit(app.exec())
