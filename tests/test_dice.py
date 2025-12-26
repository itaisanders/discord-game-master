"""
Test suite for dice.py module

Tests dice notation parsing, validation, randomness, and error handling.
"""

import pytest
import re
from dice import roll, DiceResult


class TestBasicNotation:
    """Test basic dice notation parsing."""
    
    def test_single_d20(self):
        """Test rolling a single d20."""
        result = roll("1d20")
        assert result.error is None
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 20
        assert result.total == result.rolls[0]
        assert result.modifier == 0
    
    def test_multiple_d6(self):
        """Test rolling multiple d6."""
        result = roll("3d6")
        assert result.error is None
        assert len(result.rolls) == 3
        for r in result.rolls:
            assert 1 <= r <= 6
        assert result.total == sum(result.rolls)
    
    def test_implicit_single_die(self):
        """Test d20 notation (implicit 1d20)."""
        result = roll("d20")
        assert result.error is None
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 20


class TestModifiers:
    """Test dice notation with modifiers."""
    
    def test_positive_modifier(self):
        """Test 2d6+3 notation."""
        result = roll("2d6+3")
        assert result.error is None
        assert len(result.rolls) == 2
        assert result.modifier == 3
        assert result.total == sum(result.rolls) + 3
    
    def test_negative_modifier(self):
        """Test 1d20-2 notation."""
        result = roll("1d20-2")
        assert result.error is None
        assert result.modifier == -2
        assert result.total == result.rolls[0] - 2
    
    def test_large_modifier(self):
        """Test dice with large modifier."""
        result = roll("1d6+100")
        assert result.error is None
        assert result.modifier == 100
        assert result.total == result.rolls[0] + 100


class TestSpecialDice:
    """Test special dice types."""
    
    def test_percentile_d100(self):
        """Test 1d100 notation."""
        result = roll("1d100")
        assert result.error is None
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 100
    
    def test_percentile_d_percent(self):
        """Test d% notation."""
        result = roll("d%")
        assert result.error is None
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 100
    
    def test_fate_dice(self):
        """Test 4dF notation (FATE dice)."""
        result = roll("4dF")
        assert result.error is None
        assert len(result.rolls) == 4
        for r in result.rolls:
            assert r in [-1, 0, 1]
        assert result.total == sum(result.rolls)
    
    def test_fate_dice_with_modifier(self):
        """Test FATE dice with modifier."""
        result = roll("4dF+2")
        assert result.error is None
        assert result.modifier == 2
        assert result.total == sum(result.rolls) + 2


class TestValidation:
    """Test validation and error handling."""
    
    def test_invalid_notation(self):
        """Test completely invalid notation."""
        result = roll("not-dice")
        assert result.error is not None
        assert "Invalid dice notation" in result.error
    
    def test_negative_dice_count(self):
        """Test negative dice count."""
        result = roll("-2d6")
        assert result.error is not None
    
    def test_zero_dice_count(self):
        """Test zero dice count."""
        result = roll("0d6")
        assert result.error is not None
        assert "positive" in result.error.lower()
    
    def test_too_many_dice(self):
        """Test exceeding max dice limit (100)."""
        result = roll("101d6")
        assert result.error is not None
        assert "100" in result.error
    
    def test_dice_size_too_large(self):
        """Test exceeding max dice size (d1000)."""
        result = roll("1d1001")
        assert result.error is not None
        assert "1000" in result.error
    
    def test_zero_dice_size(self):
        """Test zero dice size."""
        result = roll("2d0")
        assert result.error is not None
        assert "positive" in result.error.lower()
    
    def test_malformed_modifier(self):
        """Test malformed modifier."""
        result = roll("2d6+abc")
        assert result.error is not None


class TestFormatting:
    """Test output formatting for Discord."""
    
    def test_single_die_formatting(self):
        """Test formatting for single die roll."""
        result = roll("1d20")
        assert result.error is None
        # Should show just the result in bold
        assert "**" in result.formatted
        assert str(result.rolls[0]) in result.formatted
    
    def test_multiple_dice_formatting(self):
        """Test formatting for multiple dice."""
        result = roll("2d6")
        assert result.error is None
        # Should show list of rolls
        assert "[" in result.formatted
        assert "]" in result.formatted
    
    def test_modifier_formatting(self):
        """Test formatting with modifier."""
        result = roll("2d6+3")
        assert result.error is None
        # Should show modifier with +/- sign
        assert "+3" in result.formatted
        assert "**" in result.formatted  # Total should be bold
    
    def test_fate_dice_formatting(self):
        """Test FATE dice formatting."""
        result = roll("4dF")
        assert result.error is None
        # Should use special FATE symbols
        assert any(symbol in result.formatted for symbol in ["[-]", "[ ]", "[+]"])


