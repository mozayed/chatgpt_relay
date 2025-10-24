import json
import websockets
import os
from .result_sender import ResultSender

class CallMonitor:
    """Monitors WebSocket for tool calls during a call"""
    
    def __init__(self, tool_router):
        self.tool_router = tool_router
        self.result_sender = ResultSender()
    
    async def monitor(self, call_id):
        """Monitor call WebSocket and handle tool calls"""
        try:
            async with websockets.connect(
                f"wss://api.openai.com/v1/realtime?call_id={call_id}",
                additional_headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
                }
            ) as ws:
                print(f"📞 Monitoring call {call_id}", flush=True)
                
                async for message in ws:
                    event = json.loads(message)
                    
                    if event.get('type') == 'response.function_call_arguments.done':
                        await self._handle_tool_call(ws, event)
        
        except websockets.exceptions.ConnectionClosedError:
            print(f"📞 Call {call_id} ended", flush=True)
        except Exception as e:
            print(f"❌ Monitor error: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    async def _handle_tool_call(self, ws, event):
        """Handle single tool call"""
        try:
            function_name = event.get('name')
            call_id = event.get('call_id')
            arguments = json.loads(event.get('arguments', '{}'))
            
            print(f"🔧 Tool call: {function_name}({arguments})", flush=True)
            
            # Route to appropriate handler
            result = await self.tool_router.route(function_name, arguments)
            
            # Send result back
            await self.result_sender.send(ws, call_id, result)
            
        except Exception as e:
            error_result = {"error": str(e)}
            print(f"❌ Tool call error: {e}", flush=True)
            await self.result_sender.send(ws, call_id, error_result)