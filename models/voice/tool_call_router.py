class ToolCallRouter:
    """Routes tool calls to appropriate service"""
    
    def __init__(self, servicenow, onprem_bridge, llm_choice, documentation_service):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.llm_choice = llm_choice
        self.documentation_service = documentation_service
    
    async def route(self, function_name, arguments):
        """Route tool call to correct service"""
        print(f"Routing: {function_name}", flush=True)
        
        if function_name == 'query_servicenow_ticket':
            ticket_number = arguments.get('ticket_number')
            return await self.servicenow.get_ticket_data(ticket_number)
        
        elif function_name == 'create_servicenow_ticket':
            short_desc = arguments.get('short_description')
            description = arguments.get('description')
            priority = arguments.get('priority', '3')
            return await self.servicenow.create_ticket(short_desc, description, priority)
        
        elif function_name == 'update_servicenow_ticket':
            ticket_number = arguments.get('ticket_number')
            work_notes = arguments.get('work_notes')
            state = arguments.get('state')
            return await self.servicenow.update_ticket(ticket_number, work_notes, state)
        
        elif function_name == 'close_servicenow_ticket':
            ticket_number = arguments.get('ticket_number')
            resolution_notes = arguments.get('resolution_notes')
            close_code = arguments.get('close_code', 'Solved')
            return await self.servicenow.close_ticket(ticket_number, resolution_notes, close_code)
        
        elif function_name == "search_documentation":
            query = arguments.get('query')
            return self.documentation_service.search_documentation(query)

        # On-prem network device tools
        elif function_name in ['get_device_vlans', 'get_device_cdp', 'get_device_ntp', 'get_device_spanning_tree']:
            return await self.onprem_bridge.execute_tool(function_name, arguments)
        
        else:
            return {"error": f"Unknown tool: {function_name}"}