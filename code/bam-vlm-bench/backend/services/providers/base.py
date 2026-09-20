import abc
import base64
import httpx
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

class VLMProvider(abc.ABC):
    """Abstract base class for VLM API providers."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or self.default_base_url()
        self.client = httpx.AsyncClient(timeout=120.0)
    
    @abc.abstractmethod
    def default_base_url(self) -> str: ...
    
    @abc.abstractmethod
    def provider_id(self) -> str: ...
    
    @abc.abstractmethod
    def display_name(self) -> str: ...
    
    @abc.abstractmethod
    def supported_models(self) -> List[Dict[str, str]]: ...
    
    async def test_connection(self) -> dict:
        """Test if API key is valid."""
        try:
            start = time.time()
            models = self.supported_models()
            if not models:
                return {'success': False, 'message': 'No models available'}
            # Try a simple models list call or a minimal completion
            response = await self.client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
                timeout=15.0
            )
            elapsed = (time.time() - start) * 1000
            if response.status_code == 200:
                return {'success': True, 'message': 'Connection successful', 'response_time_ms': elapsed}
            elif response.status_code == 401:
                return {'success': False, 'message': 'Invalid API key (401 Unauthorized)'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}: {response.text[:200]}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def encode_image(self, image_path: str) -> str:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    async def extract_from_page(self, model_id: str, image_path: str, prompt: str) -> dict:
        """Send a page image to VLM and get structured extraction."""
        img_b64 = self.encode_image(image_path)
        payload = self._build_payload(model_id, img_b64, prompt)
        start = time.time()
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=120.0
        )
        elapsed = (time.time() - start) * 1000
        response.raise_for_status()
        data = response.json()
        return {
            'content': data['choices'][0]['message']['content'],
            'tokens_in': data.get('usage', {}).get('prompt_tokens', 0),
            'tokens_out': data.get('usage', {}).get('completion_tokens', 0),
            'latency_ms': elapsed
        }
    
    def _build_payload(self, model_id: str, img_b64: str, prompt: str) -> dict:
        """Build OpenAI-compatible chat completion payload with image."""
        return {
            'model': model_id,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
                    ]
                }
            ],
            'max_tokens': 4096,
            'temperature': 0.0
        }
    
    async def close(self):
        await self.client.aclose()
