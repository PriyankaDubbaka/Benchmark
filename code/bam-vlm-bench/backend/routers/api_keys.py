import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Providers catalog with VLM-specific metadata
PROVIDERS_CATALOG = [
    {
        'id': 'together',
        'aliases': ['together_ai', 'together'],
        'display_name': 'Together AI',
        'description': 'Access Qwen2.5-VL (72B/7B), Llama 3.2 Vision (90B/11B), InternVL2.5',
        'default_base_url': 'https://api.together.xyz/v1',
        'env_var': 'TOGETHER_AI_API_KEY',
        'models_count': 4,
        'color': 'bg-blue-500',
        'letter': 'T',
    },
    {
        'id': 'fireworks',
        'aliases': ['fireworks_ai', 'fireworks'],
        'display_name': 'Fireworks AI',
        'description': 'Access Qwen2.5-VL, Llama 3.2 Vision, Phi-4 Multimodal, DeepSeek-VL2',
        'default_base_url': 'https://api.fireworks.ai/inference/v1',
        'env_var': 'FIREWORKS_AI_API_KEY',
        'models_count': 5,
        'color': 'bg-orange-500',
        'letter': 'F',
    },
    {
        'id': 'mistral',
        'aliases': ['mistral_ai', 'mistral'],
        'display_name': 'Mistral AI',
        'description': 'Access Pixtral 12B and Pixtral Large 124B (Native high-resolution PDF/vision)',
        'default_base_url': 'https://api.mistral.ai/v1',
        'env_var': 'MISTRAL_AI_API_KEY',
        'models_count': 2,
        'color': 'bg-amber-500',
        'letter': 'M',
    },
    {
        'id': 'groq',
        'aliases': ['groq'],
        'display_name': 'Groq',
        'description': 'Ultra-fast LPU inference for Llama 3.2 Vision models',
        'default_base_url': 'https://api.groq.com/openai/v1',
        'env_var': 'GROQ_API_KEY',
        'models_count': 2,
        'color': 'bg-rose-500',
        'letter': 'G',
    },
    {
        'id': 'deepseek',
        'aliases': ['deepseek'],
        'display_name': 'DeepSeek',
        'description': 'Access DeepSeek-VL2 open-source vision-language model',
        'default_base_url': 'https://api.deepseek.com/v1',
        'env_var': 'DEEPSEEK_API_KEY',
        'models_count': 1,
        'color': 'bg-indigo-500',
        'letter': 'D',
    },
    {
        'id': 'huggingface',
        'aliases': ['huggingface'],
        'display_name': 'HuggingFace',
        'description': 'Access Idefics3, Florence-2 Large, GOT-OCR2.0',
        'default_base_url': 'https://router.huggingface.co/hf-inference/v1',
        'env_var': 'HUGGINGFACE_API_KEY',
        'models_count': 3,
        'color': 'bg-yellow-500',
        'letter': 'H',
    },
    {
        'id': 'openrouter',
        'aliases': ['openrouter'],
        'display_name': 'OpenRouter',
        'description': 'Unified router for Qwen2.5-VL, Pixtral, InternVL3, Llama 3.2 Vision',
        'default_base_url': 'https://openrouter.ai/api/v1',
        'env_var': 'OPENROUTER_API_KEY',
        'models_count': 7,
        'color': 'bg-violet-500',
        'letter': 'O',
    },
    {
        'id': 'custom_gpu',
        'aliases': ['custom_gpu', 'department_gpu', 'on_premise'],
        'display_name': 'Department On-Premise GPU (vLLM / TGI)',
        'description': 'Internal department-hosted GPU cluster running open-source VLMs',
        'default_base_url': 'http://localhost:8000/v1',
        'env_var': 'CUSTOM_GPU_API_KEY',
        'models_count': 3,
        'color': 'bg-emerald-500',
        'letter': 'B',
    },
]

# In-memory store initialized from environment
_configured_keys: Dict[str, str] = {}
_custom_base_urls: Dict[str, str] = {}

def _get_env_path() -> Path:
    current = Path(__file__).resolve().parent.parent.parent
    return current / '.env'

def _load_initial_keys():
    env_path = _get_env_path()
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if val:
                        os.environ[key] = val

    for provider in PROVIDERS_CATALOG:
        val = os.environ.get(provider['env_var'], '').strip()
        if val:
            _configured_keys[provider['id']] = val
        url_var = f"{provider['env_var']}_BASE_URL"
        url_val = os.environ.get(url_var, '').strip()
        if url_val:
            _custom_base_urls[provider['id']] = url_val

_load_initial_keys()

def _save_to_env():
    env_path = _get_env_path()
    lines = [
        "# BAM VLM Benchmark - API Key Configuration",
        "# Automatically saved by BAM Benchmark UI",
        ""
    ]
    for provider in PROVIDERS_CATALOG:
        pid = provider['id']
        key_val = _configured_keys.get(pid, '')
        url_val = _custom_base_urls.get(pid, '')
        lines.append(f"{provider['env_var']}={key_val}")
        if url_val:
            lines.append(f"{provider['env_var']}_BASE_URL={url_val}")
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

def mask_key(k: str) -> str:
    if not k:
        return ''
    if len(k) <= 8:
        return '••••••••'
    return f"{k[:4]}••••••••{k[-4:]}"

