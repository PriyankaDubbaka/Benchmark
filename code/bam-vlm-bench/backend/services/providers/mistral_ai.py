from .base import VLMProvider
from typing import List, Dict

class MistralAIProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://api.mistral.ai/v1'
    
    def provider_id(self) -> str:
        return 'mistral_ai'
    
    def display_name(self) -> str:
        return 'Mistral AI'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'pixtral-large-latest', 'name': 'Pixtral Large 124B', 'params': '124B'},
            {'id': 'pixtral-12b-2409', 'name': 'Pixtral 12B', 'params': '12B'},
        ]
