import uuid
import asyncio
from datetime import datetime

class OnPremBridge:
    """Handles communication with on-prem Flask API via polling"""
    
    def __init__(self):
        self.pending_requests = []
        self.responses = {}
    
    def get_pending_request(self):
        """Get next pending request (called by /poll route)"""
        if self.pending_requests:
            return self.pending_requests.pop(0)
        return None
    
    def submit_response(self, request_id, result):
        """Store response from on-prem (called by /submit_response route)"""
        self.responses[request_id] = result
        print(f"Stored response for {request_id}", flush=True)
    
    async def execute_tool(self, tool_name, parameters):
        """Execute on-prem tool and wait for response"""
        req_id = str(uuid.uuid4())
        
        request = {
            "id": req_id,
            "tool": tool_name,
            "params": parameters,
            "timestamp": datetime.now().isoformat()
        }
        
        self.pending_requests.append(request)
        print(f"Queued on-prem request {req_id}", flush=True)
        
        # Wait for response with timeout
        timeout = 10
        start = asyncio.get_event_loop().time()
        
        while req_id not in self.responses:
            if asyncio.get_event_loop().time() - start > timeout:
                return {"error": "Request timed out"}
            await asyncio.sleep(0.5)
        
        result = self.responses.pop(req_id)
        return result