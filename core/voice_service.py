import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VoiceService:
    """Stub service for text-to-speech conversion (ElevenLabs disabled)"""
    
    def __init__(self):
        """Initialize voice service stub"""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
        
        # Create audio cache directory
        self.cache_dir = Path("static/audio_cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        print("Voice service initialized in STUB mode (ElevenLabs disabled)")
    
    def text_to_speech(self, text):
        """Stub implementation - returns None"""
        print(f"STUB: Would convert to speech: {text}")
        return None
    
    def text_to_speech_for_twilio(self, text):
        """Stub implementation - returns None"""
        print(f"STUB: Would convert to speech for Twilio: {text}")
        return None

# Initialize a global instance
voice_service = VoiceService()