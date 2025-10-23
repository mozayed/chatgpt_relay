import os
import threading
from flask import Flask
from dotenv import load_dotenv

from models.servicenow import ServiceNow
from models.onprem_bridge import OnPremBridge
from models.agent import NetworkAgent
from models.voice_agent import VoiceAgent
from models.llm_factory import AbstractLLMServiceFactory

from routes.call import call_bp, init_call_routes
from routes.alert import alert_bp
from routes.onprem import onprem_bp, init_onprem_routes


load_dotenv()

app = Flask(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting AI Agent Application")
    print("=" * 60)
    
    # 1. Create LLM factory
    print("\n[1/6] Creating LLM factory...")
    llm_factory = AbstractLLMServiceFactory()
    
    # 2. Create services
    print("[2/6] Creating services...")
    servicenow = ServiceNow()
    onprem_bridge = OnPremBridge()
    
    # 3. Create agents (thin coordinators)
    print("[3/6] Creating agents...")
    network_agent = NetworkAgent(servicenow, llm_factory)
    voice_agent = VoiceAgent(servicenow, onprem_bridge, llm_factory)
    
    # 4. Initialize routes
    print("[4/6] Initializing routes...")
    init_call_routes(voice_agent, onprem_bridge)
    init_onprem_routes(onprem_bridge)
    app.register_blueprint(call_bp)
    app.register_blueprint(onprem_bp)
    app.register_blueprint(alert_bp)
    
    # 5. Start autonomous agent
    print("[5/6] Starting autonomous agent...")
    agent_thread = threading.Thread(
        target=network_agent.servicenow_instance.start_servicenow_job,
        daemon=True
    )
    agent_thread.start()
    
    # 6. Start Flask
    print("[6/6] Starting Flask server...")
    print("=" * 60)
    print("✅ Application Ready!")
    print("   - Autonomous agent: Running")
    print("   - Voice system: Ready")
    print("   - HTTP server: http://0.0.0.0:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)