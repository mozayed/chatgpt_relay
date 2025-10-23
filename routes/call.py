import asyncio, threading, requests, os, json
from flask import Blueprint, Response, request
from models.voice_call import VoiceCall
from models.tools import Tools
from models.llm_services import OpenAiService

call_bp = Blueprint('call', __name__)
tools = Tools()



@call_bp.route("/webhook", methods=['POST'])
def webhook():
    """Receive incoming call webhook from OpenAI"""
    
    try:
        openai_service = OpenAiService()
        event = openai_service.openai_client.webhooks.unwrap(request.data, request.headers)
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
                json= {
                    "type": "realtime",
                    "model": "gpt-4o-realtime-preview-2024-10-01",
                    "instructions": "You are an AI network agent. You can check device VLANs and answer questions about ServiceNow tickets. When the user asks about tickets or complex questions, use the ask_claude function.",
                    "tools": [
                        {
                            "type": "function",
                            "name": "get_device_vlans",
                            "description": "Gets VLAN data for a network device",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device_name": {
                                        "type": "string",
                                        "description": "Name of the device like 'ground floor switch' or 'Cisco test switch'"
                                    }
                                },
                                "required": ["device_name"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "check_servicenow",
                            "description": "Ask OpenAI (the AI brain) about ServiceNow tickets, complex network issues, or any questions requiring deep analysis. Use this for ticket queries like 'What is the status of ticket INC001?'",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The question to ask OpenAi, including ticket numbers if mentioned"
                                    }
                                },
                                "required": ["question"]
                            }
                        }
                    ]
                }
                    
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
