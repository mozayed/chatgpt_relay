"""ServiceNow ticket management tools"""

SERVICENOW_TOOLS = [
    {
        "type": "function",
        "name": "query_servicenow_ticket",
        "description": "Get information about a ServiceNow ticket by ticket number",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_number": {
                    "type": "string",
                    "description": "ServiceNow ticket number like INC001"
                }
            },
            "required": ["ticket_number"]
        }
    },
    {
        "type": "function",
        "name": "create_servicenow_ticket",
        "description": "Create a new ServiceNow incident ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "short_description": {
                    "type": "string",
                    "description": "Brief summary of the issue"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the issue"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level: 1-Critical, 2-High, 3-Moderate, 4-Low, 5-Planning",
                    "enum": ["1", "2", "3", "4", "5"]
                }
            },
            "required": ["short_description", "description"]
        }
    },
    {
        "type": "function",
        "name": "update_servicenow_ticket",
        "description": "Update an existing ServiceNow ticket with work notes or status changes",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_number": {
                    "type": "string",
                    "description": "ServiceNow ticket number like INC001"
                },
                "work_notes": {
                    "type": "string",
                    "description": "Work notes to add to the ticket"
                },
                "state": {
                    "type": "string",
                    "description": "New state: 1-New, 2-In Progress, 3-On Hold, 6-Resolved, 7-Closed",
                    "enum": ["1", "2", "3", "6", "7"]
                }
            },
            "required": ["ticket_number"]
        }
    },
    {
    "type": "function",
    "name": "list_open_tickets",
    "description": "List all open ServiceNow tickets in the network queue. Returns ticket numbers, descriptions, priorities, and current states.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
    },
    {
        "type": "function",
        "name": "close_servicenow_ticket",
        "description": "Close a ServiceNow ticket with resolution notes",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_number": {
                    "type": "string",
                    "description": "ServiceNow ticket number like INC001"
                },
                "resolution_notes": {
                    "type": "string",
                    "description": "Notes explaining how the issue was resolved"
                },
                "close_code": {
                    "type": "string",
                    "description": "Close code: Solved, Solved Remotely, Not Solved, Closed/Skipped, etc.",
                    "enum": ["Solved", "Solved Remotely", "Not Solved", "Closed/Skipped"]
                }
            },
            "required": ["ticket_number", "resolution_notes"]
        }
    }
]