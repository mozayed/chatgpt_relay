from flask import Flask, request
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

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
    
    async def bridge():
        try:
            # Connect to ChatGPT
            print("Attempting OpenAI connection...", flush=True)
            openai_ws = await websockets.connect(
                "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
                additional_headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "OpenAI-Beta": "realtime=v1"
                }
            )
            
            print("ChatGPT connected!", flush=True)
            
            # Check for immediate error from OpenAI
            try:
                first_msg = await asyncio.wait_for(openai_ws.recv(), timeout=2.0)
                event = json.loads(first_msg)
                print(f"First OpenAI message: {event}", flush=True)
                
                if event.get('type') == 'error':
                    print(f"OpenAI Error: {event}", flush=True)
                    return
            except asyncio.TimeoutError:
                print("No immediate message from OpenAI", flush=True)
            
            # Your voice → ChatGPT
            async def twilio_to_chatgpt():
                while True:
                    msg = ws.receive()
                    if not msg:
                        break
                    data = json.loads(msg)
                    if data['event'] == 'media':
                        await openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }))
            
            # ChatGPT → Your phone
            async def chatgpt_to_twilio():
                async for msg in openai_ws:
                    event = json.loads(msg)
                    if event['type'] == 'response.audio.delta':
                        ws.send(json.dumps({
                            'event': 'media',
                            'media': {'payload': event['delta']}
                        }))
            
            await asyncio.gather(twilio_to_chatgpt(), chatgpt_to_twilio())
            
        except Exception as e:
            print(f"Bridge error: {e}", flush=True)
    
    asyncio.run(bridge())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
