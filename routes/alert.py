import os
from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Dial
from models.alerts import Alert
from models.voice_agent import VoiceAgent
from models.engineer import Engineer
from urllib.parse import quote

alert_bp = Blueprint('alert', __name__)

@alert_bp.route("/trigger_alert", methods=['POST'])
def trigger_alert():
    """Receive alert from Grafana and trigger a phone call"""

    voice_agent = VoiceAgent()
    engineer = Engineer()
    alert = Alert()

    data = request.json
    alert_message = data.get('message', 'Critical network alert')
    alert.add_alert(alert_message)
    
    print(f"Triggering alert call to {engineer.phone_number}: {alert_message}", flush=True)
    
    try:
        encoded_message = quote(alert_message)
        
        call = voice_agent.twilio_client.calls.create(
            to=engineer.phone_number,
            from_=voice_agent.twilio_client,
            url=f"https://{request.host}/alert_twiml?message={encoded_message}"
        )
        print(f"Alert call initiated: {call.sid}", flush=True)
        return jsonify({"status": "success", "call_sid": call.sid})
    
    except Exception as e:
        print(f"Failed to trigger alert: {e}", flush=True)
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