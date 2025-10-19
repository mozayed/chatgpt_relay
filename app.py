from flask import Flask, request, Response, jsonify
from openai import OpenAI
import os
import requests
import threading
import asyncio
import websockets
import json
import uuid
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial

app = Flask(__name__)

client = OpenAI(
    webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET")
)

# Twilio credentials
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Queue system
pending_requests = []
responses = {}

@app.route("/poll", methods=['GET'])
def poll():
    """On-prem polls for pending requests"""
    if pending_requests:
        return jsonify(pending_requests.pop(0))
    return jsonify(None)

@app.route("/submit_response", methods=['POST'])
def submit_response():
    """On-prem submits response"""
    req_id = request.json['id']
    result_data = request.json['result']
    responses[req_id] = result_data
    print(f"*** STORED RESPONSE for {req_id}", flush=True)
    return jsonify({"status": "received"})

# NEW: Alert endpoints
@app.route("/trigger_alert", methods=['POST'])
def trigger_alert():
    """Receive alert from Grafana and trigger phone call"""
    data = request.json
    alert_message = data.get('message', 'Critical network alert')
    your_phone = data.get('phone', os.getenv("YOUR_PHONE_NUMBER"))
    
    print(f"Triggering alert call to {your_phone}: {alert_message}", flush=True)
    
    try:
        # URL encode the message properly
        from urllib.parse import quote
        encoded_message = quote(alert_message)
        
        call = twilio_client.calls.create(
            to=your_phone,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url=f"https://{request.host}/alert_twiml?message={encoded_message}"
        )
        print(f"Alert call initiated: {call.sid}", flush=True)
        return jsonify({"status": "success", "call_sid": call.sid})
    except Exception as e:
        print(f"Failed to trigger alert: {e}", flush=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/alert_twiml", methods=['POST'])
def alert_twiml():
    """Generate TwiML for alert call"""
    alert_message = request.args.get('message', 'Network alert')
    
    response = VoiceResponse()
    response.say(f"Alert: {alert_message}")
    response.pause(length=1)
    
    gather = response.gather(
        num_digits=1,
        action='/alert_response',
        timeout=10
    )
    gather.say("Press 1 to talk to the AI assistant for investigation, or hang up.")
    
    response.say("No input received. Goodbye.")
    return str(response)

@app.route("/alert_response", methods=['POST'])
def alert_response():
    """Handle user's response to alert"""
    digit = request.form.get('Digits', '')
    
    response = VoiceResponse()
    
    if digit == '1':
        response.say("Connecting you to the AI assistant.")
        dial = Dial()
        dial.sip(f"sip:{os.getenv('OPENAI_PROJECT_ID')}@sip.api.openai.com;transport=tls")
        response.append(dial)
    else:
        response.say("Goodbye.")
    
    return str(response)

async def monitor_call(call_id):
    """Monitor call and handle function calls"""
    try:
        async with websockets.connect(
            f"wss://api.openai.com/v1/realtime?call_id={call_id}",
            additional_headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
            }
        ) as ws:
            print(f"Monitoring call {call_id}", flush=True)
            
            async for message in ws:
                event = json.loads(message)
                event_type = event.get('type', '')
                
                if event_type == 'response.function_call_arguments.done':
                    call_data = event
                    function_name = call_data.get('name', '')
                    arguments = json.loads(call_data.get('arguments', '{}'))
                    
                    print(f"Function call: {function_name} with {arguments}", flush=True)
                    
                    if function_name == 'get_device_vlans':
                        device_name = arguments.get('device_name', '')
                        
                        # Queue request for on-prem
                        req_id = str(uuid.uuid4())
                        req_data = {
                            "id": req_id,
                            "tool": "get_device_vlans",
                            "params": {"device_name": device_name},
                            "timestamp": datetime.now().isoformat()
                        }
                        pending_requests.append(req_data)
                        print(f"Queued request {req_id}", flush=True)
                        
                        # Wait for response from on-prem
                        import time
                        timeout = 10
                        start = time.time()
                        while req_id not in responses:
                            if time.time() - start > timeout:
                                result_text = "Sorry, request timed out"
                                break
                            await asyncio.sleep(0.5)
                        else:
                            result = responses.pop(req_id)
                            result_text = f"VLANs: {json.dumps(result)}"
                        
                        print(f"Got result: {result_text}", flush=True)
                        
                        # Send result back to ChatGPT
                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_data.get('call_id'),
                                "output": result_text
                            }
                        }))
                        
    except Exception as e:
        print(f"Monitor error: {e}", flush=True)

@app.route("/webhook", methods=['POST'])
def webhook():
    """Receive incoming call webhook from OpenAI"""
    
    try:
        event = client.webhooks.unwrap(request.data, request.headers)
    except Exception as e:
        print(f"Invalid webhook: {e}", flush=True)
        return Response("Invalid signature", status=400)
    
    if event.type == 'realtime.call.incoming':
        call_id = event.data.call_id
        print(f"Incoming call: {call_id}", flush=True)
        
        # Accept the call with tools
        try:
            response = requests.post(
                f"https://api.openai.com/v1/realtime/calls/{call_id}/accept",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "realtime",
                    "model": "gpt-4o-realtime-preview-2024-10-01",
                    "instructions": "You are a network assistant. You can check device VLANs for network devices.",
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
                        }
                    ]
                }
            )
            print(f"Accept response: {response.status_code}", flush=True)
            
            # Start monitoring in background
            threading.Thread(
                target=lambda: asyncio.run(monitor_call(call_id)),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Accept call failed: {e}", flush=True)
        
        return Response(status=200)
    
    return Response(status=200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
