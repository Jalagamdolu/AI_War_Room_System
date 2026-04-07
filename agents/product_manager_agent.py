"""
ProductManagerAgent
-------------------
Evaluates the launch decision based on pre-defined success criteria,
aggregated metric signals, and user sentiment. Proposes an initial
decision (Proceed / Pause / Roll Back) with rationale.
"""

from __future__ import annotations

from typing import Any
import json

from utils.llm_client import call_llm

AGENT_NAME = "ProductManagerAgent"

# ---------------------------------------------------------------------------
# Success Criteria
# ---------------------------------------------------------------------------

SUCCESS_CRITERIA = {
    "crash_rate_max": 0.02,           # 2%
    "latency_max_ms": 350,
    "retention_d1_min": 0.45,         # 45%
    "retention_d7_min": 0.20,         # 20%
    "conversion_rate_min": 0.025,     # 2.5%
    "negative_sentiment_max": 0.45,   # 45%
    "support_ticket_surge_max": 300,  # %
}


def run(
    metrics_report: dict[str, Any],
    sentiment_report: dict[str, Any],
    release_notes: str,
) -> dict[str, Any]:
    """
    Evaluate launch decision from aggregated data.

    Parameters
    ----------
    metrics_report    : output from DataAnalystAgent
    sentiment_report  : output from MarketingAgent
    release_notes     : raw release notes text

    Returns
    -------
    dict : decision_proposal
    """
    print(f"[{AGENT_NAME}] Evaluating launch decision against success criteria...")

    criteria_results = _evaluate_criteria(metrics_report, sentiment_report)
    impact_assessment = _assess_user_impact(metrics_report, sentiment_report)
    decision, decision_rationale = _propose_decision(criteria_results, impact_assessment)

    report: dict[str, Any] = {
        "agent": AGENT_NAME,
        "success_criteria": SUCCESS_CRITERIA,
        "criteria_evaluation": criteria_results,
        "criteria_passed": sum(1 for r in criteria_results.values() if r["passed"]),
        "criteria_total": len(criteria_results),
        "impact_assessment": impact_assessment,
        "proposed_decision": decision,
        "decision_rationale": decision_rationale,
        "llm_reasoning": _call_llm_for_reasoning(metrics_report, sentiment_report, decision),
        "known_issues_acknowledged": _extract_known_issues(release_notes),
    }

    passed = report["criteria_passed"]
    total = report["criteria_total"]
    print(
        f"[{AGENT_NAME}] Criteria passed: {passed}/{total}. "
        f"Proposed decision: {decision}"
    )
    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _evaluate_criteria(
    metrics: dict, sentiment: dict
) -> dict[str, dict[str, Any]]:
    """Check each success criterion and return pass/fail with values."""
    pm = metrics.get("per_metric", {})
    results: dict[str, dict] = {}

    # Crash rate
    crash_val = pm.get("crash_rate", {}).get("last_value", None)
    results["crash_rate"] = {
        "threshold": SUCCESS_CRITERIA["crash_rate_max"],
        "actual": crash_val,
        "passed": crash_val is not None and crash_val <= SUCCESS_CRITERIA["crash_rate_max"],
        "note": f"Actual {crash_val:.1%}" if crash_val is not None else "N/A",
    }

    # Latency
    lat_val = pm.get("latency_ms", {}).get("last_value", None)
    results["latency_ms"] = {
        "threshold": SUCCESS_CRITERIA["latency_max_ms"],
        "actual": lat_val,
        "passed": lat_val is not None and lat_val <= SUCCESS_CRITERIA["latency_max_ms"],
        "note": f"Actual {lat_val:.0f}ms" if lat_val is not None else "N/A",
    }

    # Retention D1
    ret_d1 = pm.get("retention_d1", {}).get("last_value", None)
    results["retention_d1"] = {
        "threshold": SUCCESS_CRITERIA["retention_d1_min"],
        "actual": ret_d1,
        "passed": ret_d1 is not None and ret_d1 >= SUCCESS_CRITERIA["retention_d1_min"],
        "note": f"Actual {ret_d1:.1%}" if ret_d1 is not None else "N/A",
    }

    # Retention D7
    ret_d7 = pm.get("retention_d7", {}).get("last_value", None)
    results["retention_d7"] = {
        "threshold": SUCCESS_CRITERIA["retention_d7_min"],
        "actual": ret_d7,
        "passed": ret_d7 is not None and ret_d7 >= SUCCESS_CRITERIA["retention_d7_min"],
        "note": f"Actual {ret_d7:.1%}" if ret_d7 is not None else "N/A",
    }

    # Conversion rate
    conv = pm.get("conversion_rate", {}).get("last_value", None)
    results["conversion_rate"] = {
        "threshold": SUCCESS_CRITERIA["conversion_rate_min"],
        "actual": conv,
        "passed": conv is not None and conv >= SUCCESS_CRITERIA["conversion_rate_min"],
        "note": f"Actual {conv:.1%}" if conv is not None else "N/A",
    }

    # Negative sentiment
    neg_ratio = sentiment.get("sentiment", {}).get("negative_ratio", None)
    results["negative_sentiment"] = {
        "threshold": SUCCESS_CRITERIA["negative_sentiment_max"],
        "actual": neg_ratio,
        "passed": neg_ratio is not None and neg_ratio <= SUCCESS_CRITERIA["negative_sentiment_max"],
        "note": f"Actual {neg_ratio:.1%}" if neg_ratio is not None else "N/A",
    }

    return results


