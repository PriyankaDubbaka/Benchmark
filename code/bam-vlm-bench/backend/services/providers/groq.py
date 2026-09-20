from .base import VLMProvider
from typing import List, Dict

class GroqProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://api.groq.com/openai/v1'
    
    def provider_id(self) -> str:
        return 'groq'
    
    def display_name(self) -> str:
        return 'Groq'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'llama-3.2-90b-vision-preview', 'name': 'Llama 3.2 Vision 90B', 'params': '90B'},
            {'id': 'llama-3.2-11b-vision-preview', 'name': 'Llama 3.2 Vision 11B', 'params': '11B'},
        ]
