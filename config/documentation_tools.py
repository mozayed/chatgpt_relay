"""Documentation search tools"""

DOCUMENTATION_TOOLS = [
    {
        "type": "function",
        "name": "search_documentation",
        "description": "Search company network documentation, procedures, and troubleshooting guides",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (e.g., 'VLAN configuration steps', 'port troubleshooting procedure', 'WiFi setup guide')"
                }
            },
            "required": ["query"]
        }
    }
]