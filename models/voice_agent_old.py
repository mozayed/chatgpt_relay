import os, anthropic
from openai import OpenAI
from twilio.rest import Client

class VoiceAgent():
    def __init__(self, servicenow_instance, llm_factory ):
        self.openai_client = OpenAI(webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET"))
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self.Twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.default_llm = "OPENAI"
        self.servicenow_instance = servicenow_instance
        self.llm_factory = llm_factory
        

    def get_call(self):
        pass
    def get_alerts(Self):
        pass