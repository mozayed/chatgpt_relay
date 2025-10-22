from abc import ABC, abstractmethod
from models.llm_services import OpenAiService, ClaudeService

class AbstractLLMServiceFactory(ABC):

    _factories_registry = dict()

    def __init_subclass__(cls, /, llm: str):
        AbstractLLMServiceFactory._factories_registry[llm] = cls
    
    @abstractmethod
    def create_llm_service(self, llm):
        pass

    @classmethod
    def get_llm_instance(cls, llm: str):
        llm = llm
        concrete_class = cls._factories_registry.get(llm)
        if concrete_class:
            factory_instance = concrete_class()
            return factory_instance.create_llm_service(llm)
        return None
    
class OPENAIFactory(AbstractLLMServiceFactory, llm = 'OPENAI'):

    def create_llm_service(self, llm):
        return OpenAiService()
    
class ClaudeFactory(AbstractLLMServiceFactory, llm= "Claude"):
    
    def create_llm_service(self, llm):
        return ClaudeService()

