"""On-prem RestinPyth Flask API network device tools"""

ONPREM_TOOLS = [
    {
        "type": "function",
        "name": "get_device_vlans",
        "description": "Get VLAN information from a network device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {
                    "type": "string",
                    "description": "Name of the network device"
                }
            },
            "required": ["device_name"]
        }
    },
    {
        "type": "function",
        "name": "get_device_cdp",
        "description": "Get CDP neighbor information from a network device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {
                    "type": "string",
                    "description": "Name of the network device"
                }
            },
            "required": ["device_name"]
        }
    },
    {
        "type": "function",
        "name": "get_device_ntp",
        "description": "Get ntp information from a network device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {
                    "type": "string",
                    "description": "Name of the network device"
                }
            },
            "required": ["device_name"]
        }
    },
    {
        "type": "function",
        "name": "get_device_spanning_tree",
        "description": "Get spanning tree information from a network device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_name": {
                    "type": "string",
                    "description": "Name of the network device"
                }
            },
            "required": ["device_name"]
        }
    }
]