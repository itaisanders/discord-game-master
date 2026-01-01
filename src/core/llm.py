from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import os
import google.genai as genai
from google.genai import types

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, model_name: str, system_instruction: str, history: List[Any], temperature: float = 0.7) -> str:
        """
        Generates content from the LLM.
        
        Args:
            model_name: The identifier of the model to use.
            system_instruction: The system prompt.
            history: A list of message objects (format depends on provider, but we'll try to standardize).
            temperature: Creativity parameter.
            
        Returns:
            The generated text response.
        """
        pass

class GeminiProvider(LLMProvider):
    """Provider implementation for Google Gemini API."""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        
    async def generate(self, model_name: str, system_instruction: str, history: List[Any], temperature: float = 0.7) -> str:
        # Convert standard history to Gemini format if necessary, 
        # but for now we assume the app uses Gemini format internally or we adapt it here.
        # The current app uses google.genai.types.Content.
        
        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature
            )
        )
        return response.text if response.text else ""

class ProviderFactory:
    """Factory to create LLM providers based on configuration."""
    
    @staticmethod
    def get_provider(provider_name: str, **kwargs) -> LLMProvider:
        if provider_name.lower() == "gemini":
            return GeminiProvider(api_key=kwargs.get("api_key"))
        # Future: elif provider_name.lower() == "ollama": ...
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
