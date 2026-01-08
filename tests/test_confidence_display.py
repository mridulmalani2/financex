"""
Tests for Confidence Display Module (Stage 2)
"""

import pytest
from utils.confidence_display import (
    get_confidence_level,
    get_confidence_color,
    get_confidence_emoji,
    get_confidence_badge,
    get_confidence_label,
    format_confidence_tooltip,
    format_confidence_table,
    get_confidence_health_score,
    ConfidenceLevel
)


class TestConfidenceColors:
    """Test confidence color mapping."""

    def test_perfect_confidence_color(self):
        """Perfect confidence (1.00) returns green."""
        color = get_confidence_color(1.00, format="name")
        assert color == "green"

    def test_high_confidence_color(self):
        """High confidence (0.95) returns green."""
        color = get_confidence_color(0.95, format="name")
        assert color == "green"

    def test_good_confidence_color(self):
        """Good confidence (0.75) returns yellow."""
        color = get_confidence_color(0.75, format="name")
        assert color == "yellow"

    def test_medium_confidence_color(self):
        """Medium confidence (0.55) returns orange."""
        color = get_confidence_color(0.55, format="name")
        assert color == "orange"

    def test_low_confidence_color(self):
        """Low confidence (0.20) returns red."""
        color = get_confidence_color(0.20, format="name")
        assert color == "red"

    def test_hex_color_format(self):
        """Hex color format works."""
        color = get_confidence_color(1.00, format="hex")
        assert color.startswith("#")
        assert len(color) == 7  # #RRGGBB


class TestConfidenceBadges:
    """Test confidence badge generation."""

    def test_badge_with_emoji_and_score(self):
        """Badge shows emoji and score."""
        badge = get_confidence_badge(0.95, show_emoji=True, show_score=True)
        assert "🟢" in badge
        assert "0.95" in badge

    def test_badge_emoji_only(self):
        """Badge can show emoji only."""
        badge = get_confidence_badge(0.95, show_emoji=True, show_score=False)
        assert "🟢" in badge
        assert "0.95" not in badge

    def test_badge_score_only(self):
        """Badge can show score only."""
        badge = get_confidence_badge(0.95, show_emoji=False, show_score=True)
        assert "🟢" not in badge
        assert "0.95" in badge


class TestConfidenceLabels:
    """Test confidence label generation."""

    def test_perfect_label(self):
        """Perfect confidence gets 'Perfect' label."""
        label = get_confidence_label(1.00)
        assert label == "Perfect"

    def test_high_label(self):
        """High confidence gets 'Excellent' label."""
        label = get_confidence_label(0.95)
        assert label == "Excellent"

    def test_good_label(self):
        """Good confidence gets 'Good' label."""
        label = get_confidence_label(0.75)
        assert label == "Good"

    def test_low_label(self):
        """Low confidence gets 'Low' label."""
        label = get_confidence_label(0.20)
        assert label == "Low"


class TestConfidenceTooltips:
    """Test tooltip generation."""

    def test_tooltip_basic(self):
        """Tooltip includes confidence score and label."""
        tooltip = format_confidence_tooltip(0.95)
        assert "0.95" in tooltip
        assert "Confidence" in tooltip.lower()

    def test_tooltip_with_method(self):
        """Tooltip includes method when provided."""
        tooltip = format_confidence_tooltip(0.95, method="Exact Label Match")
        assert "Exact Label Match" in tooltip

    def test_tooltip_with_breakdown(self):
        """Tooltip includes breakdown when provided."""
        breakdown = {
            "Source Data": 1.00,
            "Mapping": 0.95,
            "Final": 0.95
        }
        tooltip = format_confidence_tooltip(0.95, breakdown=breakdown)
        assert "Source Data" in tooltip
        assert "Mapping" in tooltip


class TestConfidenceTables:
    """Test table formatting."""

    def test_table_generation(self):
        """Table includes all metrics."""
        scores = {
            "Revenue": 0.95,
            "EBITDA": 0.90,
            "Net Income": 0.70
        }
        table = format_confidence_table(scores)
        assert "Revenue" in table
        assert "EBITDA" in table
        assert "Net Income" in table

    def test_empty_table(self):
        """Empty scores produce informative message."""
        table = format_confidence_table({})
        assert "No confidence" in table.lower()


class TestHealthScore:
    """Test health score calculation."""

    def test_perfect_health_score(self):
        """All perfect scores give 100 health."""
        scores = {"A": 1.00, "B": 1.00, "C": 1.00}
        health = get_confidence_health_score(scores)
        assert health == 100

    def test_mixed_health_score(self):
        """Mixed scores give appropriate health."""
        scores = {
            "Perfect": 1.00,
            "High": 0.95,
            "Good": 0.75,
            "Low": 0.30
        }
        health = get_confidence_health_score(scores)
        assert 0 < health < 100

    def test_empty_health_score(self):
        """Empty scores give 0 health."""
        health = get_confidence_health_score({})
        assert health == 0


def test_confidence_level_enum():
    """Test confidence level categorization."""
    assert get_confidence_level(1.00) == ConfidenceLevel.PERFECT
    assert get_confidence_level(0.95) == ConfidenceLevel.HIGH
    assert get_confidence_level(0.75) == ConfidenceLevel.GOOD
    assert get_confidence_level(0.55) == ConfidenceLevel.MEDIUM
    assert get_confidence_level(0.20) == ConfidenceLevel.LOW
