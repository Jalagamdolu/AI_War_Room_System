"""
SentimentAnalysisTool
---------------------
Analyses user-feedback text entries to classify sentiment, extract
recurring issue keywords, and compute polarity ratios. Pure-Python,
zero external ML dependencies - production-ready as a rule-based baseline
that can be swapped for an LLM/ML backend via the same interface.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

_POSITIVE_SIGNALS = {
    "love", "great", "excellent", "amazing", "awesome", "fantastic",
    "wonderful", "perfect", "brilliant", "smooth", "fast", "easy",
    "good", "nice", "best", "helpful", "improved", "better", "happy",
    "satisfied", "outstanding", "superb", "clean", "intuitive", "solid",
    "reliable", "responsive", "efficient", "flawless", "seamless",
}

_NEGATIVE_SIGNALS = {
    "crash", "crashes", "crashed", "bug", "bugs", "broken", "freeze",
    "freezes", "slow", "laggy", "lag", "error", "errors", "fail",
    "fails", "failing", "terrible", "horrible", "awful", "worst",
    "hate", "useless", "unusable", "unresponsive", "frustrating",
    "disappointed", "disappointing", "problem", "issues", "issue",
    "overheating", "overheat", "draining", "drain", "drained",
    "missing", "lost", "stuck", "annoying", "confusing", "confused",
    "broken", "glitch", "glitches", "inconsistent", "unstable",
}

_ISSUE_KEYWORDS = {
    "crash": "app_crash",
    "crashes": "app_crash",
    "bug": "bug_report",
    "bugs": "bug_report",
    "slow": "performance",
    "laggy": "performance",
    "lag": "performance",
    "freeze": "freeze_hang",
    "freezes": "freeze_hang",
    "battery": "battery_drain",
    "draining": "battery_drain",
    "drain": "battery_drain",
    "login": "auth_issue",
    "logout": "auth_issue",
    "notification": "notification_issue",
    "notifications": "notification_issue",
    "payment": "payment_issue",
    "checkout": "payment_issue",
    "ui": "ui_ux",
    "layout": "ui_ux",
    "design": "ui_ux",
    "sync": "sync_issue",
    "syncing": "sync_issue",
    "data": "data_loss",
    "missing": "data_loss",
    "overheat": "overheating",
    "overheating": "overheating",
}

TOOL_NAME = "SentimentAnalysisTool"
TOOL_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(feedback_entries: list[str]) -> dict[str, Any]:
    """
    Analyse a list of user-feedback strings.

    Parameters
    ----------
    feedback_entries : list[str]

    Returns
    -------
    dict with keys
        - total_entries      : int
        - positive_count     : int
        - negative_count     : int
        - neutral_count      : int
        - positive_ratio     : float  (0-1)
        - negative_ratio     : float  (0-1)
        - sentiment_label    : "positive" | "negative" | "neutral" | "mixed"
        - top_issues         : list[{issue, count, example_quotes}]
        - keyword_frequency  : dict[str, int]  (raw word counts)
        - summary            : str  (human-readable summary)
    """
    print(
        f"    [Tool:{TOOL_NAME}] Analysing {len(feedback_entries)} feedback entries..."
    )

    if not feedback_entries:
        raise ValueError("feedback_entries must not be empty")

    results: list[dict[str, Any]] = [_classify_entry(e) for e in feedback_entries]

    positive = [r for r in results if r["sentiment"] == "positive"]
    negative = [r for r in results if r["sentiment"] == "negative"]
    neutral = [r for r in results if r["sentiment"] == "neutral"]

    total = len(results)
    pos_ratio = round(len(positive) / total, 3)
    neg_ratio = round(len(negative) / total, 3)

    # Determine overall label
    if pos_ratio > 0.6:
        label = "positive"
    elif neg_ratio > 0.5:
        label = "negative"
    elif pos_ratio > 0.4 and neg_ratio > 0.3:
        label = "mixed"
    else:
        label = "neutral"

    # Issue aggregation
    issue_entries: dict[str, list[str]] = {}
    all_keywords: list[str] = []
    for r in results:
        all_keywords.extend(r["matched_keywords"])
        for issue_tag in r["issue_tags"]:
            issue_entries.setdefault(issue_tag, [])
            issue_entries[issue_tag].append(r["text"])

    keyword_freq = dict(Counter(all_keywords).most_common(15))

    top_issues = [
        {
            "issue": tag,
            "count": len(entries),
            "example_quotes": entries[:2],  # first 2 examples
        }
        for tag, entries in sorted(
            issue_entries.items(), key=lambda x: -len(x[1])
        )[:5]
    ]

    summary = (
        f"Out of {total} feedback entries: "
        f"{len(positive)} positive ({pos_ratio:.0%}), "
        f"{len(negative)} negative ({neg_ratio:.0%}), "
        f"{len(neutral)} neutral. "
        f"Overall sentiment: {label.upper()}. "
        f"Top issue: {top_issues[0]['issue'] if top_issues else 'none'}."
    )

    print(
        f"    [Tool:{TOOL_NAME}] Done. Sentiment={label}, "
        f"pos={pos_ratio:.0%}, neg={neg_ratio:.0%}, "
        f"issues found: {len(top_issues)}"
    )

    return {
        "total_entries": total,
        "positive_count": len(positive),
        "negative_count": len(negative),
        "neutral_count": len(neutral),
        "positive_ratio": pos_ratio,
        "negative_ratio": neg_ratio,
        "sentiment_label": label,
        "top_issues": top_issues,
        "keyword_frequency": keyword_freq,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lowercase + split into word tokens, stripping punctuation."""
    return re.findall(r"[a-z]+", text.lower())


def _classify_entry(text: str) -> dict[str, Any]:
    """Classify a single feedback entry."""
    tokens = _tokenise(text)
    token_set = set(tokens)

    pos_hits = token_set & _POSITIVE_SIGNALS
    neg_hits = token_set & _NEGATIVE_SIGNALS

    matched_keywords = list(pos_hits | neg_hits)

    issue_tags = list(
        {_ISSUE_KEYWORDS[t] for t in tokens if t in _ISSUE_KEYWORDS}
    )

    if pos_hits and not neg_hits:
        sentiment = "positive"
    elif neg_hits and not pos_hits:
        sentiment = "negative"
    elif neg_hits and pos_hits:
        # More negative signals → negative
        sentiment = "negative" if len(neg_hits) >= len(pos_hits) else "positive"
    else:
        sentiment = "neutral"

    return {
        "text": text,
        "sentiment": sentiment,
        "matched_keywords": matched_keywords,
        "issue_tags": issue_tags,
    }
