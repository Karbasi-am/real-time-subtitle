import numpy as np
import speech_recognition as sr
import whisper
import torch
import requests
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from deep_translator import GoogleTranslator
import tkinter as tk
import threading
import argparse

def update_text_after_delay(text, delay):
    root.after(delay, update_display_text, text)

def update_display_text(new_text):
    label.config(text=new_text)

def check_internet():
    try:
        # Attempt to connect to the internet
        response = requests.get("http://www.google.com", timeout=5)
        return True if response.status_code == 200 else False
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False

# Usage
if check_internet():
    print("Internet is available.")
else:
    print("No internet connection.")


def main():

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # Bytes object which holds audio data for the current phrase
    phrase_bytes = bytes()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate=16000)

    target_language = args.language if check_internet() else False
    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout


    transcription = ['']
    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    phrase_bytes = bytes()
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()

                # Add the new audio data to the accumulated data for this phrase
                phrase_bytes += audio_data

                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                audio_np = np.frombuffer(phrase_bytes, dtype=np.int16).astype(np.float32) / 32768.0

                # Read the transcription.
                result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip()
                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise, edit the existing one.
                if phrase_complete:
                    transcription.append(text)

                else:
                    transcription[-1] = text


                line = transcription[-1]

                # Translating to target_language if a language is selected
                if target_language:
                    line = GoogleTranslator(source='auto', target=target_language).translate(line)

                # displaying the text on screen
                update_display_text(line)

            else:
                sleep(0.25)
        except KeyboardInterrupt:
            break


parser = argparse.ArgumentParser()
parser.add_argument("--model", default="base", help="Model to use",
                    choices=["tiny", "base", "small", "medium", "large"])
parser.add_argument("--non_english", default=False, action='store_true',
                    help="Don't use the english model.")
parser.add_argument("--energy_threshold", default=1000,
                    help="Energy level for mic to detect.", type=int)
parser.add_argument("--record_timeout", default=3,
                    help="How real time the recording is in seconds.", type=float)
parser.add_argument("--phrase_timeout", default=3,
                    help="How much empty space between recordings before we "
                         "consider it a new line in the transcription.", type=float)
parser.add_argument("--language", help="Translate en to selected language.")
parser.add_argument("--font_color",default="yellow" , help="Changing font color.")
parser.add_argument("--font_size",default=24 , help="Changing font size.")

args = parser.parse_args()

font_size = args.font_size
font_color = args.font_color

# Load / Download model
try:
    model = args.model
    if args.model != "large" and not args.non_english:
        model = model + ".en"
    audio_model = whisper.load_model(model)
except Exception as e:
    print("Failed to Load / Download model.\n", e)
    exit(1)

ai = threading.Thread(target=main)
ai.start()
root = tk.Tk()
root.title("Subtitle")

# Getting monitor info
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = screen_width // 3
window_height = screen_height // 9

# To place the window in the middle of the screen

x = (screen_width // 2) - (window_width // 2)

# Setting window size
root.geometry(f"{window_width}x{window_height}")

# Setting window position
root.geometry(f"+{x}-{45}")

root.configure(bg='black')

# Making the window transparent
root.attributes('-alpha', 0.5)

root.overrideredirect(True)

# Override on other windows
root.attributes('-topmost', True)

label = tk.Label(root, text="", font=("Arial", font_size), fg=font_color, bg="black", wraplength=int(window_width - window_width * 0.05))
label.pack(expand=True)
root.update()
root.mainloop()

