from abc import ABC, abstractmethod
from openai import OpenAI
import anthropic, os

class LLMServices(ABC):
    def __init__(self):
        pass

class OpenAiService(LLMServices):
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.openai_webhook = OpenAI(webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET")) 

    async def analyze(self, content):
        """Analyze with OpenAI"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        return response.choices[0].message.content
    
    
    async def ask(self, content):
        """Ask OpenAI a question"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        return response.choices[0].message.content

class ClaudeService(LLMServices):
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def analyze(self, content):
        """Analyze with Claude"""
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        return message.content[0].text
    
    async def ask(self, content):
        """Ask Claude a question"""
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        return message.content[0].text
        
