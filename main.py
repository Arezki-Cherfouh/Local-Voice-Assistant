#!/usr/bin/env python3
"""
Real-Time Voice Assistant - STREAMING VOSK VERSION
Features: Real-time transcription display as you speak
Uses: Vosk (offline STT with streaming) → Ollama → Piper
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import ollama
import queue
import threading

# Audio recording
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
except ImportError:
    print("Installing audio libraries...")
    subprocess.run([sys.executable, "-m", "pip", "install", "sounddevice", "soundfile", "numpy", "--break-system-packages"], check=True)
    import sounddevice as sd
    import soundfile as sf
    import numpy as np

# Vosk speech recognition
try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    print("Installing Vosk...")
    subprocess.run([sys.executable, "-m", "pip", "install", "vosk", "--break-system-packages"], check=True)
    from vosk import Model, KaldiRecognizer


class StreamingVoiceAssistant:
    def __init__(self, model_name="llama3.2:3b", silence_timeout=3.0):
        self.model_name = model_name
        self.silence_timeout = silence_timeout  # Seconds of silence before auto-stop
        
        # Audio settings
        self.sample_rate = 16000  # Vosk works best at 16kHz
        self.channels = 1  # Mono
        self.block_size = 4000  # Samples per block (~0.25 seconds at 16kHz)
        
        # Setup directories
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        
        # Vosk model path
        self.vosk_model_dir = self.script_dir / "../../Python-Projects/model"
        
        # TTS model setup
        self.tts_model_name = "en_US-lessac-medium"
        self.model_path = self.script_dir / f"{self.tts_model_name}.onnx"
        self.config_path = self.script_dir / f"{self.tts_model_name}.onnx.json"
        
        # Conversation history
        self.conversation_history = []
        
        # Audio queue for streaming
        self.audio_queue = queue.Queue()
        
        print("🎙️  Streaming Offline Voice Assistant")
        print("=" * 60)
        self._check_dependencies()
        
        # Initialize Vosk
        print("Loading Vosk model...")
        self.vosk_model = Model(str(self.vosk_model_dir))
        print("✓ Vosk model loaded")
        print()
        
    def _check_dependencies(self):
        """Check if all required components are available"""
        
        # Check Vosk model
        if not self.vosk_model_dir.exists():
            print(f"⚠️  Vosk model not found: {self.vosk_model_dir}")
            print("\n📥 Download the Vosk model:")
            print("   Small model (40 MB, faster):")
            print("   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
            print("   unzip vosk-model-small-en-us-0.15.zip")
            print()
            print("   Large model (1.8 GB, more accurate):")
            print("   wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip")
            print("   unzip vosk-model-en-us-0.22.zip")
            print("   mv vosk-model-en-us-0.22 vosk-model-small-en-us-0.15")
            sys.exit(1)
        
        # Check Piper
        self.piper_cmd = self._find_piper()
        if not self.piper_cmd:
            print("⚠️  Piper not found. Install with:")
            print("   pip install piper-tts --break-system-packages")
            sys.exit(1)
            
        # Check TTS models
        if not self.model_path.exists() or not self.config_path.exists():
            print(f"⚠️  TTS model not found: {self.model_path}")
            print("\n📥 Download Piper voice model:")
            print(f"   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/{self.tts_model_name}.onnx")
            print(f"   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/{self.tts_model_name}.onnx.json")
            sys.exit(1)
            
        # Check Ollama
        try:
            ollama.list()
            print(f"✓ Ollama connected (model: {self.model_name})")
        except Exception as e:
            print(f"⚠️  Ollama not available: {e}")
            print("   Make sure Ollama is running: ollama serve")
            sys.exit(1)
            
        print(f"✓ Piper TTS ready")
        print(f"✓ Vosk model found")
        print("=" * 60)
        
    def _find_piper(self):
        """Find piper executable"""
        piper_in_venv = os.path.join(sys.prefix, "bin", "piper")
        if os.path.exists(piper_in_venv):
            return piper_in_venv
            
        try:
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                return "piper"
        except FileNotFoundError:
            pass
            
        return None
        
    def listen_streaming(self):
        """
        Listen with real-time streaming transcription
        Shows partial results as you speak!
        """
        print("🎤 Listening... (speak now)")
        print(f"   💡 Partial transcription will appear in real-time")
        print(f"   ⏸️  Pause for {self.silence_timeout} seconds to finish, or press Ctrl+C\n")
        
        # Create recognizer for this session
        recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
        recognizer.SetWords(True)
        
        # Track silence for auto-stop
        silence_threshold = 500  # RMS threshold
        silence_blocks = 0
        # Calculate max silence blocks based on timeout
        # Each block is ~0.25 seconds (block_size / sample_rate)
        blocks_per_second = self.sample_rate / self.block_size
        max_silence_blocks = int(self.silence_timeout * blocks_per_second)
        
        partial_text = ""
        final_text = ""
        
        def audio_callback(indata, frames, time, status):
            """Process audio in real-time"""
            if status:
                print(f"⚠️  {status}", file=sys.stderr)
            self.audio_queue.put(bytes(indata))
        
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='int16',
                channels=self.channels,
                callback=audio_callback
            ):
                print("📝 ", end="", flush=True)
                
                while True:
                    # Get audio data
                    data = self.audio_queue.get()
                    
                    # Check for silence
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_array**2))
                    
                    if rms < silence_threshold:
                        silence_blocks += 1
                        if silence_blocks >= max_silence_blocks and final_text:
                            print("\n   (Auto-stopped after silence)")
                            break
                    else:
                        silence_blocks = 0
                    
                    # Process with Vosk
                    if recognizer.AcceptWaveform(data):
                        # Final result for this phrase
                        result = json.loads(recognizer.Result())
                        if result.get('text'):
                            final_text += " " + result['text']
                            # Clear partial, show final
                            print(f"\r📝 {final_text.strip()}", end="", flush=True)
                    else:
                        # Partial result (word being spoken)
                        partial_result = json.loads(recognizer.PartialResult())
                        if partial_result.get('partial'):
                            partial_text = partial_result['partial']
                            # Show final + current partial
                            display = final_text.strip()
                            if partial_text:
                                display += " " + partial_text if display else partial_text
                            print(f"\r📝 {display}", end="", flush=True)
                
        except KeyboardInterrupt:
            print("\n   (Stopped by user)")
        
        finally:
            # Get any remaining text
            final_result = json.loads(recognizer.FinalResult())
            if final_result.get('text'):
                final_text += " " + final_result['text']
        
        final_text = final_text.strip()
        
        if final_text:
            print(f"\n✓ Final: \"{final_text}\"\n")
            return final_text
        else:
            print("\n❓ No speech detected\n")
            return None
            
    def generate_response(self, user_input):
        """Stream response from LLM"""
        # Add user message to history
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        print("🤖 Assistant: ", end="", flush=True)
        
        full_response = ""
        
        try:
            stream = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=True,
            )
            
            for chunk in stream:
                content = chunk['message']['content']
                print(content, end="", flush=True)
                full_response += content
                
        except Exception as e:
            print(f"\n❌ LLM error: {e}")
            return None
            
        print()  # New line after response
        
        # Add assistant response to history
        self.conversation_history.append({
            'role': 'assistant',
            'content': full_response
        })
        
        return full_response
        
    def speak(self, text):
        """Convert text to speech and play it (offline)"""
        if not text:
            return
            
        print("🔊 Speaking...")
        
        # Generate unique filename
        output_file = self.output_dir / f"response_{hash(text) % 100000}.wav"
        
        try:
            # Generate speech with Piper
            result = subprocess.run(
                [self.piper_cmd, "-m", str(self.model_path), "-f", str(output_file)],
                input=text,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and output_file.exists():
                # Play the audio
                data, samplerate = sf.read(str(output_file))
                sd.play(data, samplerate)
                sd.wait()  # Wait until playback is finished
                
                # Clean up
                output_file.unlink()
                return True
            else:
                print(f"⚠️  TTS failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"⚠️  TTS error: {e}")
            return False
            
    def run(self):
        """Main voice assistant loop"""
        print("🔒 Streaming Offline Voice Assistant Ready!")
        print("=" * 60)
        print("Features:")
        print("  ✓ Real-time transcription (see words as you speak)")
        print("  ✓ Auto-start listening (no Enter key needed)")
        print("  ✓ Vosk offline speech recognition")
        print("  ✓ Ollama local LLM")
        print("  ✓ Piper offline text-to-speech")
        print()
        print("💡 Usage:")
        print("  1. Just start speaking - listening starts automatically")
        print("  2. Transcription appears in real-time as you speak")
        print(f"  3. Pause for {self.silence_timeout} seconds to finish")
        print("  4. Assistant responds, then listening starts again")
        print()
        print(f"⚙️  Settings:")
        print(f"  • Silence timeout: {self.silence_timeout} seconds")
        print(f"  • Model: {self.model_name}")
        print()
        print("Commands: Say 'exit', 'quit', or 'goodbye' to end")
        print("         Press Ctrl+C anytime to force stop")
        print("=" * 60)
        print()
        
        try:
            while True:
                # Auto-start listening (no Enter key needed)
                user_input = self.listen_streaming()
                
                if not user_input:
                    continue
                    
                # Check for exit commands
                if any(word in user_input.lower() for word in ['exit', 'quit', 'goodbye', 'stop', 'bye']):
                    farewell = "Goodbye! Have a great day!"
                    print(f"🤖 Assistant: {farewell}")
                    self.speak(farewell)
                    break
                    
                # Generate LLM response
                response = self.generate_response(user_input)
                
                if response:
                    # Speak the response
                    self.speak(response)
                    
                print("\n" + "="*60 + "\n")  # Separator between conversations
                print("Ready for next input...\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Voice assistant stopped")
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()


def main():
    # Parse command line arguments
    model = "llama3.2:3b"
    silence_timeout = 3.0
    
    if len(sys.argv) > 1:
        model = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            silence_timeout = float(sys.argv[2])
        except ValueError:
            print(f"Invalid timeout value: {sys.argv[2]}, using default: 3.0")
    
    print(f"Starting with model: {model}, silence timeout: {silence_timeout}s\n")
    
    assistant = StreamingVoiceAssistant(model_name=model, silence_timeout=silence_timeout)
    assistant.run()


if __name__ == "__main__":
    main()




# #!/usr/bin/env python3
# """
# Real-Time Voice Assistant - STREAMING VOSK VERSION
# Features: Real-time transcription display as you speak
# Uses: Vosk (offline STT with streaming) → Ollama → Piper
# """