def _assess_user_impact(metrics: dict, sentiment: dict) -> list[str]:
    """Qualitative user impact statements."""
    impacts = []
    pm = metrics.get("per_metric", {})

    crash = pm.get("crash_rate", {}).get("last_value", 0)
    if crash > 0.05:
        impacts.append(
            f"~{crash:.0%} of sessions end in a crash — users are actively losing work."
        )

    tix_pct = pm.get("support_tickets", {}).get("pct_change", 0)
    if tix_pct > 400:
        impacts.append(
            f"Support volume increased {tix_pct:+.0f}% — support team overwhelmed."
        )

    neg = sentiment.get("sentiment", {}).get("negative_ratio", 0)
    if neg > 0.5:
        impacts.append(
            f"{neg:.0%} of users express negative sentiment — brand damage risk."
        )

    top_issues = sentiment.get("top_issues", [])
    if top_issues:
        tag = top_issues[0]["issue"].replace("_", " ")
        count = top_issues[0]["count"]
        impacts.append(f"'{tag}' is the most reported user pain point ({count} mentions).")

    return impacts


def _propose_decision(
    criteria: dict, impact: list[str]
) -> tuple[str, list[str]]:
    """Simple decision heuristic based on critical criteria failures."""
    failures = [k for k, v in criteria.items() if not v["passed"]]
    critical_failures = [
        k for k in failures
        if k in ("crash_rate", "latency_ms", "retention_d1", "negative_sentiment")
    ]

    if len(critical_failures) >= 3 or (
        "crash_rate" in critical_failures and "negative_sentiment" in critical_failures
    ):
        decision = "Roll Back"
        rationale = [
            f"Critical failure in {len(critical_failures)} key metrics: "
            f"{', '.join(critical_failures)}.",
            "User impact is severe and the release cannot sustain further exposure.",
        ] + impact
    elif len(failures) >= 2:
        decision = "Pause"
        rationale = [
            f"{len(failures)} success criteria failed: {', '.join(failures)}.",
            "Release should be paused pending investigation and hotfix deployment.",
        ] + impact
    else:
        decision = "Proceed"
        rationale = [
            f"Only {len(failures)} criteria failed — within acceptable tolerance.",
            "Release can proceed with enhanced monitoring.",
        ]

    return decision, rationale


def _extract_known_issues(notes: str) -> list[str]:
    """Parse HIGH severity known issues from release notes."""
    lines = notes.splitlines()
    issues = []
    for line in lines:
        if "HIGH" in line and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                issues.append(f"{parts[0]}: {parts[2]}")
    return issues


def _call_llm_for_reasoning(metrics: dict, sentiment: dict, pm_decision: str) -> str | None:
    system_prompt = (
        "You are an expert Product Manager analyzing a software launch. "
        "Review the summarized metrics and user sentiment. "
        "The rule-based system has proposed a decision. "
        "Provide bullet points explaining the decision, risks, and next steps for the team. "
        "Do NOT output JSON. Output formatting as markdown bullet points."
    )
    
    # Strip down context to avoid massive token usage
    metrics_context = {
        "overall_health": metrics.get("overall_health"),
        "key_findings": metrics.get("key_findings"),
        "anomalies": metrics.get("anomaly_summary"),
    }
    sentiment_context = {
        "perception": sentiment.get("perception_status"),
        "top_issues": [i["issue"] for i in sentiment.get("top_issues", [])],
        "sentiment_ratios": f"Positive: {sentiment.get('sentiment', {}).get('positive_ratio', 0):.0%}, Negative: {sentiment.get('sentiment', {}).get('negative_ratio', 0):.0%}"
    }

    user_prompt = f"""
Rule-Based System Proposed Decision: {pm_decision}

Metrics context:
{json.dumps(metrics_context, indent=2)}

Sentiment context:
{json.dumps(sentiment_context, indent=2)}
"""
    return call_llm(system_prompt, user_prompt)

