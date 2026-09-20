from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class ApiKeyConfig(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None  # custom endpoint URL
    is_custom: bool = False  # True if user's department hosts this

class ApiKeyStatus(BaseModel):
    provider: str
    display_name: str
    is_configured: bool
    is_valid: Optional[bool] = None  # None = not tested yet
    base_url: str
    models_count: int
    masked_key: Optional[str] = None
    is_custom: bool = False

class ApiKeyTestResult(BaseModel):
    provider: str
    success: bool
    message: str
    response_time_ms: Optional[float] = None

class ProviderInfo(BaseModel):
    id: str
    display_name: str
    description: str
    base_url: str
    api_format: str  # 'openai_compatible' or 'custom'
    supports_custom_url: bool = True
    models: List[str]