# import os
# import sys
# import json
# import subprocess
# from pathlib import Path
# import ollama
# import queue
# import threading

# # Audio recording
# try:
#     import sounddevice as sd
#     import soundfile as sf
#     import numpy as np
# except ImportError:
#     print("Installing audio libraries...")
#     subprocess.run([sys.executable, "-m", "pip", "install", "sounddevice", "soundfile", "numpy", "--break-system-packages"], check=True)
#     import sounddevice as sd
#     import soundfile as sf
#     import numpy as np

# # Vosk speech recognition
# try:
#     from vosk import Model, KaldiRecognizer
# except ImportError:
#     print("Installing Vosk...")
#     subprocess.run([sys.executable, "-m", "pip", "install", "vosk", "--break-system-packages"], check=True)
#     from vosk import Model, KaldiRecognizer


# class StreamingVoiceAssistant:
#     def __init__(self, model_name="llama3.2:3b"):
#         self.model_name = model_name
        
#         # Audio settings
#         self.sample_rate = 16000  # Vosk works best at 16kHz
#         self.channels = 1  # Mono
#         self.block_size = 4000  # Samples per block (~0.25 seconds at 16kHz)
        
#         # Setup directories
#         self.script_dir = Path(__file__).parent
#         self.output_dir = self.script_dir / "outputs"
#         self.output_dir.mkdir(exist_ok=True)
        
