import json

class ResultSender:
    """Sends tool call results back to ChatGPT via WebSocket"""
    
    async def send(self, ws, call_id, result):
        """Send result back to ChatGPT"""
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result) if isinstance(result, dict) else str(result)
            }
        }
        await ws.send(json.dumps(message))
        print(f"✓ Sent result for {call_id}", flush=True)