"""Chat Agent - interactive text chat with Claude"""
import anthropic
import os
import json
from .tool_router import ToolRouter

class ChatAgent:
    """Chat interface using Claude for network operations"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service):
        self.servicenow = servicenow
        self.onprem_bridge = onprem_bridge
        self.rag_service = rag_service
        
        # Create router
        self.router = ToolRouter(servicenow, onprem_bridge, rag_service)
        
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

            IMPORTANT: Be concise and direct. When asked "how many", just give the count unless specifically asked for details. Example:
            - User: "How many open tickets?" → You: "You have 5 open tickets."
            - User: "List all open tickets" → You: "Here are the 5 open tickets: [list details]"

            Be helpful, technical, and concise. Use tools when needed to get real-time information."""
        
        # Tool definitions
        self.tools = self._load_tools()
    
    def _load_tools(self):
        """Load and convert tool definitions to Claude format"""
        from config.servicenow_tools import SERVICENOW_TOOLS
        from config.onprem_tools import ONPREM_TOOLS
        from config.documentation_tools import DOCUMENTATION_TOOLS
        
        # Combine all tools
        all_tools = SERVICENOW_TOOLS + ONPREM_TOOLS + DOCUMENTATION_TOOLS
        
        # Convert from OpenAI format to Claude format
        claude_tools = []
        for tool in all_tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["parameters"]
            }
            claude_tools.append(claude_tool)
        
        return claude_tools
    
    async def chat(self, message, conversation_history=None):
        """Process a chat message"""
        if conversation_history is None:
            conversation_history = []
        
        # Build messages
        messages = conversation_history + [{"role": "user", "content": message}]
        
        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages,
            tools=self.tools
        )
        
        # Handle response
        return await self._handle_response(response, messages)
    
    async def _handle_response(self, response, messages):
        """Handle Claude's response and tool calls"""
        # Check if tool use is needed
        if response.stop_reason == "tool_use":
            # Extract tool calls
            tool_results = []
            assistant_content = []
            
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id
                    
                    print(f"🔧 Claude calling: {tool_name}({tool_input})", flush=True)
                    
                    # Store tool use in assistant content (serializable format)
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_use_id,
                        "name": tool_name,
                        "input": tool_input
                    })
                    
                    # Execute tool
                    result = await self.router.route(tool_name, tool_input)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result)
                    })
                elif content_block.type == "text":
                    # Include any text blocks too
                    assistant_content.append({
                        "type": "text",
                        "text": content_block.text
                    })
            
            # Add assistant message with tool use (serializable format)
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Add tool results
            messages.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get final response
            final_response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
                tools=self.tools
            )
            
            # Extract text response and convert to serializable format
            text_response = ""
            final_content = []
            for block in final_response.content:
                if hasattr(block, 'text'):
                    text_response += block.text
                    final_content.append({
                        "type": "text",
                        "text": block.text
                    })
            
            # Add final assistant message
            messages.append({
                "role": "assistant",
                "content": final_content
            })
            
            return {
                "message": text_response,
                "conversation_history": messages
            }
        
        else:
            # No tool use, direct response
            text_response = ""
            serializable_content = []
            
            for block in response.content:
                if hasattr(block, 'text'):
                    text_response += block.text
                    serializable_content.append({
                        "type": "text",
                        "text": block.text
                    })
            
            messages.append({
                "role": "assistant",
                "content": serializable_content
            })
            
            return {
                "message": text_response,
                "conversation_history": messages
            }