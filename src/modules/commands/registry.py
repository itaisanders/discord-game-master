
import pathlib

def get_help_text() -> str:
    """Returns the help text from the help_text.md file."""
    current_dir = pathlib.Path(__file__).parent
    help_file_path = current_dir / "help_text.md"
    
    if help_file_path.exists():
        return help_file_path.read_text(encoding="utf-8")
    return "Could not find the help file."
