# routes/onprem.py - new

from flask import Blueprint, jsonify, request

onprem_bp = Blueprint('onprem', __name__)

# Injected dependency
_onprem_bridge = None

def init_onprem_routes(onprem_bridge):
    """Initialize onprem routes with OnPremBridge"""
    global _onprem_bridge
    _onprem_bridge = onprem_bridge
    print("✓ OnPrem routes initialized", flush=True)

@onprem_bp.route("/poll", methods=['GET'])
def poll():
    """On-prem poller gets pending requests"""
    request_data = _onprem_bridge.get_pending_request()
    return jsonify(request_data)

@onprem_bp.route("/submit_response", methods=['POST'])
def submit_response():
    """On-prem poller submits results"""
    req_id = request.json['id']
    result_data = request.json['result']
    _onprem_bridge.submit_response(req_id, result_data)
    return jsonify({"status": "received"})