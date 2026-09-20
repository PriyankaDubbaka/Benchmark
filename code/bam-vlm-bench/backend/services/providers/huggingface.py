from .base import VLMProvider
from typing import List, Dict

class HuggingFaceProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://router.huggingface.co/hf-inference/v1'
    
    def provider_id(self) -> str:
        return 'huggingface'
    
    def display_name(self) -> str:
        return 'HuggingFace'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'HuggingFaceM4/Idefics3-8B-Llama', 'name': 'Idefics3 8B', 'params': '8B'},
            {'id': 'microsoft/Florence-2-large', 'name': 'Florence-2 Large', 'params': 'Large'},
            {'id': 'stepfun-ai/GOT-OCR2_0', 'name': 'GOT-OCR2.0', 'params': 'Unknown'},
        ]
