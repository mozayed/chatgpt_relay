from models.tool_handler import AbstractToolHandler, ServiceNowHandler, OnPremToolHandler, DocumentationHandler
from config.servicenow_tools import SERVICENOW_TOOLS
from config.onprem_tools import ONPREM_TOOLS
from config.documentation_tools import DOCUMENTATION_TOOLS
class ToolRouter:
    """Routes tool calls from ChatAgent to appropriate service handlers"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.rag_service = rag_service
        self.servicenow_handler = ServiceNowHandler(self.servicenow)
        self.documentation_handler = DocumentationHandler(self.rag_service)
        self.onprembridge_handler = OnPremToolHandler(self.onprem_bridge)
        # BUILD TOOL -> HANDLER MAPPING FROM CONFIGS!
        self.tool_map = {}
        # Map ServiceNow tools
        for tool in SERVICENOW_TOOLS:
            self.tool_map[tool['name']] = self.servicenow_handler
        
        # Map OnPrem tools
        for tool in ONPREM_TOOLS:
            self.tool_map[tool['name']] = self.onprembridge_handler
        
        # Map Documentation tools
        for tool in DOCUMENTATION_TOOLS:
            self.tool_map[tool['name']] = self.documentation_handler
       

    async def route(self, function_name, arguments):
        print(f"🔧 Routing: {function_name}", flush=True)
        
        # LOOKUP HANDLER FROM MAP!
        handler = self.tool_map.get(function_name)
        
        if handler:
            result = await handler.handle(function_name, arguments)
            print(f"✅ Returning: {result}", flush=True)
            return result
        
        return {"error": f"No handler found for: {function_name}"}
        
    

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
        
        