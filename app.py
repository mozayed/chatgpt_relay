from flask import Flask, request, Response
from openai import OpenAI
import os
import requests

app = Flask(__name__)

# Initialize OpenAI client with webhook secret
client = OpenAI(
    webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET")
)

@app.route("/webhook", methods=['POST'])
def webhook():
    """Receive incoming call webhook from OpenAI"""
    
    # Verify webhook is from OpenAI
    try:
        event = client.webhooks.unwrap(request.data, request.headers)
    except Exception as e:
        print(f"Invalid webhook: {e}", flush=True)
        return Response("Invalid signature", status=400)
    
    if event.type == 'realtime.call.incoming':
        call_id = event.data.call_id
        print(f"Incoming call: {call_id}", flush=True)
        
        # Accept the call
        requests.post(
            f"https://api.openai.com/v1/realtime/calls/{call_id}/accept",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "type": "realtime",
                "model": "gpt-4o-realtime-preview-2024-10-01",
                "instructions": "You are a helpful assistant."
            }
        )
        
        return Response(status=200)
    
    return Response(status=200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
