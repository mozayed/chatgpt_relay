import os
from openai import OpenAI
from twilio.rest import Client

class VoiceAgent():
    def __init__(self):
        self.openai_client = OpenAI(webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET"))
        self.twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self.Twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        

    def get_call(self):
        pass
    def get_alerts(Self):
        pass