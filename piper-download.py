#!/usr/bin/env python3
"""
Download Piper voice model to current directory
"""

import os
import urllib.request
import sys


def download_file(url, filename):
    """Download a file with progress"""
    print(f"Downloading {filename}...")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        sys.stdout.write(f'\r  Progress: {percent:.1f}%')
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, report_progress)
        print()  # New line after progress
        return True
    except Exception as e:
        print(f"\n✗ Error downloading: {e}")
        return False


def main():
    print("="*60)
    print("Piper Voice Model Downloader")
    print("="*60)
    print()
    
    # Model files to download
    voice_name = "en_US-lessac-medium"
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
    
    files = [
        (f"{voice_name}.onnx", f"{base_url}/{voice_name}.onnx"),
        (f"{voice_name}.onnx.json", f"{base_url}/{voice_name}.onnx.json"),
    ]
    
    print(f"Downloading voice: {voice_name}")
    print(f"Destination: {os.getcwd()}")
    print()
    
    success_count = 0
    
    for filename, url in files:
        # Check if already exists
        if os.path.exists(filename):
            print(f"✓ {filename} already exists (skipping)")
            success_count += 1
            continue
        
        # Download
        if download_file(url, filename):
            file_size = os.path.getsize(filename)
            print(f"✓ Downloaded {filename} ({file_size/1024/1024:.1f} MB)")
            success_count += 1
        else:
            print(f"✗ Failed to download {filename}")
    
    print()
    print("="*60)
    
    if success_count == len(files):
        print("✓ All files downloaded successfully!")
        print()
        print("Files in current directory:")
        for filename, _ in files:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"  • {filename} ({size/1024/1024:.1f} MB)")
        print()
        print("You can now run: python3 piper_local.py")
    else:
        print("⚠ Some downloads failed")
        print()
        print("Manual download:")
        for filename, url in files:
            if not os.path.exists(filename):
                print(f"  wget {url}")


if __name__ == "__main__":
    main()



# #!/usr/bin/env python3
# """
# Piper TTS Demo Script
# Fast, local, high-quality text-to-speech
# """

# import os
# import sys
# import subprocess
# from pathlib import Path


# def check_piper_installed():
#     """Check if Piper is installed"""
#     # Check for piper in multiple locations
#     locations_to_check = [
#         "piper",  # System PATH
#         ".venv/bin/piper",  # Local venv
#         "../.venv/bin/piper",  # Parent venv
#         os.path.expanduser("~/.local/bin/piper"),  # User local
#     ]
    
#     for piper_path in locations_to_check:
#         try:
#             result = subprocess.run(
#                 [piper_path, "--version"],
#                 capture_output=True,
#                 text=True,
#                 check=False
#             )
#             if result.returncode == 0:
#                 print(f"✓ Found piper at: {piper_path}")
#                 return piper_path
#         except (FileNotFoundError, PermissionError):
#             continue
    
#     return None


# def get_piper_command():
#     """Get the piper command/path to use"""
#     global _piper_cmd
#     if '_piper_cmd' not in globals():
#         _piper_cmd = check_piper_installed()
#     return _piper_cmd


# def check_pathvalidate():
#     """Check if pathvalidate is installed (required dependency)"""
#     try:
#         import pathvalidate
#         return True
#     except ImportError:
#         return False


# def list_downloaded_voices():
#     """List already downloaded Piper voices"""
#     data_dir = os.path.expanduser("~/.local/share/piper")
    
#     if not os.path.exists(data_dir):
#         return []
    
#     voices = []
#     for item in os.listdir(data_dir):
#         voice_dir = os.path.join(data_dir, item)
#         if os.path.isdir(voice_dir):
#             # Check if it has the required .onnx file
#             onnx_files = list(Path(voice_dir).glob("*.onnx"))
#             if onnx_files:
#                 voices.append(item)
    
#     return voices


# def download_voice(voice_name="en_US-lessac-medium"):
#     """Download a Piper voice using piper.download"""
#     print(f"\nDownloading voice: {voice_name}")
#     print("This may take a moment (~20MB)...")
    
#     try:
#         # Try using piper's download functionality
#         from piper.download import ensure_voice_exists, find_voice, get_voices
        
#         voices_info = get_voices(None, update_voices=True)
#         voice = find_voice(voice_name, [voices_info])
        
