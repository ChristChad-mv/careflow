from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from src.utils.config import OPENAI_API_KEY, GEMINI_API_KEY
from typing import Optional, TypedDict, Any, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelConfig(TypedDict, total=False):
    """Configuration options for language models."""
    model: str
    temperature: float
    streaming: bool


def get_model(model_config: Optional[ModelConfig] = None) -> BaseChatModel:
    """
    Get a language model instance with optional configuration overrides.

    Args:
        model_config: Optional configuration parameters for the model

    Returns:
        A configured language model instance

    Raises:
        ValueError: If no API keys are configured
    """
    # Default configuration
    config: Dict[str, Any] = {
        'model': None,
        'temperature': 0.7,
        'streaming': False
    }

    # Merge with provided config
    if model_config:
        config.update(model_config)

    # Extract model name
    model_name = config.pop('model')

    if GEMINI_API_KEY:
        logger.info('Using Gemini')
        return ChatGoogleGenerativeAI(
            model=model_name or 'gemini-2.5-pro',
            api_key=GEMINI_API_KEY,
            temperature=config.get('temperature', 0.7),
            streaming=config.get('streaming', False)
        )

    if OPENAI_API_KEY:
        logger.info('Using OpenAI')
        return ChatOpenAI(
            model=model_name or 'gpt-4o',
            api_key=OPENAI_API_KEY,
            temperature=config.get('temperature', 0.7),
            streaming=config.get('streaming', False)
        )

    raise ValueError("No API keys configured")


# Export the type for use in other modules
__all__ = ['get_model', 'ModelConfig', 'BaseChatModel']
