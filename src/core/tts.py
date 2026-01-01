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
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        self.model_name = model_name

    async def generate_audio(self, text: str, voice_id: str) -> io.BytesIO:
        """
        Generates audio using Gemini's native narration capabilities.
        Strictly follows the provided integration pattern for high-quality audio.
        """
        try:
            print(f"🎙️ Generating NARRATION using {self.model_name} (Voice: {voice_id})", flush=True)
            
            # The prompt is enriched to trigger native affective dialogue (emotional tone)
            # We assume 'text' already contains the dramatic script from the Scriptwriter.
            prompt = f"Narrate the following scene with an evocative, atmospheric, and emotional tone: {text}"
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
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
            
            # Extract the raw PCM/WAV byte stream
            audio_bytes = None
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        audio_bytes = part.inline_data.data
                        break
            
            if audio_bytes:
                return io.BytesIO(audio_bytes)
            
            raise RuntimeError("Gemini returned a response but no 'inline_data' (audio bytes) was found.")

        except Exception as e:
            print(f"❌ Narration Error: {e}", flush=True)
            raise e
