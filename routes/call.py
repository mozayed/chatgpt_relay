import asyncio, threading, requests, os
from flask import Blueprint, Response, request
from models.voice_call import VoiceCall
from models.voice_agent import VoiceAgent
from models.tools import Tools

call_bp = Blueprint('call', __name__)

voice_agent = VoiceAgent()
tools = Tools()

@call_bp.route("/webhook", methods=['POST'])
def webhook():
    """Receive incoming call webhook from OpenAI"""
    
    try:
        event = voice_agent.openai_client.webhooks.unwrap(request.data, request.headers)
    except Exception as e:
        print(f"Invalid webhook: {e}", flush=True)
        return Response("Invalid signature", status=400)
    
    if event.type == 'realtime.call.incoming':
        call_id = event.data.call_id
        voice_call = VoiceCall(call_id)
        print(f"Incoming call: {call_id}", flush=True)
        
        # Accept the call with tools
        try:
            response = requests.post(
                f"https://api.openai.com/v1/realtime/calls/{call_id}/accept",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={tools.get_tools()}
                    
            )
            print(f"Accept response: {response.status_code}", flush=True)
            
            # Start monitoring in background
            threading.Thread(
                target=lambda: asyncio.run(voice_call.monitor_call()),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Accept call failed: {e}", flush=True)
        
        return Response(status=200)
    
    return Response(status=200)
