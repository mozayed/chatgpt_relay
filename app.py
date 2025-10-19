from flask import Flask, request
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv
import threading

load_dotenv()

app = Flask(__name__)
sock = Sock(app)

@app.route("/voice/incoming", methods=['POST'])
def incoming_call():
    """Answer call and connect to WebSocket"""
    response = VoiceResponse()
    response.say("Connecting you to ChatGPT")
    
    connect = Connect()
    connect.stream(url=f'wss://{request.host}/voice/stream')
    response.append(connect)
    
    return str(response)

@sock.route('/voice/stream')
def handle_stream(ws):
    """Bridge Twilio audio to ChatGPT"""
    print("WebSocket connected", flush=True)
    
    # Run async bridge in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bridge_audio(ws))
    except Exception as e:
        print(f"Handler error: {e}", flush=True)
    finally:
        loop.close()

async def bridge_audio(ws):
    """Async bridge function"""
    stream_sid = None
    openai_ws = None
    
    try:
        # Connect to ChatGPT
        print("Connecting to OpenAI...", flush=True)
        openai_ws = await websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
            additional_headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "OpenAI-Beta": "realtime=v1"
            }
        )
        
        print("Connected to OpenAI!", flush=True)
        
        # Configure session
        await openai_ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw"
            }
        }))
        
        print("Session configured", flush=True)
        
        # Handle messages
        twilio_task = asyncio.create_task(handle_twilio_messages(ws, openai_ws))
        openai_task = asyncio.create_task(handle_openai_messages(openai_ws, ws))
        
        # Wait for both tasks
        await asyncio.gather(twilio_task, openai_task, return_exceptions=True)
        
    except Exception as e:
        print(f"Bridge error: {e}", flush=True)
    finally:
        if openai_ws:
            await openai_ws.close()
        print("Bridge closed", flush=True)

async def handle_twilio_messages(ws, openai_ws):
    """Handle messages from Twilio"""
    try:
        print("Listening for Twilio messages...", flush=True)
        while True:
            msg = ws.receive()
            if not msg:
                break
                
            data = json.loads(msg)
            
            if data['event'] == 'start':
                print(f"Stream started: {data['start']['streamSid']}", flush=True)
                
            elif data['event'] == 'media':
                # Forward audio to OpenAI
                await openai_ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": data['media']['payload']
                }))
                
            elif data['event'] == 'stop':
                print("Stream stopped", flush=True)
                break
                
    except Exception as e:
        print(f"Twilio handler error: {e}", flush=True)

async def handle_openai_messages(openai_ws, ws):
    """Handle messages from OpenAI"""
    stream_sid = None
    
    try:
        print("Listening for OpenAI messages...", flush=True)
        
        # Get stream SID from first Twilio message
        first_msg = ws.receive()
        if first_msg:
            data = json.loads(first_msg)
            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                print(f"Got stream SID: {stream_sid}", flush=True)
        
        async for msg in openai_ws:
            event = json.loads(msg)
            event_type = event.get('type', '')
            
            if event_type == 'response.audio.delta' and stream_sid:
                # Forward audio to Twilio
                ws.send(json.dumps({
                    'event': 'media',
                    'streamSid': stream_sid,
                    'media': {'payload': event['delta']}
                }))
                
            elif event_type == 'conversation.item.input_audio_transcription.completed':
                print(f"You: {event.get('transcript', '')}", flush=True)
                
            elif event_type == 'error':
                print(f"OpenAI error: {event}", flush=True)
                
    except Exception as e:
        print(f"OpenAI handler error: {e}", flush=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
