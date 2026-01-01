from abc import ABC, abstractmethod
import io
import google.genai as genai
from google.genai import types

class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""
    
    @abstractmethod
    async def generate_audio(self, text: str, voice_id: str) -> io.BytesIO:
        """
        Generates audio from text using a specific voice.
        
        Returns:
            A BytesIO object containing the audio data.
        """
        pass

class GeminiTTSProvider(TTSProvider):
    """
    Implementation using Gemini's native audio generation.
    Note: Requires a model that supports audio output modality.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite-preview-02-05"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_audio(self, text: str, voice_id: str) -> io.BytesIO:
        """
        Generates audio using Gemini. 
        In Gemini 2.0, audio is requested via response_modalities.
        """
        # This is a simplified conceptual implementation for Gemini 2.0 audio output.
        # We instruct the model to perform the text in a specific voice style.
        # Note: 'voice_id' in Gemini maps to their supported speech config names.
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[text],
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_id
                        )
                    )
                )
            )
        )
        
        # Extract audio bytes from the response
        audio_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                audio_bytes = part.inline_data.data
                break
        
        if audio_bytes:
            return io.BytesIO(audio_bytes)
        
        raise RuntimeError("Failed to generate audio content from Gemini.")
