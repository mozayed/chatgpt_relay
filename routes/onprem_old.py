from flask import Blueprint, jsonify, request
from models.jobs import Jobs

onprem_bp = Blueprint('onprem', __name__)
current_jobs = Jobs() 


@onprem_bp.route("/poll", methods=['GET'])
def poll():
    """On-prem polls for pending requests towards the Network Mgmt App"""
    if current_jobs.pending_requests:
        return jsonify(current_jobs.pending_requests.pop(0))
    return jsonify(None)

@onprem_bp.route("/submit_response", methods=['POST'])
def submit_response():
    """On-prem submits response"""
    req_id = request.json['id']
    result_data = request.json['result']
    current_jobs.responses[req_id] = result_data
    print(f"*** STORED RESPONSE for {req_id}", flush=True)
    return jsonify({"status": "received"})