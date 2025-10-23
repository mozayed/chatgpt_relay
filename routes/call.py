from flask import Blueprint, Response, request, jsonify
from openai import OpenAI
import os

call_bp = Blueprint('call', __name__)

# Module-level references
_voice_agent = None
_onprem_bridge = None
_openai_client = None

def init_call_routes(voice_agent, onprem_bridge):
    """Initialize routes with dependencies"""
    global _voice_agent, _onprem_bridge, _openai_client
    _voice_agent = voice_agent
    _onprem_bridge = onprem_bridge
    _openai_client = OpenAI(webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET"))
    print("✓ Call routes initialized", flush=True)

@call_bp.route("/webhook", methods=['POST'])
def webhook():
    """Receive incoming call webhook from OpenAI"""
    try:
        event = _openai_client.webhooks.unwrap(request.data, request.headers)
    except Exception as e:
        print(f"❌ Invalid webhook: {e}", flush=True)
        return Response("Invalid signature", status=400)
    
    _voice_agent.handle_webhook(event)
    return Response(status=200)

@call_bp.route("/poll", methods=['GET'])
def poll():
    """On-prem polls for pending requests"""
    request_data = _onprem_bridge.get_pending_request()
    return jsonify(request_data)

@call_bp.route("/submit_response", methods=['POST'])
def submit_response():
    """On-prem submits response"""
    req_id = request.json['id']
    result_data = request.json['result']
    _onprem_bridge.submit_response(req_id, result_data)
    return jsonify({"status": "received"})

# Keep your existing alert routes if you have them