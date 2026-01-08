"""
Confidence Display Module
Provides visualization and formatting functions for confidence scores.

Part of Stage 2: UI Transparency & Debugging
"""

from typing import Dict, Optional, Tuple
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level categories."""
    PERFECT = "perfect"  # 1.00 - Analyst Brain
    HIGH = "high"  # 0.90-0.99 - Exact/Alias
    GOOD = "good"  # 0.70-0.89 - Keyword
    MEDIUM = "medium"  # 0.40-0.69 - Partial
    LOW = "low"  # 0.00-0.39 - Low/Unmapped


def get_confidence_level(score: float) -> ConfidenceLevel:
    """
    Categorize confidence score into level.

    Args:
        score: Confidence score (0.0 to 1.0)

    Returns:
        ConfidenceLevel enum
    """
    if score >= 1.0:
        return ConfidenceLevel.PERFECT
    elif score >= 0.90:
        return ConfidenceLevel.HIGH
    elif score >= 0.70:
        return ConfidenceLevel.GOOD
    elif score >= 0.40:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW


def get_confidence_color(score: float, format: str = "hex") -> str:
    """
    Get color for confidence score.

    Args:
        score: Confidence score (0.0 to 1.0)
        format: Color format ("hex", "rgb", "name")

    Returns:
        Color string in requested format
    """
    level = get_confidence_level(score)

    if format == "hex":
        colors = {
            ConfidenceLevel.PERFECT: "#00C851",  # Green
            ConfidenceLevel.HIGH: "#00C851",     # Green
            ConfidenceLevel.GOOD: "#FFB300",     # Yellow/Amber
            ConfidenceLevel.MEDIUM: "#FF6F00",   # Orange
            ConfidenceLevel.LOW: "#FF3547",      # Red
        }
    elif format == "rgb":
        colors = {
            ConfidenceLevel.PERFECT: "rgb(0, 200, 81)",
            ConfidenceLevel.HIGH: "rgb(0, 200, 81)",
            ConfidenceLevel.GOOD: "rgb(255, 179, 0)",
            ConfidenceLevel.MEDIUM: "rgb(255, 111, 0)",
            ConfidenceLevel.LOW: "rgb(255, 53, 71)",
        }
    elif format == "name":
        colors = {
            ConfidenceLevel.PERFECT: "green",
            ConfidenceLevel.HIGH: "green",
            ConfidenceLevel.GOOD: "yellow",
            ConfidenceLevel.MEDIUM: "orange",
            ConfidenceLevel.LOW: "red",
        }
    else:
        raise ValueError(f"Unknown format: {format}")

    return colors[level]


def get_confidence_emoji(score: float) -> str:
    """
    Get emoji indicator for confidence score.

    Args:
        score: Confidence score (0.0 to 1.0)

    Returns:
        Emoji string
    """
    level = get_confidence_level(score)

    emojis = {
        ConfidenceLevel.PERFECT: "🟢",  # Green circle
        ConfidenceLevel.HIGH: "🟢",     # Green circle
        ConfidenceLevel.GOOD: "🟡",     # Yellow circle
        ConfidenceLevel.MEDIUM: "🟠",   # Orange circle
        ConfidenceLevel.LOW: "🔴",      # Red circle
    }

    return emojis[level]


def get_confidence_badge(score: float, show_emoji: bool = True, show_score: bool = True) -> str:
    """
    Generate confidence badge HTML/Markdown.

    Args:
        score: Confidence score (0.0 to 1.0)
        show_emoji: Include emoji indicator
        show_score: Include numerical score

    Returns:
        Badge string (Markdown format)
    """
    emoji = get_confidence_emoji(score) if show_emoji else ""
    score_text = f"{score:.2f}" if show_score else ""

    if show_emoji and show_score:
        return f"{emoji} {score_text}"
    elif show_emoji:
        return emoji
    elif show_score:
        return score_text
    else:
        return ""


def get_confidence_label(score: float) -> str:
    """
    Get human-readable label for confidence score.

    Args:
        score: Confidence score (0.0 to 1.0)

    Returns:
        Label string (e.g., "Excellent", "Good", "Low")
    """
    level = get_confidence_level(score)

    labels = {
        ConfidenceLevel.PERFECT: "Perfect",
        ConfidenceLevel.HIGH: "Excellent",
        ConfidenceLevel.GOOD: "Good",
        ConfidenceLevel.MEDIUM: "Medium",
        ConfidenceLevel.LOW: "Low",
    }

    return labels[level]


def format_confidence_tooltip(
    score: float,
    breakdown: Optional[Dict[str, float]] = None,
    method: Optional[str] = None
) -> str:
    """
    Generate tooltip text for confidence score.

    Args:
        score: Confidence score (0.0 to 1.0)
        breakdown: Optional dict of confidence components
        method: Optional mapping/calculation method

    Returns:
        Tooltip text (Markdown format)
    """
    label = get_confidence_label(score)

    tooltip = f"**Confidence: {score:.2f} ({label})**\n\n"

    if method:
        tooltip += f"Method: {method}\n"

    if breakdown:
        tooltip += "\nBreakdown:\n"
        for component, value in breakdown.items():
            emoji = get_confidence_emoji(value)
            tooltip += f"  {emoji} {component}: {value:.2f}\n"

    # Add interpretation
    if score >= 0.90:
        tooltip += "\n✅ High quality - safe to use in models"
    elif score >= 0.70:
        tooltip += "\n⚠️ Good quality - review recommended"
    elif score >= 0.40:
        tooltip += "\n⚠️ Medium quality - verify accuracy"
    else:
        tooltip += "\n❌ Low quality - requires attention"

    return tooltip


def format_confidence_table(scores: Dict[str, float]) -> str:
    """
    Generate Markdown table of confidence scores.

    Args:
        scores: Dict mapping metric names to confidence scores

    Returns:
        Markdown table string
    """
    if not scores:
        return "No confidence scores available."

    table = "| Metric | Confidence | Status |\n"
    table += "|--------|-----------|--------|\n"

    for metric, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        badge = get_confidence_badge(score)
        label = get_confidence_label(score)
        table += f"| {metric} | {badge} | {label} |\n"

    return table


def get_avg_confidence_color(avg_score: float) -> Tuple[str, str]:
    """
    Get color and emoji for average confidence score.

    Args:
        avg_score: Average confidence score (0.0 to 1.0)

    Returns:
        Tuple of (emoji, color_name)
    """
    emoji = get_confidence_emoji(avg_score)

    if avg_score >= 0.90:
        return (emoji, "success")  # Streamlit success (green)
    elif avg_score >= 0.70:
        return (emoji, "warning")  # Streamlit warning (yellow)
    else:
        return (emoji, "error")  # Streamlit error (red)


def format_confidence_summary(scores: Dict[str, float]) -> str:
    """
    Generate summary statistics for confidence scores.

    Args:
        scores: Dict mapping metric names to confidence scores

    Returns:
        Summary text (Markdown format)
    """
    if not scores:
        return "No confidence scores available."

    values = list(scores.values())
    avg_score = sum(values) / len(values)
    min_score = min(values)
    max_score = max(values)

    # Count by level
    perfect = sum(1 for s in values if s >= 1.0)
    high = sum(1 for s in values if 0.90 <= s < 1.0)
    good = sum(1 for s in values if 0.70 <= s < 0.90)
    medium = sum(1 for s in values if 0.40 <= s < 0.70)
    low = sum(1 for s in values if s < 0.40)

    emoji, _ = get_avg_confidence_color(avg_score)

    summary = f"### Confidence Summary {emoji}\n\n"
    summary += f"**Average Confidence:** {avg_score:.2f} ({get_confidence_label(avg_score)})\n"
    summary += f"**Range:** {min_score:.2f} - {max_score:.2f}\n"
    summary += f"**Total Metrics:** {len(scores)}\n\n"
    summary += "**Distribution:**\n"
    summary += f"- 🟢 Perfect (1.00): {perfect}\n"
    summary += f"- 🟢 High (0.90-0.99): {high}\n"
    summary += f"- 🟡 Good (0.70-0.89): {good}\n"
    summary += f"- 🟠 Medium (0.40-0.69): {medium}\n"
    summary += f"- 🔴 Low (0.00-0.39): {low}\n"

    return summary


def get_confidence_health_score(scores: Dict[str, float]) -> int:
    """
    Calculate overall health score (0-100) based on confidence distribution.

    Args:
        scores: Dict mapping metric names to confidence scores

    Returns:
        Health score (0-100)
    """
    if not scores:
        return 0

    values = list(scores.values())

    # Weight scores by confidence level
    health = 0
    for score in values:
        if score >= 1.0:
            health += 100  # Perfect
        elif score >= 0.90:
            health += 95  # High
        elif score >= 0.70:
            health += 80  # Good
        elif score >= 0.40:
            health += 50  # Medium
        else:
            health += 20  # Low

    # Average
    return int(health / len(values))


# Backwards compatibility aliases
def confidence_color(score: float) -> str:
    """Alias for get_confidence_color() with hex format."""
    return get_confidence_color(score, format="hex")


def confidence_badge(score: float) -> str:
    """Alias for get_confidence_badge()."""
    return get_confidence_badge(score)


def confidence_tooltip(score: float, method: Optional[str] = None) -> str:
    """Alias for format_confidence_tooltip()."""
    return format_confidence_tooltip(score, method=method)
