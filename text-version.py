#!/usr/bin/env python3
"""
Text-to-Voice Assistant
Combines: Text Input → Streaming LLM → Text-to-Speech
"""

import os
import sys
import queue
import threading
import subprocess
from pathlib import Path
import ollama

# Audio playback
try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("Installing audio libraries...")
    subprocess.run([sys.executable, "-m", "pip", "install", "sounddevice", "soundfile", "--break-system-packages"], check=True)
    import sounddevice as sd
    import soundfile as sf


class TextAssistant:
    def __init__(self, model_name="llama3.2:3b"):
        self.model_name = model_name
        
        # Setup directories
        self.script_dir = Path(__file__).parent
        self.output_dir = self.script_dir / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        
        # TTS model setup
        self.tts_model_name = "en_US-lessac-medium"
        self.model_path = self.script_dir / f"{self.tts_model_name}.onnx"
        self.config_path = self.script_dir / f"{self.tts_model_name}.onnx.json"
        
        # Conversation history for context
        self.conversation_history = []
        
        # Audio queue for streaming playback
        self.audio_queue = queue.Queue()
        self.is_speaking = False
        
        print("💬 Text-to-Voice Assistant")
        print("=" * 60)
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Check if all required components are available"""
        # Check Piper
        self.piper_cmd = self._find_piper()
        if not self.piper_cmd:
            print("⚠️  Piper not found. Install with:")
            print("   pip install piper-tts --break-system-packages")
            sys.exit(1)
            
        # Check TTS models
        if not self.model_path.exists() or not self.config_path.exists():
            print(f"⚠️  TTS model not found: {self.model_path}")
            print("\nDownload with:")
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
        print("=" * 60)
        print()
        
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
        
    def get_input(self):
        """Get text input from user"""
        try:
            text = input("You: ").strip()
            if text:
                return text
            return None
        except EOFError:
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
        """Convert text to speech and play it"""
        if not text:
            return
            
        print("🔊 Speaking...")
        
        # Generate unique filename for this utterance
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
        """Main assistant loop"""
        print("Text Assistant Ready!")
        print("Commands:")
        print("  - Type your messages to chat")
        print("  - Type 'exit', 'quit', or 'goodbye' to end")
        print("  - Press Ctrl+C to force quit")
        print()
        
        try:
            while True:
                # Get user input
                user_input = self.get_input()
                
                if not user_input:
                    continue
                    
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'goodbye', 'stop', 'bye']:
                    farewell = "Goodbye! Have a great day!"
                    print(f"🤖 Assistant: {farewell}")
                    self.speak(farewell)
                    break
                    
                # Generate LLM response
                response = self.generate_response(user_input)
                
                if response:
                    # Speak the response
                    self.speak(response)
                    
                print()  # Blank line between conversations
                
        except KeyboardInterrupt:
            print("\n\n👋 Assistant stopped")
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()


def main():
    # Parse command line arguments
    model = "llama3.2:3b"
    if len(sys.argv) > 1:
        model = sys.argv[1]
        
    assistant = TextAssistant(model_name=model)
    assistant.run()


if __name__ == "__main__":
    main()