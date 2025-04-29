import os
import time
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class VoiceService:
    def __init__(self):
        # Get API key and voice ID from environment variables
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.api_url = "https://api.elevenlabs.io/v1/text-to-speech"
        
        # Create directory for audio cache if it doesn't exist
        self.cache_dir = Path("static/audio_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def text_to_speech_for_twilio(self, text: str) -> Optional[str]:
        """Convert text to speech and return URL for Twilio to play"""
        try:
            # Prepare the API request
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            # Make the API request
            url = f"{self.api_url}/{self.voice_id}"
            response = requests.post(url, json=payload, headers=headers)
            
            # Check if the request was successful
            if response.status_code != 200:
                print(f"ElevenLabs API error: {response.status_code}, {response.text}")
                return None
                
            # Generate a unique filename
            filename = f"tts_{int(time.time())}.mp3"
            file_path = self.cache_dir / filename
            
            # Save the audio file
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            # Return the URL for Twilio to access
            base_url = os.getenv("BASE_URL", "http://localhost:5000")
            return f"{base_url}/static/audio_cache/{file_path.name}"
                
        except Exception as e:
            print(f"Error in text-to-speech conversion: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

# Create an instance for easy importing
voice_service = VoiceService()