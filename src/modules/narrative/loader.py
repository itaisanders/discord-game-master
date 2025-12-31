
import os
import pathlib

def load_system_instruction() -> str:
    """
    Loads the GM persona and injects any markdown files from ./knowledge.
    """
    context_parts = []
    
    # 1. Load Base Persona (Relative to this file)
    current_dir = pathlib.Path(__file__).parent
    persona_path = current_dir / "gm_persona.md"
    
    if persona_path.exists():
        context_parts.append(persona_path.read_text(encoding="utf-8").strip())
    else:
        context_parts.append("You are an amazing Game Master.")
        print(f"⚠️ {persona_path} not found, using default instruction.")

    # 2. Inject Knowledge Files (.md) - Assumes running from Project Root
    # We could also look for knowledge dir relative to project root if we wanted to be safer
    knowledge_dir = pathlib.Path("./knowledge")
    injected_files = []
    
    if knowledge_dir.exists():
        for md_file in knowledge_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                context_parts.append(f"\n\n--- FILE: {md_file.name} ---\n\n{content}")
                injected_files.append(md_file.name)
            except Exception as e:
                print(f"❌ Failed to load {md_file.name}: {e}")

    if injected_files:
        print(f"📚 Injected Knowledge: {', '.join(injected_files)}")
    else:
        print("ℹ️ No extra markdown knowledge found in ./knowledge")

    return "\n".join(context_parts)
