"""Chat Tool Router - routes chat tool calls to appropriate services"""

class ChatToolRouter:
    """Routes tool calls from ChatAgent to appropriate services"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.rag_service = rag_service
    
    async def route(self, function_name, arguments):
        """Route tool call to correct service"""
        print(f"🔧 Chat routing: {function_name}", flush=True)
        
        # ServiceNow tools
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
        
        elif function_name == 'list_open_tickets':
            return await self.servicenow.list_open_tickets()
        
        # Documentation search
        elif function_name == 'search_documentation':
            query = arguments.get('query')
            return self._search_documentation(query)
        
        # OnPrem network device tools
        elif function_name in ['get_device_vlans', 'get_device_cdp', 'get_device_ntp', 'get_device_spanning_tree']:
            return await self.onprem_bridge.execute_tool(function_name, arguments)
        
        else:
            return {"error": f"Unknown tool: {function_name}"}
    
    def _search_documentation(self, query):
        """Search documentation via RAG"""
        try:
            print(f"📚 Searching docs: {query}", flush=True)
            docs = self.rag_service.search(query, top_k=3)
            
            if not docs:
                return {"success": True, "message": "No relevant documentation found"}
            
            result = {"success": True, "results": []}
            for doc in docs:
                result["results"].append({
                    "source": doc['source'],
                    "content": doc['text'],
                    "score": doc['score']
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Doc search error: {e}", flush=True)
            return {"success": False, "error": str(e)}