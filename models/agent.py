import asyncio, anthropic, os
from models.servicenow import ServiceNow

class NetworkAgent:
    
    def __init__(self):
        self.claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.servicenow_instance = ServiceNow(agent_instance= self)

    def start_servicenow(self):
        """Start the autonomous agent in a background thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.servicenow_instance.start_servicenow_job())

    def access_tool(self):
        pass
    def do_job(self):
        pass
    def chat(self):
        pass
    