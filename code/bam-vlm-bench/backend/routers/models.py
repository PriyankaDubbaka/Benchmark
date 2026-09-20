from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from .api_keys import _configured_keys, normalize_provider_id

router = APIRouter()

class VLMModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    provider_id: str
    parameters: str
    capabilities: List[str]
    isAvailable: bool
    is_available: bool
    license: str
    document_strength: str
    api_format: str = "openai_compatible"

# Strictly OPEN-SOURCE models with VISION-LANGUAGE (VLM) capabilities
VLM_CATALOG = [
    {
        "id": "qwen-2.5-vl-72b",
        "model_id": "Qwen/Qwen2.5-VL-72B-Instruct",
        "name": "Qwen2.5-VL 72B Instruct",
        "provider": "Together AI",
        "provider_id": "together",
        "parameters": "72B",
        "capabilities": ["High-Res Vision", "Table Extraction", "Dense OCR", "Multi-Page PDF"],
        "license": "Qwen License (Open Weights)",
        "document_strength": "Exceptional (#1 rank for complex table and scientific certificate parsing)",
    },
    {
        "id": "qwen-2.5-vl-7b",
        "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "name": "Qwen2.5-VL 7B Instruct",
        "provider": "Together AI",
        "provider_id": "together",
        "parameters": "7B",
        "capabilities": ["Vision", "Table Extraction", "Fast Inference"],
        "license": "Apache 2.0 (Fully Open)",
        "document_strength": "Very Strong (Cost-effective, rapid certificate reading)",
    },
    {
        "id": "qwen-2.5-vl-72b-fw",
        "model_id": "accounts/fireworks/models/qwen2p5-vl-72b-instruct",
        "name": "Qwen2.5-VL 72B (Fireworks)",
        "provider": "Fireworks AI",
        "provider_id": "fireworks",
        "parameters": "72B",
        "capabilities": ["High-Res Vision", "Table Extraction", "Compound OCR"],
        "license": "Qwen License (Open Weights)",
        "document_strength": "Exceptional",
    },
    {
        "id": "pixtral-12b",
        "model_id": "pixtral-12b-2409",
        "name": "Pixtral 12B",
        "provider": "Mistral AI",
        "provider_id": "mistral",
        "parameters": "12B",
        "capabilities": ["Arbitrary Aspect Ratio", "Multi-Image", "Scientific Diagrams"],
        "license": "Apache 2.0 (Fully Open)",
        "document_strength": "Excellent (Native aspect-ratio preserves certificate layout)",
    },
    {
        "id": "pixtral-large-124b",
        "model_id": "pixtral-large-latest",
        "name": "Pixtral Large 124B",
        "provider": "Mistral AI",
        "provider_id": "mistral",
        "parameters": "124B",
        "capabilities": ["Frontier Vision", "Deep Reasoning", "Multi-Page PDF"],
        "license": "Mistral Research License / Open Weights",
        "document_strength": "State-of-the-Art reasoning on multi-page technical reports",
    },
    {
        "id": "llama-3.2-90b-vision",
        "model_id": "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
        "name": "Llama 3.2 Vision 90B",
        "provider": "Together AI",
        "provider_id": "together",
        "parameters": "90B",
        "capabilities": ["Document QA", "Image Reasoning", "Vision-Language"],
        "license": "Llama 3.2 Community License",
        "document_strength": "Strong general document VQA",
    },
    {
        "id": "llama-3.2-11b-vision",
        "model_id": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "name": "Llama 3.2 Vision 11B",
        "provider": "Together AI",
        "provider_id": "together",
        "parameters": "11B",
        "capabilities": ["Lightweight Vision", "Fast OCR"],
        "license": "Llama 3.2 Community License",
        "document_strength": "Good for straightforward text/summary tables",
    },
    {
        "id": "llama-3.2-90b-groq",
        "model_id": "llama-3.2-90b-vision-preview",
        "name": "Llama 3.2 Vision 90B (Groq LPU)",
        "provider": "Groq",
        "provider_id": "groq",
        "parameters": "90B",
        "capabilities": ["Ultra-Fast LPU", "Document Vision"],
        "license": "Llama 3.2 Community License",
        "document_strength": "Fast inference for real-time document search",
    },
    {
        "id": "internvl3-78b",
        "model_id": "opengvlab/internvl3-78b",
        "name": "InternVL3 78B",
        "provider": "OpenRouter",
        "provider_id": "openrouter",
        "parameters": "78B",
        "capabilities": ["Dynamic High-Res Tiling", "ChartQA", "Dense Table Parsing"],
        "license": "Apache 2.0 (Open Weights)",
        "document_strength": "Exceptional DocVQA benchmark scores",
    },
    {
        "id": "phi-4-multimodal",
        "model_id": "accounts/fireworks/models/phi-4-multimodal-instruct",
        "name": "Phi-4 Multimodal 5.6B",
        "provider": "Fireworks AI",
        "provider_id": "fireworks",
        "parameters": "5.6B",
        "capabilities": ["Small Form Factor", "High Density OCR", "MIT License"],
        "license": "MIT (Fully Open)",
        "document_strength": "Strong efficiency-to-accuracy ratio",
    },
    {
        "id": "deepseek-vl2",
        "model_id": "deepseek-vl2",
        "name": "DeepSeek-VL2",
        "provider": "DeepSeek",
        "provider_id": "deepseek",
        "parameters": "27.5B MoE",
        "capabilities": ["Dynamic Vision Tiles", "MoE Architecture", "High-Res OCR"],
        "license": "MIT (Fully Open)",
        "document_strength": "Strong at tabular and technical figures",
    },
    {
        "id": "idefics3-8b",
        "model_id": "HuggingFaceM4/Idefics3-8B-Llama",
        "name": "Idefics3 8B",
        "provider": "HuggingFace",
        "provider_id": "huggingface",
        "parameters": "8B",
        "capabilities": ["Docmatix Pretrained", "Document QA", "Column Understanding"],
        "license": "Apache 2.0 / Llama Community",
        "document_strength": "Pretrained on 2.4M document-visual pairs",
    },
    {
        "id": "florence-2-large",
        "model_id": "microsoft/Florence-2-large",
        "name": "Florence-2 Large",
        "provider": "HuggingFace",
        "provider_id": "huggingface",
        "parameters": "0.77B",
        "capabilities": ["Spatial Grounding", "Bounding Boxes", "Fast Layout Extraction"],
        "license": "MIT (Fully Open)",
        "document_strength": "Fast region localization and cell boundary detection",
    },
    {
        "id": "got-ocr2",
        "model_id": "stepfun-ai/GOT-OCR2_0",
        "name": "GOT-OCR2.0",
        "provider": "HuggingFace",
        "provider_id": "huggingface",
        "parameters": "0.58B",
        "capabilities": ["OCR-to-Markdown", "Formula-to-LaTeX", "Table Structure"],
        "license": "Apache 2.0 (Fully Open)",
        "document_strength": "Converts document tables to pure Markdown and LaTeX",
    },
    {
        "id": "custom-gpu-vlm",
        "model_id": "default-vlm",
        "name": "BAM GPU Cluster VLM (vLLM)",
        "provider": "Department GPU",
        "provider_id": "custom_gpu",
        "parameters": "Configurable",
        "capabilities": ["Zero-Leakage On-Premise", "High VRAM", "Custom Weights"],
        "license": "Open Source Internal",
        "document_strength": "Dedicated BAM GPU host with private weights",
    }
]

@router.get('/models')
def list_models(available: Optional[bool] = Query(None)):
    """List open-source VLM models, optionally filtered by API key availability."""
    models_out = []
    for item in VLM_CATALOG:
        pid = item['provider_id']
        is_avail = bool(_configured_keys.get(pid))
        
        # If user asked for available only
        if available and not is_avail:
            continue
            
        m = {
            "id": item["id"],
            "model_id": item["model_id"],
            "name": item["name"],
            "provider": item["provider"],
            "provider_id": pid,
            "parameters": item["parameters"],
            "capabilities": item["capabilities"],
            "isAvailable": is_avail,
            "is_available": is_avail,
            "license": item["license"],
            "document_strength": item["document_strength"],
            "api_format": "openai_compatible"
        }
        models_out.append(m)
    return models_out

@router.get('/models/available')
def list_available_models():
    """List only models whose provider API key is currently configured."""
    return list_models(available=True)