#         # Vosk model path
#         self.vosk_model_dir = self.script_dir / "../../Python-Projects/model"
        
#         # TTS model setup
#         self.tts_model_name = "en_US-lessac-medium"
#         self.model_path = self.script_dir / f"{self.tts_model_name}.onnx"
#         self.config_path = self.script_dir / f"{self.tts_model_name}.onnx.json"
        
#         # Conversation history
#         self.conversation_history = []
        
#         # Audio queue for streaming
#         self.audio_queue = queue.Queue()
        
#         print("🎙️  Streaming Offline Voice Assistant")
#         print("=" * 60)
#         self._check_dependencies()
        
#         # Initialize Vosk
#         print("Loading Vosk model...")
#         self.vosk_model = Model(str(self.vosk_model_dir))
#         print("✓ Vosk model loaded")
#         print()
        
#     def _check_dependencies(self):
#         """Check if all required components are available"""
        
#         # Check Vosk model
#         if not self.vosk_model_dir.exists():
#             print(f"⚠️  Vosk model not found: {self.vosk_model_dir}")
#             print("\n📥 Download the Vosk model:")
#             print("   Small model (40 MB, faster):")
#             print("   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
#             print("   unzip vosk-model-small-en-us-0.15.zip")
#             print()
#             print("   Large model (1.8 GB, more accurate):")
#             print("   wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip")
#             print("   unzip vosk-model-en-us-0.22.zip")
#             print("   mv vosk-model-en-us-0.22 vosk-model-small-en-us-0.15")
#             sys.exit(1)
        
