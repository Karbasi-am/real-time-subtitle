# Real Time Whisper Subtitle

This is a demo of real time speech to text with OpenAI's Whisper model, which also displays the text on screen like a subtitle and traslates the text to any language the user wants. It works by constantly recording audio in a thread and concatenating the raw bytes over multiple recordings.

To install dependencies simply run
```
pip install -r requirements.txt
```
in an environment of your choosing.

Whisper also requires the command-line tool [`ffmpeg`](https://ffmpeg.org/) to be installed on your system, which is available from most package managers:

```
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

## More

### Translation
you can select a language (fr, zh, fa, etc..) for the translation
this tool will translate the english text output from whisper to the selected language and displays the text on screen

```
# an example for real time translation
python3 main.py --model small --language fa
```

### Font
you can change and choose font color and font size

```
# an example for font size and font color
python3 main.py --model small --font_size 24 --font_color "yellow"
```
