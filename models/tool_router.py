from models.tool_handler import AbstractToolHandler, ServiceNowHandler, OnPremToolHandler, DocumentationHandler

class ToolRouter:
    """Routes tool calls from ChatAgent to appropriate service handlers"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.rag_service = rag_service
        registry = AbstractToolHandler._handlers_registry
        self.handlers = {}
        # Map services to handlers
        service_map = {
            'servicenow': servicenow,
            'device': onprem_bridge,
            'search': rag_service
        }
        # Create handler instances from registry
        for pattern, handler_class in registry.items():
            service = service_map.get(pattern)
            if service:
                self.handlers[pattern] = handler_class(service)
        
    async def route(self, function_name, arguments):
        print(f"🔧 Routing: {function_name}", flush=True)
        
        # FIND HANDLER BY PATTERN!
        for pattern, handler in self.handlers.items():
            if pattern in function_name or function_name.startswith(pattern):
                return await handler.handle(function_name, arguments)
        
        # No handler found
        return {"error": f"No handler found for: {function_name}"}
        # self.servicenow_handler = ServiceNowHandler(self.servicenow)
        # self.documentation_handler = DocumentationHandler(self.rag_service)
        # self.onprembridge_handler = OnPremToolHandler(self.onprem_bridge)
    

    # async def route(self, function_name, arguments):
    #     """Route tool call to correct handler"""
    #     print(f"🔧 Chat routing: {function_name}", flush=True)
        
        
    #     if 'servicenow' in function_name:
    #         result= await self.servicenow_handler.handle(function_name, arguments)
    #         print(f"✅ Router returning: {result}", flush=True)
    #         return result
        
    #     elif 'search' in function_name:
    #         return await self.documentation_handler.handle(function_name, arguments)
        
    #     elif function_name in ['get_device_vlans', 'get_device_cdp', 'get_device_ntp', 'get_device_spanning_tree']:
    #         return await self.onprembridge_handler.handle(function_name, arguments)
        
        