#         # Check Piper
#         self.piper_cmd = self._find_piper()
#         if not self.piper_cmd:
#             print("⚠️  Piper not found. Install with:")
#             print("   pip install piper-tts --break-system-packages")
#             sys.exit(1)
            
#         # Check TTS models
#         if not self.model_path.exists() or not self.config_path.exists():
#             print(f"⚠️  TTS model not found: {self.model_path}")
#             print("\n📥 Download Piper voice model:")
#             print(f"   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/{self.tts_model_name}.onnx")
#             print(f"   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/{self.tts_model_name}.onnx.json")
#             sys.exit(1)
            
#         # Check Ollama
#         try:
#             ollama.list()
#             print(f"✓ Ollama connected (model: {self.model_name})")
#         except Exception as e:
#             print(f"⚠️  Ollama not available: {e}")
#             print("   Make sure Ollama is running: ollama serve")
#             sys.exit(1)
            
#         print(f"✓ Piper TTS ready")
#         print(f"✓ Vosk model found")
#         print("=" * 60)
        
#     def _find_piper(self):
#         """Find piper executable"""
#         piper_in_venv = os.path.join(sys.prefix, "bin", "piper")
#         if os.path.exists(piper_in_venv):
#             return piper_in_venv
            
#         try:
#             result = subprocess.run(
#                 ["piper", "--version"],
#                 capture_output=True,
#                 check=False
#             )
#             if result.returncode == 0:
#                 return "piper"
#         except FileNotFoundError:
#             pass
            
#         return None
        
#     def listen_streaming(self):
#         """
#         Listen with real-time streaming transcription
#         Shows partial results as you speak!
#         """
#         print("🎤 Listening... (speak now)")
#         print("   💡 Partial transcription will appear in real-time")
#         print("   ⏸️  Pause for 2 seconds to finish, or press Ctrl+C\n")
        
#         # Create recognizer for this session
#         recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
#         recognizer.SetWords(True)
        
#         # Track silence for auto-stop
#         silence_threshold = 500  # RMS threshold
#         silence_blocks = 0
#         max_silence_blocks = 8  # ~2 seconds of silence (8 * 0.25s)
        
#         partial_text = ""
#         final_text = ""
        
#         def audio_callback(indata, frames, time, status):
#             """Process audio in real-time"""
#             if status:
#                 print(f"⚠️  {status}", file=sys.stderr)
#             self.audio_queue.put(bytes(indata))
        
#         try:
#             with sd.RawInputStream(
#                 samplerate=self.sample_rate,
#                 blocksize=self.block_size,
#                 dtype='int16',
#                 channels=self.channels,
#                 callback=audio_callback
#             ):
#                 print("📝 ", end="", flush=True)
                
#                 while True:
#                     # Get audio data
#                     data = self.audio_queue.get()
                    
#                     # Check for silence
#                     audio_array = np.frombuffer(data, dtype=np.int16)
#                     rms = np.sqrt(np.mean(audio_array**2))
                    
#                     if rms < silence_threshold:
#                         silence_blocks += 1
#                         if silence_blocks >= max_silence_blocks and final_text:
#                             print("\n   (Auto-stopped after silence)")
#                             break
#                     else:
#                         silence_blocks = 0
                    
#                     # Process with Vosk
#                     if recognizer.AcceptWaveform(data):
#                         # Final result for this phrase
#                         result = json.loads(recognizer.Result())
#                         if result.get('text'):
#                             final_text += " " + result['text']
#                             # Clear partial, show final
#                             print(f"\r📝 {final_text.strip()}", end="", flush=True)
#                     else:
#                         # Partial result (word being spoken)
#                         partial_result = json.loads(recognizer.PartialResult())
#                         if partial_result.get('partial'):
#                             partial_text = partial_result['partial']
#                             # Show final + current partial
#                             display = final_text.strip()
#                             if partial_text:
#                                 display += " " + partial_text if display else partial_text
#                             print(f"\r📝 {display}", end="", flush=True)
                
#         except KeyboardInterrupt:
#             print("\n   (Stopped by user)")
        
