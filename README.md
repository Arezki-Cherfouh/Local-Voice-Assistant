Real-Time Voice Assistant – Streaming Offline Version

This project is a fully offline, real-time voice assistant built in Python. It performs streaming speech-to-text using Vosk, generates responses with Ollama running a local LLM, and converts responses back to speech using Piper TTS. All components run locally with no cloud dependency.

Architecture

Speech Recognition: Vosk (streaming, offline)
Language Model: Ollama (local models such as llama3.2:3b)
Text-to-Speech: Piper (offline neural TTS)
Audio I/O: sounddevice + soundfile
Streaming Queue: Python queue + threading

Features

• Real-time transcription while speaking (partial + final results)
• Automatic silence detection to stop recording
• Fully offline pipeline (no internet required after setup)
• Streaming LLM responses
• Automatic conversation loop
• Clean audio playback with temporary file handling
• Configurable model and silence timeout via CLI

How It Works

1. Microphone audio is streamed in small blocks (16kHz mono).
2. Vosk processes audio incrementally and returns partial transcripts.
3. After silence timeout, final text is sent to Ollama.
4. Ollama streams a response token by token.
5. Piper converts the final response to speech and plays it.
6. Assistant returns to listening mode.

Requirements

Python 3.10+
Ollama running locally
Vosk model downloaded
Piper TTS installed
Piper voice model files
Linux (tested on Arch Linux with GNOME)

Installation

1. Install dependencies:
   pip install vosk sounddevice soundfile numpy piper-tts ollama --break-system-packages

2. Download Vosk model:
   Small (faster):
   wget [https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip)
   unzip vosk-model-small-en-us-0.15.zip

3. Download Piper voice model:
   wget [https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx)
   wget [https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json)

4. Start Ollama:
   ollama serve

Usage

python assistant.py
python assistant.py llama3.2:3b 2.5

Arguments:
1st argument: Ollama model name
2nd argument: silence timeout in seconds

Voice Commands

Say:
exit
quit
goodbye
stop
bye

Press Ctrl+C anytime to force stop.

Project Structure

assistant.py
outputs/ (temporary TTS audio)
vosk model directory
piper voice model files

Use Cases

• Offline AI assistant
• Local AI experimentation
• Voice interface prototyping
• Privacy-focused assistants
• Edge AI deployments

Everything runs locally. No API keys. No cloud calls. Full control.
