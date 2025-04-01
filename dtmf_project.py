from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
import numpy as np
from scipy.io.wavfile import write
import requests

DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477)
}

class DialerApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        self.number_input = TextInput(font_size=32, readonly=True, size_hint=(1, 0.2), halign='center')
        main_layout.add_widget(self.number_input)
        
        grid_layout = GridLayout(cols=3, spacing=10, size_hint=(1, 0.6))
        buttons = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for btn in buttons:
            button = Button(text=btn, font_size=32, size_hint=(None, None), size=(100, 100))
            button.bind(on_press=self.add_digit)
            grid_layout.add_widget(button)
        main_layout.add_widget(grid_layout)
        
        call_button_layout = BoxLayout(size_hint=(1, 0.2))
        self.call_button = Button(text='CALL', font_size=32, size_hint=(None, None), size=(100, 100), background_color=(0, 1, 0, 1))
        self.call_button.bind(on_press=self.make_call)
        call_button_layout.add_widget(self.call_button)
        main_layout.add_widget(call_button_layout)
        
        self.result_label = Label(text='Result:', font_size=24, size_hint=(1, 0.2))
        main_layout.add_widget(self.result_label)
        
        return main_layout
    
    def add_digit(self, instance):
        self.number_input.text += instance.text
    
    def generate_dtmf_tone(self, digits, filename='dtmf.wav'):
        rate = 8000
        duration = 0.5
        signal = np.array([])
        for digit in digits:
            if digit in DTMF_FREQS:
                f1, f2 = DTMF_FREQS[digit]
                t = np.linspace(0, duration, int(rate * duration), endpoint=False)
                tone = 0.5 * (np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t))
                signal = np.concatenate((signal, tone, np.zeros(int(rate * 0.1))))
        write(filename, rate, (signal * 32767).astype(np.int16))
        return filename
    
    def make_call(self, instance):
        digits = self.number_input.text
        if not digits:
            self.result_label.text = 'Enter a number first!'
            return
        
        wav_file = self.generate_dtmf_tone(digits)
        
        with open(wav_file, 'rb') as f:
            response = requests.post(
                'https://dsp-dtmf-h8hqdhhnapaaddgn.southeastasia-01.azurewebsites.net/decode',
                files={'file': f}
            )
        
        if response.status_code == 200:
            jsonResponse = response.json()
            decodedValue = jsonResponse.get("decoded", "Unknown")
            self.result_label.text = f'Result: {decodedValue}'
        else:
            self.result_label.text = 'Error in API call'

if __name__ == '__main__':
    DialerApp().run()