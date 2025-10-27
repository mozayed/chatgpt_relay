"""Chat API routes"""
from flask import Blueprint, request, jsonify, render_template
import asyncio

chat_bp = Blueprint('chat', __name__)

# Global chat agent instance
_chat_agent = None

def init_chat_routes(chat_agent):
    """Initialize routes with chat agent instance"""
    global _chat_agent
    _chat_agent = chat_agent
    print("✓ Chat routes initialized")

@chat_bp.route("/chat", methods=['GET'])
def chat_page():
    """Serve chat interface"""
    return render_template('chat.html')

@chat_bp.route("/api/chat", methods=['POST'])
def chat():
    """Chat endpoint - send message, get response"""
    try:
        data = request.json
        message = data.get('message')
        conversation_history = data.get('conversation_history', [])
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Call chat agent (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _chat_agent.chat(message, conversation_history)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Chat error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/api/chat/health", methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ready",
        "agent": "ChatAgent",
        "llm": "Claude"
    })