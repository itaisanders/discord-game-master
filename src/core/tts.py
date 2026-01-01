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
    
    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_audio(self, text: str, voice_id: str) -> io.BytesIO:
        """
        Generates audio using Gemini. 
        In Gemini 2.0, audio is requested via response_modalities.
        """
        try:
            print(f"🎙️ Requesting Audio from {self.model_name} with voice: {voice_id}", flush=True)
            # Wrap the script in a clear instruction
            prompt = f"Please read the following story aloud using a dramatic voice:\n\n{text}"
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[prompt],
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
        except Exception as e:
            print(f"⚠️ First attempt with voice '{voice_id}' failed: {e}")
            print("🔄 Attempting fallback to default voice...")
            try:
                # Fallback: Try without speech_config (default voice)
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=[text],
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"]
                    )
                )
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                raise e # Raise original error if both fail

        # Extract audio bytes from the response
        audio_bytes = None
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    audio_bytes = part.inline_data.data
                    break
        
        if audio_bytes:
            return io.BytesIO(audio_bytes)
        
        print(f"⚠️ No audio data found. Full Response Candidates: {response.candidates}")
        raise RuntimeError("Gemini returned a response but no audio data found.")
