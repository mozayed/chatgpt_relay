import asyncio, anthropic, os
from openai import OpenAI

class NetworkAgent:
    
    def __init__(self, servicenow_instance, rag_service):
        # self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.servicenow_instance = servicenow_instance
        self.rag_service = rag_service
        self.preferred_llm = "Claude"
    
    def set_preferred_llm(self, llm):
        self.preferred_llm = llm

    def start_servicenow(self, llm):
        """Start the autonomous agent in a background thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.set_preferred_llm(llm)
        print(f"NetworkAgent starting with RAG: {self.rag_service is not None}", flush=True)
        loop.run_until_complete(self.servicenow_instance.start_servicenow_job(self.preferred_llm, rag_service= self.rag_service))

    def access_tool(self):
        pass
    def do_job(self):
        pass
    def chat(self):
        pass
    