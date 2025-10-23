import threading
import asyncio

class WebhookHandler:
    """Handles incoming webhooks from OpenAI"""
    
    def __init__(self, call_acceptor, call_monitor):
        self.call_acceptor = call_acceptor
        self.call_monitor = call_monitor
    
    def handle(self, event):
        """Handle incoming webhook event"""
        if event.type == 'realtime.call.incoming':
            call_id = event.data.call_id
            print(f"📞 Incoming call: {call_id}", flush=True)
            
            # Accept call
            if self.call_acceptor.accept(call_id):
                # Start monitoring in background thread
                threading.Thread(
                    target=lambda: asyncio.run(self.call_monitor.monitor(call_id)),
                    daemon=True
                ).start()
            
            return True
        
        return False