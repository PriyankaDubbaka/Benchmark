from .base import VLMProvider
from typing import List, Dict

class TogetherAIProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://api.together.xyz/v1'
    
    def provider_id(self) -> str:
        return 'together_ai'
    
    def display_name(self) -> str:
        return 'Together AI'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'Qwen/Qwen2.5-VL-72B-Instruct', 'name': 'Qwen2.5-VL 72B', 'params': '72B'},
            {'id': 'Qwen/Qwen2.5-VL-7B-Instruct', 'name': 'Qwen2.5-VL 7B', 'params': '7B'},
            {'id': 'meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo', 'name': 'Llama 3.2 Vision 90B', 'params': '90B'},
            {'id': 'meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo', 'name': 'Llama 3.2 Vision 11B', 'params': '11B'},
        ]
