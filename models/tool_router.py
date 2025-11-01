from models.tool_handler import ServiceNowHandler, OnPremToolHandler, DocumentationHandler

class ToolRouter:
    """Routes tool calls from ChatAgent to appropriate service handlers"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service, llm_choice= None):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.rag_service = rag_service
        self.llm_choice = llm_choice
        self.servicenow_handler = ServiceNowHandler(self.servicenow)
        self.documentation_handler = DocumentationHandler(self.rag_service)
        self.onprembridge_handler = OnPremToolHandler(self.onprem_bridge)
    
    async def route(self, function_name, arguments):
        """Route tool call to correct handler"""
        print(f"🔧 Chat routing: {function_name}", flush=True)
        
        
        if 'servicenow' in function_name:
            return await self.servicenow_handler.handle(function_name, arguments)
        
        elif 'search' in function_name:
            return await self.documentation_handler.handle(function_name, arguments)
        
        elif function_name in ['get_device_vlans', 'get_device_cdp', 'get_device_ntp', 'get_device_spanning_tree']:
            return await self.onprembridge_handler.handle(function_name, arguments)
        
        