import os, json
from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Dial
from urllib.parse import quote

alert_bp = Blueprint('alert', __name__)

# Module-level references (set by init)
_alert_service = None
_engineer = None
_twilio_client = None

def init_alert_routes(alert_service, engineer, twilio_client):
    """Initialize alert routes with dependencies"""
    global _alert_service, _engineer, _twilio_client
    _alert_service = alert_service
    _engineer = engineer
    _twilio_client = twilio_client
    print("✓ Alert routes initialized", flush=True)

@alert_bp.route("/trigger_alert", methods=['POST'])
def trigger_alert():
    """Receive alert from Grafana and trigger a phone call"""
    data = request.json
  
    # alert_message = data.get('message', 'Critical network alert')
    if data.get('alerts') and len(data['alerts']) > 0:
        alert = data['alerts'][0]
        annotations = alert.get('annotations', {})
        alert_message = annotations.get('summary', data.get('title', 'Network Alert'))
    
    # Store alert
    _alert_service.add_alert(alert_message)
    
    print(f"Triggering alert call to {_engineer.phone_number}: {alert_message}", flush=True)
    
    try:
        encoded_message = quote(alert_message)
        twiml_url = f"https://{request.host}/alert_twiml?message={encoded_message}"
        
        call = _twilio_client.make_call(_engineer.phone_number, twiml_url)
        
        if call:
            print(f"✓ Alert call initiated: {call.sid}", flush=True)
            return jsonify({"status": "success", "call_sid": call.sid})
        else:
            return jsonify({"status": "error", "message": "Failed to initiate call"}), 500
    
    except Exception as e:
        print(f"❌ Failed to trigger alert: {e}", flush=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@alert_bp.route("/alert_twiml", methods=['POST'])
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
    gather.say("Press 1 to talk to the AI agent for investigation, or hang up.")
    
    response.say("No input received. Goodbye.")
    return str(response)

@alert_bp.route("/alert_response", methods=['POST'])
def alert_response():
    """Handle user's response to alert"""
    digit = request.form.get('Digits', '')
    
    response = VoiceResponse()
    
    if digit == '1':
        response.say("Connecting you to the AI agent.")
        dial = Dial()
        dial.sip(f"sip:{os.getenv('OPENAI_PROJECT_ID')}@sip.api.openai.com;transport=tls")
        response.append(dial)
    else:
        response.say("Goodbye.")
    
    return str(response)