#         finally:
#             # Get any remaining text
#             final_result = json.loads(recognizer.FinalResult())
#             if final_result.get('text'):
#                 final_text += " " + final_result['text']
        
#         final_text = final_text.strip()
        
#         if final_text:
#             print(f"\n✓ Final: \"{final_text}\"\n")
#             return final_text
#         else:
#             print("\n❓ No speech detected\n")
#             return None
            
#     def generate_response(self, user_input):
#         """Stream response from LLM"""
#         # Add user message to history
#         self.conversation_history.append({
#             'role': 'user',
#             'content': user_input
#         })
        
#         print("🤖 Assistant: ", end="", flush=True)
        
#         full_response = ""
        
#         try:
#             stream = ollama.chat(
#                 model=self.model_name,
#                 messages=self.conversation_history,
#                 stream=True,
#             )
            
#             for chunk in stream:
#                 content = chunk['message']['content']
#                 print(content, end="", flush=True)
#                 full_response += content
                
#         except Exception as e:
#             print(f"\n❌ LLM error: {e}")
#             return None
            
#         print()  # New line after response
        
#         # Add assistant response to history
#         self.conversation_history.append({
#             'role': 'assistant',
#             'content': full_response
#         })
        
#         return full_response
        
#     def speak(self, text):
#         """Convert text to speech and play it (offline)"""
#         if not text:
#             return
            
#         print("🔊 Speaking...")
        
#         # Generate unique filename
#         output_file = self.output_dir / f"response_{hash(text) % 100000}.wav"
        
#         try:
#             # Generate speech with Piper
#             result = subprocess.run(
#                 [self.piper_cmd, "-m", str(self.model_path), "-f", str(output_file)],
#                 input=text,
#                 text=True,
#                 capture_output=True,
#                 timeout=30
#             )
            
#             if result.returncode == 0 and output_file.exists():
#                 # Play the audio
#                 data, samplerate = sf.read(str(output_file))
#                 sd.play(data, samplerate)
#                 sd.wait()  # Wait until playback is finished
                
#                 # Clean up
#                 output_file.unlink()
#                 return True
#             else:
#                 print(f"⚠️  TTS failed: {result.stderr}")
#                 return False
                
#         except Exception as e:
#             print(f"⚠️  TTS error: {e}")
#             return False
            
#     def run(self):
#         """Main voice assistant loop"""
#         print("🔒 Streaming Offline Voice Assistant Ready!")
#         print("=" * 60)
#         print("Features:")
#         print("  ✓ Real-time transcription (see words as you speak)")
#         print("  ✓ Vosk offline speech recognition")
#         print("  ✓ Ollama local LLM")
#         print("  ✓ Piper offline text-to-speech")
#         print()
#         print("💡 Usage:")
#         print("  1. Press Enter to start listening")
#         print("  2. Speak naturally - transcription appears in real-time")
#         print("  3. Pause for 2 seconds OR press Ctrl+C to finish")
#         print("  4. Assistant responds")
#         print()
#         print("Commands: Say 'exit', 'quit', or 'goodbye' to end")
#         print("=" * 60)
#         print()
        
#         try:
#             while True:
#                 # Wait for user to start
#                 input("Press Enter to speak...")
#                 print()
                
#                 # Listen with streaming transcription
#                 user_input = self.listen_streaming()
                
#                 if not user_input:
#                     continue
                    
#                 # Check for exit commands
#                 if any(word in user_input.lower() for word in ['exit', 'quit', 'goodbye', 'stop', 'bye']):
#                     farewell = "Goodbye! Have a great day!"
#                     print(f"🤖 Assistant: {farewell}")
#                     self.speak(farewell)
#                     break
                    
#                 # Generate LLM response
#                 response = self.generate_response(user_input)
                
#                 if response:
#                     # Speak the response
#                     self.speak(response)
                    
#                 print("\n" + "="*60 + "\n")  # Separator between conversations
                
#         except KeyboardInterrupt:
#             print("\n\n👋 Voice assistant stopped")
            
#         except Exception as e:
#             print(f"\n❌ Unexpected error: {e}")
#             import traceback
#             traceback.print_exc()


# def main():
#     # Parse command line arguments
#     model = "llama3.2:3b"
#     if len(sys.argv) > 1:
#         model = sys.argv[1]
        
#     assistant = StreamingVoiceAssistant(model_name=model)
#     assistant.run()


# if __name__ == "__main__":
#     main()



