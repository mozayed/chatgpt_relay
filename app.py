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
        stream_sid = None
        
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
            
            # Configure session for Twilio's audio format
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw",
                    "turn_detection": {
                        "type": "server_vad"
                    }
                }
            }))
            print("Session configured for Twilio audio", flush=True)
            
            # Your voice → ChatGPT
            async def twilio_to_chatgpt():
                nonlocal stream_sid
                try:
                    print("Starting Twilio→ChatGPT stream...", flush=True)
                    while True:
                        msg = ws.receive()
                        if not msg:
                            print("Twilio connection closed", flush=True)
                            break
                        
                        data = json.loads(msg)
                        
                        if data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            print(f"Twilio stream started, SID: {stream_sid}", flush=True)
                            
                        elif data['event'] == 'media':
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }))
                            
                        elif data['event'] == 'stop':
                            print("Twilio stream stopped", flush=True)
                            break
                            
                except Exception as e:
                    print(f"Twilio→ChatGPT error: {e}", flush=True)
                finally:
                    await openai_ws.close()
            
            # ChatGPT → Your phone
            async def chatgpt_to_twilio():
                try:
                    print("Starting ChatGPT→Twilio stream...", flush=True)
                    
                    async for msg in openai_ws:
                        event = json.loads(msg)
                        event_type = event.get('type', '')
                        
                        if event_type == 'response.audio.delta':
                            if stream_sid:
                                ws.send(json.dumps({
                                    'event': 'media',
                                    'streamSid': stream_sid,
                                    'media': {'payload': event['delta']}
                                }))
                                
                        elif event_type == 'conversation.item.input_audio_transcription.completed':
                            print(f"\nYou said: {event.get('transcript', 'N/A')}", flush=True)
                            
                        elif event_type == 'response.done':
                            print("\nChatGPT finished responding", flush=True)
                            
                        elif event_type == 'error':
                            print(f"\nOpenAI error: {event}", flush=True)
                            
                except Exception as e:
                    print(f"ChatGPT→Twilio error: {e}", flush=True)
            
            await asyncio.gather(twilio_to_chatgpt(), chatgpt_to_twilio())
            
        except Exception as e:
            print(f"Bridge error: {e}", flush=True)
    
    asyncio.run(bridge())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