#         if not voice:
#             print(f"✗ Voice '{voice_name}' not found in voice list")
#             return False
        
#         data_dir = os.path.expanduser("~/.local/share/piper")
#         os.makedirs(data_dir, exist_ok=True)
        
#         model_path = ensure_voice_exists(voice_name, [voices_info], data_dir)
        
#         if model_path and os.path.exists(model_path):
#             print(f"✓ Successfully downloaded: {voice_name}")
#             return True
#         else:
#             print(f"✗ Failed to download voice")
#             return False
            
#     except ImportError:
#         print("✗ Piper download module not available")
#         print("\n  Manual download instructions:")
#         print(f"  mkdir -p ~/.local/share/piper/{voice_name}")
#         print(f"  cd ~/.local/share/piper/{voice_name}")
        
#         # Provide download URLs for common voices
#         if voice_name == "en_US-lessac-medium":
#             print("  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx")
#             print("  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json")
#         elif voice_name == "en_US-amy-medium":
#             print("  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx")
#             print("  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json")
#         else:
#             print(f"  # Visit: https://huggingface.co/rhasspy/piper-voices")
#             print(f"  # Search for: {voice_name}")
        
#         return False
#     except Exception as e:
#         print(f"✗ Error downloading voice: {e}")
#         return False


# def demo_piper_voice(text, voice_name, output_file, speed=1.0):
#     """Generate speech using Piper with a specific voice"""
#     print(f"\n{'='*60}")
#     print(f"Voice: {voice_name}")
#     print(f"{'='*60}")
    
#     try:
#         piper_cmd = get_piper_command()
#         if not piper_cmd:
#             print("✗ Piper not found")
#             return False
        
#         # Build command
#         cmd = [piper_cmd, "-m", voice_name, "-f", output_file]
        
#         # Add speed if not default
#         if speed != 1.0:
#             # Note: Piper doesn't have a direct speed parameter
#             # Speed is controlled by editing the .onnx.json file
#             print(f"Note: Speed control requires editing the voice config file")
#             print(f"      Current speed: 1.0 (default)")
        
#         print(f"Generating: {output_file}")
        
#         # Run Piper
#         result = subprocess.run(
#             cmd,
#             input=text,
#             text=True,
#             capture_output=True
#         )
        
#         if result.returncode == 0 and os.path.exists(output_file):
#             file_size = os.path.getsize(output_file)
#             print(f"✓ Successfully created {output_file}")
#             print(f"  File size: {file_size} bytes ({file_size/1024:.1f} KB)")
#             return True
#         else:
#             print(f"✗ Failed to generate speech")
#             if result.stderr:
#                 error_msg = result.stderr.strip()
                
#                 # Parse error and provide helpful feedback
#                 if "pathvalidate" in error_msg.lower():
#                     print(f"  Missing dependency: pathvalidate")
#                     print(f"  Install with: pip install pathvalidate --break-system-packages")
#                 elif "voice" in error_msg.lower() or "not found" in error_msg.lower():
#                     print(f"  Voice '{voice_name}' not found")
#                     print(f"  Available voices: {', '.join(list_downloaded_voices())}")
#                     print(f"\n  Download with: python3 piper_demo.py --download {voice_name}")
#                 else:
#                     print(f"  Error: {error_msg[:200]}")
#             return False
            
#     except Exception as e:
#         print(f"✗ Error: {e}")
#         return False


# def demo_multiple_voices(text, output_dir):
#     """Demo multiple Piper voices"""
#     # List of popular voices to try
#     voices = [
#         ("en_US-lessac-medium", "US Male - Clear professional voice"),
#         ("en_US-amy-medium", "US Female - Natural friendly voice"),
#         ("en_US-ryan-medium", "US Male - Young energetic voice"),
#         ("en_GB-alan-medium", "UK Male - British accent"),
#     ]
    
#     print("\n╔════════════════════════════════════════════════════════════╗")
#     print("║              Piper TTS - Multiple Voices Demo             ║")
#     print("╚════════════════════════════════════════════════════════════╝")
    
#     downloaded = list_downloaded_voices()
#     print(f"\nCurrently downloaded voices: {', '.join(downloaded) if downloaded else 'None'}")
    
#     success_count = 0
    
#     for voice_name, description in voices:
#         print(f"\n{description}")
        
