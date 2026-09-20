from .base import VLMProvider
from typing import List, Dict

class DeepSeekProvider(VLMProvider):
    def default_base_url(self) -> str:
        return 'https://api.deepseek.com/v1'
    
    def provider_id(self) -> str:
        return 'deepseek'
    
    def display_name(self) -> str:
        return 'DeepSeek'
    
    def supported_models(self) -> List[Dict[str, str]]:
        return [
            {'id': 'deepseek-vl2', 'name': 'DeepSeek-VL2', 'params': 'Unknown'},
        ]
