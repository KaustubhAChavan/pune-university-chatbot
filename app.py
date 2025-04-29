from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from core.langchain_bot import process_query
from core.twilio_service import twilio_service
from core.voice_service import voice_service  # type: ignore
import os
from dotenv import load_dotenv
import time
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Store conversation history
conversation_histories = {}

@app.route('/')
def index():
    """Render the main HTML page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat API endpoint"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        voice_enabled = data.get('voice_enabled', False)  # New parameter for voice responses
        
        # Get conversation history for this session
        conversation_history = conversation_histories.get(session_id, [])
        
        # Process the query
        start_time = time.time()
        response, updated_history = process_query(user_message, conversation_history)
        processing_time = time.time() - start_time
        
        # Update the conversation history
        conversation_histories[session_id] = updated_history
        
        # Log the interaction
        print(f"[{session_id}] User: {user_message}")
        print(f"[{session_id}] Bot: {response}")
        print(f"[{session_id}] Processing time: {processing_time:.2f} seconds")
        
        result = {
            'response': response,
            'processingTime': round(processing_time, 2)
        }
        
        # Generate voice response if requested
        if voice_enabled:
            try:
                audio_url = voice_service.text_to_speech_for_twilio(response)
                if audio_url:
                    result['audio_url'] = audio_url
                    print(f"[{session_id}] Generated audio: {audio_url}")
            except Exception as e:
                print(f"Error generating voice response: {str(e)}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Sorry, there was an error processing your request.',
            'details': str(e)
        }), 500

@app.route('/api/voice', methods=['POST'])
def generate_voice():
    """Generate voice for a given text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Generate voice using ElevenLabs
        audio_url = voice_service.text_to_speech_for_twilio(text)
        
        if audio_url:
            return jsonify({'audio_url': audio_url})
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    
    except Exception as e:
        print(f"Error in voice generation endpoint: {str(e)}")
        return jsonify({
            'error': 'Sorry, there was an error generating the voice.',
            'details': str(e)
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset conversation history"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        # Clear the conversation history
        conversation_histories[session_id] = []
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation reset successfully.'
        })
    
    except Exception as e:
        print(f"Error in reset endpoint: {str(e)}")
        return jsonify({
            'error': 'Sorry, there was an error resetting the conversation.'
        }), 500

@app.route('/static/audio_cache/<filename>')
def serve_audio(filename):
    """Serve cached audio files"""
    filename = secure_filename(filename)
    return send_from_directory('static/audio_cache', filename)

# Twilio SMS webhook
@app.route('/api/sms', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS messages via Twilio"""
    try:
        # Get the message content from Twilio request
        incoming_msg = request.form.get('Body', '')
        sender = request.form.get('From', '')
        
        # Use the sender's phone number as session ID
        session_id = f"sms_{sender}"
        conversation_history = conversation_histories.get(session_id, [])
        
        # Process the query
        response, updated_history = process_query(incoming_msg, conversation_history)
        
        # Update conversation history
        conversation_histories[session_id] = updated_history
        
        # Return a TwiML response
        return f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>{response}</Message>
        </Response>
        """
    
    except Exception as e:
        print(f"Error in SMS webhook: {str(e)}")
        return f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>Sorry, there was an error processing your request.</Message>
        </Response>
        """

# Twilio Voice webhooks
@app.route('/api/voice/welcome', methods=['POST'])
def voice_welcome():
    """Handle incoming voice calls"""
    try:
        # Generate welcome message
        welcome_message = "Welcome to the Pune University chatbot. How can I help you today?"
        
        # Generate audio using ElevenLabs
        audio_url = voice_service.text_to_speech_for_twilio(welcome_message)
        
        if audio_url:
            # Use the generated audio
            resp = f"""
            <?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Play>{audio_url}</Play>
                <Gather input="speech" action="/api/voice/process" method="POST" speechTimeout="auto" language="en-IN">
                    <Say>Please ask your question after the beep.</Say>
                </Gather>
            </Response>
            """
        else:
            # Fallback to Twilio's TTS
            resp = twilio_service.generate_welcome_twiml()
            
        return Response(resp, mimetype='text/xml')
    
    except Exception as e:
        print(f"Error in voice welcome endpoint: {str(e)}")
        resp = """
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Sorry, there was an error with our service. Please try again later.</Say>
            <Hangup/>
        </Response>
        """
        return Response(resp, mimetype='text/xml')

@app.route('/api/voice/process', methods=['POST'])
def voice_process():
    """Process voice input from user"""
    try:
        # Get the caller's number
        caller = request.form.get('From', '')
        # Get speech input
        user_input = request.form.get('SpeechResult', '')
        
        if not user_input:
            # If no speech detected
            resp = twilio_service.generate_response_twiml(
                "I didn't catch that. Could you please repeat?",
                gather_again=True
            )
            return Response(resp, mimetype='text/xml')
        
        # Use the caller's number as session ID
        session_id = f"voice_{caller}"
        conversation_history = conversation_histories.get(session_id, [])
        
        # Process the query
        response, updated_history = process_query(user_input, conversation_history)
        
        # Update conversation history
        conversation_histories[session_id] = updated_history
        
        # Generate audio using ElevenLabs
        audio_url = voice_service.text_to_speech_for_twilio(response)
        
        if audio_url:
            # Use the ElevenLabs generated audio
            resp = f"""
            <?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Play>{audio_url}</Play>
                <Pause length="1"/>
                <Gather input="speech" action="/api/voice/process" method="POST" speechTimeout="auto" language="en-IN">
                    <Say>Do you have another question?</Say>
                </Gather>
            </Response>
            """
        else:
            # Fallback to Twilio's TTS
            resp = twilio_service.generate_response_twiml(response, gather_again=True)
            
        return Response(resp, mimetype='text/xml')
    
    except Exception as e:
        print(f"Error in voice process endpoint: {str(e)}")
        resp = """
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Sorry, there was an error processing your request. Please try again.</Say>
            <Hangup/>
        </Response>
        """
        return Response(resp, mimetype='text/xml')

# New route to check ElevenLabs connectivity
@app.route('/api/check-voice', methods=['GET'])
def check_voice():
    """Check if ElevenLabs integration is working"""
    try:
        test_message = "This is a test of the ElevenLabs voice integration."
        audio_url = voice_service.text_to_speech_for_twilio(test_message)
        
        if audio_url:
            return jsonify({
                'status': 'success',
                'message': 'ElevenLabs integration is working correctly.',
                'audio_url': audio_url
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate audio with ElevenLabs.'
            }), 500
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking ElevenLabs integration: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)