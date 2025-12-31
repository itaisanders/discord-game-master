import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

def test_imports_of_all_modules():
    """
    This test imports all major python files in the project to ensure
    syntax validity and importability.
    """
    try:
        import src.main
        import src.core.config
        import src.core.client
        import src.core.views
        import src.modules.dice.rolling
        import src.modules.presence.manager
        import src.modules.memory.service
        import src.modules.narrative.parser
        
        # Scripts
        import scripts.analyze_art_style
        import scripts.check_env
        import scripts.ingest_rpg_book
        
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in module: {e}")