def normalize_provider_id(pid: str) -> str:
    pid_clean = pid.lower().strip()
    for p in PROVIDERS_CATALOG:
        if pid_clean == p['id'] or pid_clean in p['aliases']:
            return p['id']
    return pid_clean

class KeyConfigRequest(BaseModel):
    provider: str
    key: Optional[str] = None
    api_key: Optional[str] = None
    baseUrl: Optional[str] = None
    base_url: Optional[str] = None

class KeyTestRequest(BaseModel):
    provider: str
    key: Optional[str] = None
    api_key: Optional[str] = None
    baseUrl: Optional[str] = None
    base_url: Optional[str] = None

@router.get('/keys')
def list_keys():
    """List all supported VLM providers with their configuration status."""
    result = []
    for p in PROVIDERS_CATALOG:
        pid = p['id']
        has_key = bool(_configured_keys.get(pid))
        base_url = _custom_base_urls.get(pid) or p['default_base_url']
        result.append({
            'provider': pid,
            'name': p['display_name'],
            'desc': p['description'],
            'isConfigured': has_key,
            'is_configured': has_key,
            'baseUrl': base_url,
            'base_url': base_url,
            'defaultBaseUrl': p['default_base_url'],
            'models': p['models_count'],
            'letter': p['letter'],
            'color': p['color'],
            'maskedKey': mask_key(_configured_keys.get(pid, ''))
        })
    return result

@router.post('/keys')
def save_key(req: KeyConfigRequest):
    """Save or update an API key and optional custom Base URL."""
    pid = normalize_provider_id(req.provider)
    api_key_val = (req.key or req.api_key or '').strip()
    base_url_val = (req.baseUrl or req.base_url or '').strip()
    
    if api_key_val:
        _configured_keys[pid] = api_key_val
    if base_url_val:
        _custom_base_urls[pid] = base_url_val
    elif base_url_val == '' and pid in _custom_base_urls:
        # clear custom url if explicitly empty
        _custom_base_urls.pop(pid, None)

    # Sync to environment
    for p in PROVIDERS_CATALOG:
        if p['id'] == pid:
            if api_key_val:
                os.environ[p['env_var']] = api_key_val
            if base_url_val:
                os.environ[f"{p['env_var']}_BASE_URL"] = base_url_val

    _save_to_env()
    return {
        'status': 'ok',
        'provider': pid,
        'isConfigured': bool(_configured_keys.get(pid)),
        'message': f"API key for {pid} saved successfully"
    }

@router.delete('/keys/{provider}')
def delete_key(provider: str):
    """Delete an API key for a provider."""
    pid = normalize_provider_id(provider)
    _configured_keys.pop(pid, None)
    _custom_base_urls.pop(pid, None)
    
    for p in PROVIDERS_CATALOG:
        if p['id'] == pid:
            os.environ.pop(p['env_var'], None)
            os.environ.pop(f"{p['env_var']}_BASE_URL", None)
            
    _save_to_env()
    return {'status': 'ok', 'provider': pid, 'message': 'API key deleted'}

@router.post('/keys/test')
@router.post('/keys/{provider}/test')
async def test_key(req: Optional[KeyTestRequest] = None, provider: Optional[str] = None):
    """Test connection to a provider using provided or saved credentials."""
    pid_raw = (req.provider if req and req.provider else provider) or ''
    pid = normalize_provider_id(pid_raw)
    
    catalog_info = next((p for p in PROVIDERS_CATALOG if p['id'] == pid), None)
    if not catalog_info:
        raise HTTPException(status_code=404, detail=f"Provider '{pid_raw}' not recognized")
        
    api_key_val = (req.key or req.api_key if req else None) or _configured_keys.get(pid, '')
    base_url_val = (req.baseUrl or req.base_url if req else None) or _custom_base_urls.get(pid) or catalog_info['default_base_url']
    
    if not api_key_val:
        return {'success': False, 'error': 'No API key provided or configured'}
        
    start = time.time()
    try:
        headers = {
            'Authorization': f"Bearer {api_key_val}",
            'Content-Type': 'application/json'
        }
        # Many providers accept GET /models
        async with httpx.AsyncClient(timeout=10.0) as client:
            test_url = f"{base_url_val.rstrip('/')}/models"
            resp = await client.get(test_url, headers=headers)
            elapsed_ms = round((time.time() - start) * 1000, 1)
            
            if resp.status_code == 200:
                return {
                    'success': True,
                    'message': f"Connected successfully ({elapsed_ms}ms)",
                    'response_time_ms': elapsed_ms
                }
            elif resp.status_code == 401:
                return {
                    'success': False,
                    'error': '401 Unauthorized: Invalid API key',
                    'response_time_ms': elapsed_ms
                }
            elif resp.status_code == 404:
                # Some custom vLLM / OpenAI endpoints don't support GET /models but accept POST /chat/completions
                # Fall back to checking status
                return {
                    'success': True,
                    'message': f"Endpoint reachable ({elapsed_ms}ms)",
                    'response_time_ms': elapsed_ms
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {resp.status_code}: {resp.text[:120]}",
                    'response_time_ms': elapsed_ms
                }
    except Exception as e:
        elapsed_ms = round((time.time() - start) * 1000, 1)
        return {
            'success': False,
            'error': f"Connection failed: {str(e)}",
            'response_time_ms': elapsed_ms
        }
