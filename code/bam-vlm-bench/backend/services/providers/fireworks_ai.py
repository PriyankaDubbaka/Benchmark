from .base import VLMProvider
from typing import List, Dict

class FireworksAIProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://api.fireworks.ai/inference/v1'
    
    def provider_id(self) -> str:
        return 'fireworks_ai'
    
    def display_name(self) -> str:
        return 'Fireworks AI'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'accounts/fireworks/models/qwen2p5-vl-72b-instruct', 'name': 'Qwen2.5-VL 72B', 'params': '72B'},
            {'id': 'accounts/fireworks/models/qwen2p5-vl-7b-instruct', 'name': 'Qwen2.5-VL 7B', 'params': '7B'},
            {'id': 'accounts/fireworks/models/llama-v3p2-90b-vision-instruct', 'name': 'Llama 3.2 Vision 90B', 'params': '90B'},
            {'id': 'accounts/fireworks/models/llama-v3p2-11b-vision-instruct', 'name': 'Llama 3.2 Vision 11B', 'params': '11B'},
            {'id': 'accounts/fireworks/models/phi-4-multimodal-instruct', 'name': 'Phi-4 Multimodal', 'params': 'Multimodal'},
        ]
