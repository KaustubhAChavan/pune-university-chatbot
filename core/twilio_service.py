from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
# from core.voice_service import voice_service  # Comment out this import
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a stub implementation of voice_service
class VoiceStub:
    """Stub implementation of voice service when ElevenLabs is not available"""
    
    def text_to_speech(self, text):
        print(f"Voice feature disabled - would have converted to speech: {text}")
        return None
        
    def text_to_speech_for_twilio(self, text):
        print(f"Voice feature disabled - would have converted to speech: {text}")
        return None

# Replace the imported voice_service with our stub
voice_service = VoiceStub()

class TwilioService:
    """Service for handling Twilio voice and SMS interactions"""
    
    def __init__(self):
        """Initialize Twilio service"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # Initialize Twilio client if credentials are available
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("Warning: Twilio credentials not found in environment variables")
    
    def generate_welcome_twiml(self) -> str:
        """Generate TwiML for welcome message"""
        response = VoiceResponse()
        
        # Convert welcome message to speech and get URL
        welcome_text = "Welcome to Pune University support chatbot. How can I help you today?"
        audio_url = voice_service.text_to_speech_for_twilio(welcome_text)
        
        if audio_url:
            # Use the generated audio file
            response.play(audio_url)
        else:
            # Fallback to Twilio's basic TTS
            response.say(welcome_text)
        
        gather = Gather(
            input='speech',
            action='/api/voice/process',
            method='POST',
            speech_timeout='auto',
            language='en-IN'
        )
        
        # Add prompt to gather
        prompt_text = "Please speak after the tone."
        prompt_audio = voice_service.text_to_speech_for_twilio(prompt_text)
        if prompt_audio:
            gather.play(prompt_audio)
        else:
            gather.say(prompt_text)
            
        response.append(gather)
        
        # If no input is received, retry
        response.redirect('/api/voice/welcome')
        
        return str(response)
    
    def generate_response_twiml(self, message: str, gather_again: bool = True) -> str:
        """Generate TwiML for bot response with human-like voice"""
        response = VoiceResponse()
        
        # Convert bot message to speech and get URL
        audio_url = voice_service.text_to_speech_for_twilio(message)
        
        if audio_url:
            # Use the generated audio file
            response.play(audio_url)
        else:
            # Fallback to Twilio's basic TTS
            response.say(message)
        
        if gather_again:
            gather = Gather(
                input='speech',
                action='/api/voice/process',
                method='POST',
                speech_timeout='auto',
                language='en-IN'
            )
            
            # Add follow-up prompt
            prompt_text = "Is there anything else I can help you with?"
            prompt_audio = voice_service.text_to_speech_for_twilio(prompt_text)
            
            if prompt_audio:
                gather.play(prompt_audio)
            else:
                gather.say(prompt_text)
                
            response.append(gather)
            
            # If no input is received, end the call with goodbye message
            goodbye_text = "Thank you for calling Pune University support. Goodbye!"
            goodbye_audio = voice_service.text_to_speech_for_twilio(goodbye_text)
            
            if goodbye_audio:
                response.play(goodbye_audio)
            else:
                response.say(goodbye_text)
                
            response.hangup()
        
        return str(response)
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message using Twilio"""
        if not self.client:
            print("Error: Twilio client not initialized")
            return False
        
        try:
            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            return True
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return False

# Initialize a global instance
twilio_service = TwilioService()