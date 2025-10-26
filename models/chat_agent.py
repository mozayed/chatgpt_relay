"""Chat Agent - interactive text chat with Claude"""
import anthropic
import os
import json
from models.chat_tool_router import ChatToolRouter

class ChatAgent:
    """Chat interface using Claude for network operations"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.rag_service = rag_service
        
        # Create router
        self.router = ChatToolRouter(servicenow, onprem_bridge, rag_service)
        
        # Claude client
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # System prompt
        self.system_prompt = """You are an AI Network Operations Assistant helping network engineers.

                                You can:
                                - Query, create, update, and close ServiceNow tickets
                                - List open tickets and generate reports
                                - Check network device status (VLANs, interfaces, CDP neighbors, spanning tree)
                                - Search company documentation and troubleshooting procedures
                                - Answer questions about network operations

                                Be helpful, technical, and concise. Use tools when needed to get real-time information."""
        
        # Tool definitions
        self.tools = self._load_tools()
    
    def _load_tools(self):
        """Load tool definitions from config files"""
        from config.servicenow_tools import SERVICENOW_TOOLS
        from config.onprem_tools import ONPREM_TOOLS
        from config.documentation_tools import DOCUMENTATION_TOOLS
        
        # Combine all tools
        all_tools = SERVICENOW_TOOLS + ONPREM_TOOLS + DOCUMENTATION_TOOLS
        
        # Convert from OpenAI format to Claude format ← THIS IS THE CONVERTER
        claude_tools = []
        for tool in all_tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["parameters"]  # OpenAI calls it "parameters", Claude calls it "input_schema"
            }
            claude_tools.append(claude_tool)
        
        return claude_tools