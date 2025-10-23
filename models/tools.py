class Tools:
    
    current_tools = {"type": "realtime",
                    "model": "gpt-4o-realtime-preview-2024-10-01",
                    "instructions": "You are an AI network agent. You can check device VLANs and answer questions about ServiceNow tickets. When the user asks about tickets or complex questions, use the ask_claude function.",
                    "tools": [
                        {
                            "type": "function",
                            "name": "get_device_vlans",
                            "description": "Gets VLAN data for a network device",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device_name": {
                                        "type": "string",
                                        "description": "Name of the device like 'ground floor switch' or 'Cisco test switch'"
                                    }
                                },
                                "required": ["device_name"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "ask_servicenow",
                            "description": "Ask Claude (the AI brain) about ServiceNow tickets, complex network issues, or any questions requiring deep analysis. Use this for ticket queries like 'What is the status of ticket INC001?'",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The question to ask OpenAI, including ticket numbers if mentioned"
                                    }
                                },
                                "required": ["question"]
                            }
                        }
                    ]
                }
    def __init__(self):
        pass
    
    def get_tools(self):
        return Tools.current_tools