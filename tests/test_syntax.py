import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

def test_syntax_of_all_files():
    """
    This test imports all major python files in the project and runs a
    simple function from each. This ensures that no file has a syntax error
    that would prevent it from being imported, which can sometimes be missed
    by linters or other checks.
    """
    from away import _syntax_check as away_check
    from bot import _syntax_check as bot_check
    from dice import _syntax_check as dice_check
    from scripts.analyze_art_style import _syntax_check as analyze_art_style_check
    from scripts.check_env import _syntax_check as check_env_check
    from scripts.ingest_rpg_book import _syntax_check as ingest_rpg_book_check

    assert away_check() is True
    assert bot_check() is True
    assert dice_check() is True
    assert analyze_art_style_check() is True
    assert check_env_check() is True
    assert ingest_rpg_book_check() is True
