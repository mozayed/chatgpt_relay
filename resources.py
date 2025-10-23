from models.voice_agent import VoiceAgent
from models.llm_factory import AbstractLLMServiceFactory
from models.servicenow import ServiceNow
from models.agent import NetworkAgent

# create one instance of the abstract factory llm service class
llm_factoy_object = AbstractLLMServiceFactory()
# create one instance for servicenow in the app
servicenow_instance = ServiceNow()
# creae one instance of the Network Agent in the app
network_agent = NetworkAgent(servicenow_instance, llm_factoy_object)
# create one instance of the voice agent in the app
voice_agent = VoiceAgent(servicenow_instance, llm_factoy_object)