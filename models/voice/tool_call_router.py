class ToolCallRouter:
    """Routes tool calls to appropriate service"""
    
    def __init__(self, servicenow, onprem_bridge, llm_choice):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.llm_choice = llm_choice
    
    async def route(self, function_name, arguments):
        """Route tool call to correct service"""
        print(f"Routing: {function_name}", flush=True)
        
        if function_name == 'query_servicenow_ticket':
            ticket_number = arguments.get('ticket_number')
            return await self.servicenow.get_ticket_data(ticket_number)
        
        elif function_name == 'get_device_vlans':
            return await self.onprem_bridge.execute_tool(function_name, arguments)
        
        else:
            return {"error": f"Unknown tool: {function_name}"}