import asyncio
import threading
from flask import Flask

from models.servicenow import ServiceNow
from models.onprem_bridge import OnPremBridge
from models.agent import NetworkAgent
from models.voice_agent import VoiceAgent
from models.alert import Alert
from models.engineer import Engineer
from models.twilio_client import TwilioClient
from models.rag_service import RAGService
from models.chat_agent import ChatAgent

from routes.call import call_bp, init_call_routes
from routes.alert import alert_bp, init_alert_routes
from routes.onprem import onprem_bp, init_onprem_routes
from routes.rag import rag_bp, init_rag_routes
from routes.chat import chat_bp, init_chat_routes




app = Flask(__name__)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting AI Agent Application")
    print("=" * 60)
    
    
    # 1. Create services
    print("[1/5] Creating services...")
    servicenow = ServiceNow()
    onprem_bridge = OnPremBridge()
    twilio_client = TwilioClient()
    alert_service = Alert()
    engineer = Engineer()
    rag_service = RAGService(auto_setup=True)
    
    # 2. Create agents (thin coordinators)
    print("[2/5] Creating agents...")
    network_agent = NetworkAgent(servicenow, rag_service)
    voice_agent = VoiceAgent(servicenow, onprem_bridge, rag_service)
    chat_agent = ChatAgent(servicenow, onprem_bridge, rag_service)
    
    # 4. Initialize routes
    print("[3/5] Initializing routes...")
    init_call_routes(voice_agent, onprem_bridge)
    init_onprem_routes(onprem_bridge)
    init_alert_routes(alert_service, engineer, twilio_client)
    init_rag_routes(rag_service)
    init_chat_routes(chat_agent)

    app.register_blueprint(call_bp)
    app.register_blueprint(onprem_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(chat_bp)
    
    # 5. Start autonomous agent
    print("[4/5] Starting autonomous agent...")
    agent_thread = threading.Thread(
        target=lambda: asyncio.run(
            network_agent.start_servicenow(
                llm=network_agent.preferred_llm  # Pass agent's LLM preference
            )
        ),
        daemon=True
    )
    agent_thread.start()
    
    # 5. Start Flask
    print("=" * 60)
    print("✅ Application Ready!")
    print(f"   - Autonomous agent: Running (using {network_agent.preferred_llm})")
    print(f"   - Voice system: Ready (using {voice_agent.preferred_llm})")
    print("   - Chat interface: Ready (using Claude)")
    print("   - HTTP server: http://0.0.0.0:5000")
    print("=" * 60)    
    app.run(host='0.0.0.0', port=5000, debug=True)