from .together_ai import TogetherAIProvider
from .fireworks_ai import FireworksAIProvider
from .mistral_ai import MistralAIProvider
from .groq import GroqProvider
from .deepseek import DeepSeekProvider
from .huggingface import HuggingFaceProvider
from .openrouter import OpenRouterProvider

PROVIDER_CLASSES = {
    'together_ai': TogetherAIProvider,
    'fireworks_ai': FireworksAIProvider,
    'mistral_ai': MistralAIProvider,
    'groq': GroqProvider,
    'deepseek': DeepSeekProvider,
    'huggingface': HuggingFaceProvider,
    'openrouter': OpenRouterProvider,
}