#         # Check if voice is downloaded
#         if voice_name not in downloaded:
#             print(f"  Voice not downloaded. Attempting to download...")
#             if not download_voice(voice_name):
#                 print(f"  Skipping {voice_name}")
#                 continue
        
#         output_file = output_dir / f"{voice_name}.wav"
#         if demo_piper_voice(text, voice_name, str(output_file)):
#             success_count += 1
    
#     return success_count


# def main():
#     """Main function"""
#     import argparse
    
#     parser = argparse.ArgumentParser(description="Piper TTS Demo")
#     parser.add_argument("--text", "-t", default="hello there", help="Text to synthesize")
#     parser.add_argument("--voice", "-v", help="Specific voice to use")
#     parser.add_argument("--download", "-d", help="Download a specific voice")
#     parser.add_argument("--list", "-l", action="store_true", help="List downloaded voices")
#     parser.add_argument("--output", "-o", help="Output file path")
    
#     args = parser.parse_args()
    
#     # Check if Piper is installed
#     piper_cmd = check_piper_installed()
#     if not piper_cmd:
#         print("✗ Piper is not installed or not in PATH")
#         print("\nPossible solutions:")
#         print("  1. Activate your virtual environment:")
#         print("     source .venv/bin/activate")
#         print("  2. Install Piper:")
#         print("     pip install piper-tts pathvalidate")
#         print("  3. Use full path:")
#         print("     .venv/bin/piper --version")
#         print("\nFor more help, see: VENV_PIPER_FIX.md")
#         sys.exit(1)
    
#     # Store for later use
#     global _piper_cmd
#     _piper_cmd = piper_cmd
    
#     # Check pathvalidate
#     if not check_pathvalidate():
#         print("⚠ Warning: pathvalidate not installed")
#         print("  Install with: pip install pathvalidate --break-system-packages")
#         print()
    
#     # Handle --list
#     if args.list:
#         voices = list_downloaded_voices()
#         if voices:
#             print("\nDownloaded voices:")
#             for v in voices:
#                 print(f"  • {v}")
#         else:
#             print("\nNo voices downloaded yet")
#             print("Download a voice with: python3 piper_demo.py --download en_US-lessac-medium")
#         return
    
#     # Handle --download
#     if args.download:
#         download_voice(args.download)
#         return
    
#     # Create output directory
#     output_dir = Path("piper_outputs")
#     output_dir.mkdir(exist_ok=True)
    
#     # Demo specific voice or multiple voices
#     if args.voice:
#         # Single voice demo
#         output_file = args.output or str(output_dir / f"{args.voice}.wav")
#         print(f"\nText to synthesize: '{args.text}'")
        
#         downloaded = list_downloaded_voices()
#         if args.voice not in downloaded:
#             print(f"\nVoice '{args.voice}' not downloaded. Downloading...")
#             if not download_voice(args.voice):
#                 print("\nFailed to download voice. Exiting.")
#                 sys.exit(1)
        
#         demo_piper_voice(args.text, args.voice, output_file)
#     else:
#         # Multiple voices demo
#         success_count = demo_multiple_voices(args.text, output_dir)
        
#         print("\n" + "="*60)
#         print("Demo Complete!")
#         print("="*60)
#         print(f"\nSuccessfully generated {success_count} audio files")
#         print(f"Output directory: {output_dir}/")
        
#         # List generated files
#         files = sorted(output_dir.glob("*.wav"))
#         if files:
#             print("\nGenerated files:")
#             for f in files:
#                 size = f.stat().st_size
#                 print(f"  • {f.name} ({size/1024:.1f} KB)")
        
#         print("\nTo play audio files:")
#         print("  mpv piper_outputs/*.wav")
#         print("  # or")
#         print("  aplay piper_outputs/*.wav")
    
#     print("\n" + "="*60)
#     print("Tips:")
#     print("="*60)
#     print("• List voices: python3 piper_demo.py --list")
#     print("• Download voice: python3 piper_demo.py --download en_GB-alan-medium")
#     print("• Use specific voice: python3 piper_demo.py --voice en_US-amy-medium")
#     print("• Custom text: python3 piper_demo.py --text 'Your custom text here'")
#     print("\nBrowse all voices: https://github.com/rhasspy/piper/blob/master/VOICES.md")


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         print("\n\nInterrupted by user.")
#         sys.exit(0)