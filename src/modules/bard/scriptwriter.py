import pathlib
from google.genai import types
from src.core.client import llm_provider
from src.core.config import MODEL_GM

class Scriptwriter:
    def __init__(self):
        self.persona_path = pathlib.Path(__file__).parent / "narrator_persona.md"
        self.persona = self._load_persona()

    def _load_persona(self) -> str:
        if self.persona_path.exists():
            return self.persona_path.read_text(encoding="utf-8")
        return "You are a dramatic narrator summarizing a story."

    async def generate_script(self, history_text: str, context: str, scope: str = "session") -> str:
        """
        Generates a dramatic script based on history and campaign context.
        """
        # Separate System Identity from Task Content
        system_instruction = self.persona
        
        task_instruction = ""
        if scope == "campaign":
            task_instruction = """
            # TASK: CAMPAIGN RECAP
            Summarize the GRAND ARC of the campaign based on the 'CAMPAIGN CONTEXT' provided. 
            Focus on major milestones, the main threat, and the party's long-term journey.
            Ignore the granular details of the 'RECENT HISTORY' unless they are pivotal.
            Style: Epic, broad, mythological.
            """
        else: # session
            task_instruction = """
            # TASK: SESSION RECAP
            Summarize the IMMEDIATE EVENTS of the recent session based on 'RECENT HISTORY'.
            Focus on the specific scene, the latest combat, or the current conversation.
            Use 'CAMPAIGN CONTEXT' only for background flavor.
            Style: Immediate, tense, episodic.
            """

        user_content = f"""
        # CAMPAIGN CONTEXT (LEDGERS)
        {context}

        # RECENT HISTORY (LOGS)
        {history_text}

        {task_instruction}

        Generate the dramatic audio script now. Do not include any meta-talk or tags. 
        Start immediately with the narration.
        """

        # Pass user_content as a single-item list to 'history' (which maps to 'contents' in Gemini)
        response = await llm_provider.generate(
            model_name=MODEL_GM,
            system_instruction=system_instruction,
            history=[user_content], 
            temperature=0.8
        )
        
        return response.strip() if response else "The chronicles are silent..."
