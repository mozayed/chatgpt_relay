import os
from twilio.rest import Client

class TwilioClient:
    """Twilio operations wrapper"""
    
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    def make_call(self, to_number, twiml_url):
        """Make outbound call"""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=twiml_url
            )
            return call
        except Exception as e:
            print(f"Failed to make call: {e}", flush=True)
            return None