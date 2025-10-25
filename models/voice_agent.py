from models.voice.webhook_handler import WebhookHandler
from models.voice.call_acceptor import CallAcceptor
from models.voice.call_monitor import CallMonitor
from models.voice.tool_call_router import ToolCallRouter

class VoiceAgent:
    """Voice Agent - coordinates voice call system"""
    
    def __init__(self, servicenow, onprem_bridge, rag_service):
        # Store references (like NetworkAgent)
        self.servicenow_instance = servicenow
        self.rag_service = rag_service
        self.onprem_bridge = onprem_bridge
        self.preferred_llm = "OPENAI"
        
        # Create voice system components
        self._tool_router = ToolCallRouter(servicenow, onprem_bridge, self.preferred_llm)
        self._call_monitor = CallMonitor(self._tool_router)
        self._call_acceptor = CallAcceptor()
        self._webhook_handler = WebhookHandler(self._call_acceptor, self._call_monitor)
    
    def handle_webhook(self, event):
        """Handle incoming webhook (called by route)"""
        return self._webhook_handler.handle(event)
    
    def change_llm(self, llm_name):
        """Change LLM preference"""
        self.preferred_llm = llm_name
        self._tool_router.llm_choice = llm_name
        print(f"VoiceAgent LLM changed to: {llm_name}", flush=True)