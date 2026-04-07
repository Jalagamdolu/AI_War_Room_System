"""
MarketingAgent
--------------
Analyses user feedback sentiment to surface perception trends,
recurring complaints, and positive signals. Calls SentimentAnalysisTool.
"""

from __future__ import annotations

from typing import Any

from tools import sentiment_tool

AGENT_NAME = "MarketingAgent"

# Thresholds
_CRISIS_NEG_RATIO = 0.55
_CONCERNING_NEG_RATIO = 0.35
_POSITIVE_TARGET = 0.60


def run(feedback_entries: list[str]) -> dict[str, Any]:
    """
    Analyse user feedback and return a structured perception report.

    Parameters
    ----------
    feedback_entries : list[str]
        Raw user feedback strings.

    Returns
    -------
    dict : perception_report
    """
    print(f"[{AGENT_NAME}] Starting user feedback analysis...")
    print(
        f"[{AGENT_NAME}] Calling SentimentAnalysisTool on "
        f"{len(feedback_entries)} feedback entries..."
    )

    raw = sentiment_tool.run(feedback_entries)

    print(f"[{AGENT_NAME}] Processing sentiment output...")

    perception_status = _assess_perception(raw)
    key_themes = _extract_key_themes(raw)
    narrative = _build_narrative(raw, perception_status, key_themes)

    report: dict[str, Any] = {
        "agent": AGENT_NAME,
        "perception_status": perception_status,
        "sentiment": {
            "label": raw["sentiment_label"],
            "positive_ratio": raw["positive_ratio"],
            "negative_ratio": raw["negative_ratio"],
            "neutral_count": raw["neutral_count"],
            "total_entries": raw["total_entries"],
        },
        "top_issues": raw["top_issues"],
        "keyword_frequency": raw["keyword_frequency"],
        "key_themes": key_themes,
        "narrative": narrative,
        "recommendation": _derive_recommendation(perception_status),
    }

    print(
        f"[{AGENT_NAME}] Analysis complete. "
        f"Perception={perception_status}, "
        f"neg_ratio={raw['negative_ratio']:.0%}, "
        f"top_issue={raw['top_issues'][0]['issue'] if raw['top_issues'] else 'none'}"
    )
    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assess_perception(raw: dict) -> str:
    neg = raw["negative_ratio"]
    if neg >= _CRISIS_NEG_RATIO:
        return "crisis"
    if neg >= _CONCERNING_NEG_RATIO:
        return "negative"
    if raw["positive_ratio"] >= _POSITIVE_TARGET:
        return "positive"
    return "mixed"


def _extract_key_themes(raw: dict) -> list[str]:
    """Distill the most important recurring themes."""
    themes = []
    top_issues = raw.get("top_issues", [])

    for issue in top_issues[:3]:
        count = issue["count"]
        tag = issue["issue"].replace("_", " ").title()
        themes.append(f"{tag} ({count} mentions)")

    label = raw.get("sentiment_label", "neutral")
    if label == "negative":
        themes.insert(0, "Predominantly negative user perception post-release")
    elif label == "positive":
        themes.insert(0, "Predominantly positive user reception")
    elif label == "mixed":
        themes.insert(0, "Mixed reception — quality concerns alongside positive praise")

    return themes


def _build_narrative(raw: dict, status: str, themes: list[str]) -> list[str]:
    """Generate a list of human-readable insight strings."""
    lines = []
    pos = raw["positive_ratio"]
    neg = raw["negative_ratio"]
    total = raw["total_entries"]

    lines.append(
        f"Analysed {total} feedback entries: "
        f"{pos:.0%} positive, {neg:.0%} negative, rest neutral."
    )

    top = raw.get("top_issues", [])
    if top:
        top_tag = top[0]["issue"].replace("_", " ")
        lines.append(
            f"Most reported issue: '{top_tag}' mentioned in {top[0]['count']} entries."
        )
        if len(top) > 1:
            second = top[1]["issue"].replace("_", " ")
            lines.append(
                f"Secondary issue cluster: '{second}' ({top[1]['count']} mentions)."
            )

    if status == "crisis":
        lines.append(
            "User sentiment is in CRISIS territory. Negative ratio exceeds 55%. "
            "Immediate public communication and hotfix are required."
        )
    elif status == "negative":
        lines.append(
            "User sentiment is predominantly negative. "
            "Marketing and product teams must align on a response strategy."
        )
    elif status == "positive":
        lines.append(
            "User sentiment is broadly positive. Feature highlights can be amplified."
        )
    else:
        lines.append(
            "Mixed feedback: positive features should be communicated while "
            "critical bug fixes are expedited."
        )

    return lines


def _derive_recommendation(status: str) -> str:
    mapping = {
        "crisis": (
            "HALT further rollout. Initiate incident comms. "
            "Priority hotfix for crash and loss-of-data bugs."
        ),
        "negative": (
            "Consider pausing rollout. Address top user pain points before continuing. "
            "Proactive user communication recommended."
        ),
        "mixed": (
            "Proceed cautiously. Fix critical bugs highlighted in feedback before "
            "expanding rollout."
        ),
        "positive": (
            "User reception is healthy. Continue rollout with standard monitoring."
        ),
    }
    return mapping.get(status, "Insufficient data.")
