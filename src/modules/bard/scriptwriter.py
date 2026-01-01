import pathlib
from google.genai import types
from src.core.llm import llm_provider
from src.core.config import MODEL_GM

class Scriptwriter:
    def __init__(self):
        self.persona_path = pathlib.Path(__file__).parent / "narrator_persona.md"
        self.persona = self._load_persona()

    def _load_persona(self) -> str:
        if self.persona_path.exists():
            return self.persona_path.read_text(encoding="utf-8")
        return "You are a dramatic narrator summarizing a story."

    async def generate_script(self, history_text: str, context: str) -> str:
        """
        Generates a dramatic script based on history and campaign context.
        """
        prompt = f"""
        # SYSTEM INSTRUCTIONS
        {self.persona}

        # CAMPAIGN CONTEXT (LEDGERS)
        {context}

        # RECENT HISTORY (LOGS)
        {history_text}

        # TASK
        Generate the dramatic audio script now. Do not include any meta-talk or tags. 
        Start immediately with the narration.
        """

        response = await llm_provider.generate(
            model_name=MODEL_GM,
            system_instruction=prompt,
            history=[], # We pass history as text for better summarization control
            temperature=0.8
        )
        
        return response.strip() if response else "The chronicles are silent..."
