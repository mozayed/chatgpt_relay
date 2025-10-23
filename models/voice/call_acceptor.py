import os
import requests

class CallAcceptor:
    """Accepts incoming calls and configures ChatGPT with tools"""
    
    def accept(self, call_id):
        """Accept call with OpenAI Realtime API"""
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
                            - After calling query_servicenow_ticket, immediately tell the user what you found
                            - Be conversational and helpful

                            Example flow:
                            User: "What's ticket INC001 about?"
                            You: "Let me check that for you..." [calls tool] [receives data] "Ticket INC001 is about network connectivity issues. It was created on..."

                            Never stop talking after getting function results - always narrate what you found.""",
                    "tools": [
                        {
                            "type": "function",
                            "name": "query_servicenow_ticket",
                            "description": "Get ServiceNow ticket information by ticket number",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "ticket_number": {
                                        "type": "string",
                                        "description": "Ticket number like INC001"
                                    }
                                },
                                "required": ["ticket_number"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "get_device_vlans",
                            "description": "Get VLAN information from network device",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device_name": {
                                        "type": "string",
                                        "description": "Name of the device"
                                    }
                                },
                                "required": ["device_name"]
                            }
                        }
                    ]
                }
            )
            
            success = response.status_code == 200
            print(f"{'✓' if success else '❌'} Call accept: {response.status_code}", flush=True)
            return success
            
        except Exception as e:
            print(f"❌ Failed to accept call: {e}", flush=True)
            return False