class TestRandomness:
    """Test statistical properties of randomness."""
    
    def test_d6_distribution(self):
        """Test that d6 rolls are uniformly distributed."""
        # Roll 6000 times (1000 per face)
        rolls = [roll("1d6").total for _ in range(6000)]
        
        # Count occurrences of each face
        counts = {i: rolls.count(i) for i in range(1, 7)}
        
        # Each face should appear roughly 1000 times (±200 is reasonable)
        for face, count in counts.items():
            assert 800 <= count <= 1200, f"Face {face} appeared {count} times (expected ~1000)"
    
    def test_d20_range(self):
        """Test that d20 rolls cover full range."""
        # Roll 100 times
        rolls = [roll("1d20").rolls[0] for _ in range(100)]
        
        # Should have variety (not all the same)
        assert len(set(rolls)) > 10, "d20 rolls lack variety"
        
        # All should be in valid range
        for r in rolls:
            assert 1 <= r <= 20
    
    def test_fate_dice_distribution(self):
        """Test FATE dice distribution."""
        # Roll 3000 FATE dice
        rolls = []
        for _ in range(750):  # 750 rolls of 4dF = 3000 individual dice
            result = roll("4dF")
            rolls.extend(result.rolls)
        
        # Count -1, 0, +1
        counts = {-1: rolls.count(-1), 0: rolls.count(0), 1: rolls.count(1)}
        
        # Each should appear roughly 1000 times (±200)
        for value, count in counts.items():
            assert 800 <= count <= 1200, f"FATE value {value} appeared {count} times (expected ~1000)"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_max_valid_dice(self):
        """Test maximum valid dice count (100)."""
        result = roll("100d6")
        assert result.error is None
        assert len(result.rolls) == 100
    
    def test_max_valid_size(self):
        """Test maximum valid dice size (d1000)."""
        result = roll("1d1000")
        assert result.error is None
        assert 1 <= result.rolls[0] <= 1000
    
    def test_whitespace_handling(self):
        """Test notation with extra whitespace."""
        result = roll("  2d6+3  ")
        assert result.error is None
        assert result.notation == "2d6+3"
    
    def test_case_insensitivity(self):
        """Test that notation is case-insensitive."""
        result1 = roll("4df")
        result2 = roll("4dF")
        result3 = roll("4Df")
        
        assert result1.error is None
        assert result2.error is None
        assert result3.error is None
    
    def test_empty_string(self):
        """Test empty notation string."""
        result = roll("")
        assert result.error is not None
    
    def test_single_d(self):
        """Test just 'd' without numbers."""
        result = roll("d")
        assert result.error is not None


class TestDiceResult:
    """Test DiceResult dataclass."""
    
    def test_result_structure(self):
        """Test that DiceResult has all required fields."""
        result = roll("2d6+3")
        
        assert hasattr(result, 'notation')
        assert hasattr(result, 'rolls')
        assert hasattr(result, 'modifier')
        assert hasattr(result, 'total')
        assert hasattr(result, 'formatted')
        assert hasattr(result, 'error')
    
    def test_error_result_structure(self):
        """Test that error results have proper structure."""
        result = roll("invalid")
        
        assert result.error is not None
        assert result.notation == "invalid"
        assert result.rolls == []
        assert result.total == 0


class TestRealWorldScenarios:
    """Test real-world TTRPG scenarios."""
    
    def test_dungeon_world_hack_and_slash(self):
        """Test Dungeon World Hack & Slash (2d6+STR)."""
        result = roll("2d6+2")
        assert result.error is None
        assert len(result.rolls) == 2
        assert result.modifier == 2
        # Total should be 4-14
        assert 4 <= result.total <= 14
    
    def test_dnd_attack_roll(self):
        """Test D&D attack roll (1d20+5)."""
        result = roll("1d20+5")
        assert result.error is None
        assert result.modifier == 5
        # Total should be 6-25
        assert 6 <= result.total <= 25
    
    def test_shadowrun_dice_pool(self):
        """Test Shadowrun-style dice pool (10d6)."""
        result = roll("10d6")
        assert result.error is None
        assert len(result.rolls) == 10
        # Total should be 10-60
        assert 10 <= result.total <= 60
    
    def test_fate_core_roll(self):
        """Test FATE Core roll (4dF+3)."""
        result = roll("4dF+3")
        assert result.error is None
        assert result.modifier == 3
        # Total should be -1 to 7 (4dF ranges from -4 to +4, plus modifier)
        assert -1 <= result.total <= 7


class TestDicePools:
    """Test dice pool notation (NdSp)."""
    
    def test_basic_pool(self):
        """Test simple pool notation (5d6p)."""
        result = roll("5d6p")
        assert result.error is None
        assert len(result.rolls) == 5
        # Should format as list
        assert "[" in result.formatted
        assert "]" in result.formatted
        # Should NOT have total
        assert "=" not in result.formatted
        
    def test_pool_alias(self):
        """Test 'pool' alias (5d6pool)."""
        result = roll("5d6pool")
        assert result.error is None
        assert len(result.rolls) == 5
        
    def test_pool_with_modifier_rejection(self):
        """Test that pools reject modifiers."""
        result = roll("5d6p+3")
        assert result.error is not None
        assert "modifier" in result.error.lower()
