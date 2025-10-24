import os
import requests
from config.servicenow_tools import SERVICENOW_TOOLS
from config.onprem_tools import ONPREM_TOOLS

class CallAcceptor:
    """Accepts incoming calls and configures ChatGPT with tools"""
    
    def accept(self, call_id):
        """Accept call with OpenAI Realtime API"""
        all_tools = SERVICENOW_TOOLS + ONPREM_TOOLS

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
                    "instructions": """You are an AI network agent for ServiceNow tickets and network devices.
                    CRITICAL BEHAVIOR:
                    - When you call a function, ALWAYS speak the results immediately
                    - Never say "I'm checking..." and then stay silent
                    - After calling any tool, immediately tell the user what you found
                    - Be conversational and helpful

                    You can:
                    - Query, create, update, and close ServiceNow tickets
                    - Check network device information (VLANs, CDP, interfaces, spanning tree)""",
                    "tools": all_tools
                }
            )
            
            success = response.status_code == 200
            print(f"{'✓' if success else '❌'} Call accept: {response.status_code}", flush=True)
            return success
            
        except Exception as e:
            print(f"❌ Failed to accept call: {e}", flush=True)
            return False