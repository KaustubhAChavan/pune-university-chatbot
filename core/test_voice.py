# test_voice.py
import os
from voice_service import voice_service
from dotenv import load_dotenv

load_dotenv()

# Print environment variables (without revealing full API key)
api_key = os.getenv("ELEVENLABS_API_KEY", "")
voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")

print(f"API Key exists: {'Yes' if api_key else 'No'}")
print(f"API Key starts with: {api_key[:5]}..." if api_key else "No API key found")
print(f"Voice ID exists: {'Yes' if voice_id else 'No'}")
print(f"Voice ID: {voice_id}" if voice_id else "No Voice ID found")

# Test text-to-speech
test_text = "Hello, this is a test of the Eleven Labs voice service."
print("Generating audio...")
audio_url = voice_service.text_to_speech_for_twilio(test_text)

print(f"Generated audio URL: {audio_url}")
print("Test completed. Check the static/audio_cache folder for the audio file.")