from .base import VLMProvider
from typing import List, Dict

class OpenRouterProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://openrouter.ai/api/v1'
    
    def provider_id(self) -> str:
        return 'openrouter'
    
    def display_name(self) -> str:
        return 'OpenRouter'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'qwen/qwen-2.5-vl-72b-instruct', 'name': 'Qwen2.5-VL 72B', 'params': '72B'},
            {'id': 'qwen/qwen-2.5-vl-7b-instruct', 'name': 'Qwen2.5-VL 7B', 'params': '7B'},
            {'id': 'mistralai/pixtral-large-2411', 'name': 'Pixtral Large', 'params': '124B'},
            {'id': 'mistralai/pixtral-12b', 'name': 'Pixtral 12B', 'params': '12B'},
            {'id': 'meta-llama/llama-3.2-11b-vision-instruct', 'name': 'Llama 3.2 Vision 11B', 'params': '11B'},
            {'id': 'meta-llama/llama-3.2-90b-vision-instruct', 'name': 'Llama 3.2 Vision 90B', 'params': '90B'},
            {'id': 'opengvlab/internvl3-78b', 'name': 'InternVL3 78B', 'params': '78B'},
        ]
