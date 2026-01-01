from abc import ABC, abstractmethod
import io
import wave
import google.genai as genai
from google.genai import types

class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""
    
    @abstractmethod
    async def generate_audio(self, text: str, voice_id: str) -> io.BytesIO:
        """
        Generates audio from text using a specific voice.
        
        Returns:
            A BytesIO object containing the WAV audio data.
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
        Wraps raw PCM output in a standard WAV header for playback compatibility.
        """
        try:
            print(f"🎙️ Generating NARRATION using {self.model_name} (Voice: {voice_id})", flush=True)
            
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
            
            # Extract the raw PCM byte stream
            raw_pcm_bytes = None
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        raw_pcm_bytes = part.inline_data.data
                        break
            
            if raw_pcm_bytes:
                # Create a WAV container in memory
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)        # Mono
                    wav_file.setsampwidth(2)        # 16-bit
                    wav_file.setframerate(24000)    # 24kHz (Gemini Standard)
                    wav_file.writeframes(raw_pcm_bytes)
                
                # Reset buffer pointer to the beginning so it can be read
                wav_buffer.seek(0)
                return wav_buffer
            
            raise RuntimeError("Gemini returned a response but no 'inline_data' (audio bytes) was found.")

        except Exception as e:
            print(f"❌ Narration Error: {e}", flush=True)
            raise e
