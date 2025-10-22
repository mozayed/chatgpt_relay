import threading
from flask import Flask
from models.agent import NetworkAgent
from routes.alert import alert_bp
from routes.call import call_bp
from routes.onprem import onprem_bp
from models.servicenow import ServiceNow
from models.agent import NetworkAgent

app = Flask(__name__)
app.register_blueprint(alert_bp)
app.register_blueprint(call_bp)
app.register_blueprint(onprem_bp)




# ==================== MAIN ====================

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

    servicenow_instance = ServiceNow()
    network_agent = NetworkAgent(servicenow_instance)
    
    # Start autonomous agent servicenow work in a background thread
    agent_thread = threading.Thread(target=network_agent.start_servicenow, daemon=True)
    agent_thread.start()
    print("Autonomous agent started in background", flush=True)
