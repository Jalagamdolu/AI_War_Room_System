"""
EvaluatorAgent
--------------
Synthesises outputs from all agents and assigns a calibrated
confidence score (0.0 – 1.0) to the final decision.
Also generates the communication plan for internal and external stakeholders.
"""

from __future__ import annotations

from typing import Any

AGENT_NAME = "EvaluatorAgent"


def run(
    metrics_report: dict[str, Any],
    sentiment_report: dict[str, Any],
    pm_report: dict[str, Any],
    critic_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate confidence in the war room decision.

    Parameters
    ----------
    metrics_report   : output from DataAnalystAgent
    sentiment_report : output from MarketingAgent
    pm_report        : output from ProductManagerAgent
    critic_report    : output from CriticAgent

    Returns
    -------
    dict : evaluation_report
    """
    print(f"[{AGENT_NAME}] Calculating confidence score and generating communication plan...")

    confidence, confidence_breakdown = _calculate_confidence(
        metrics_report, sentiment_report, pm_report, critic_report
    )

    final_decision = _arbitrate_decision(pm_report, critic_report, confidence)

    rationale = _build_rationale(metrics_report, sentiment_report, critic_report, final_decision)

    comm_plan = _build_communication_plan(final_decision, critic_report)

    report: dict[str, Any] = {
        "agent": AGENT_NAME,
        "final_decision": final_decision,
        "confidence_score": confidence,
        "confidence_breakdown": confidence_breakdown,
        "confidence_label": _confidence_label(confidence),
        "decision_rationale": rationale,
        "communication_plan": comm_plan,
    }

    print(
        f"[{AGENT_NAME}] Evaluation complete. "
        f"Final decision: {final_decision}, "
        f"Confidence: {confidence:.2f} ({report['confidence_label']})"
    )
    return report


# ---------------------------------------------------------------------------
# Internal scoring
# ---------------------------------------------------------------------------

def _calculate_confidence(
    metrics: dict, sentiment: dict, pm: dict, critic: dict
) -> tuple[float, dict]:
    """
    Score based on four pillars (each 0.0–1.0), then weighted average.
    """
    scores: dict[str, float] = {}

    # 1. Metric health (0 = critical, 1 = healthy)
    health_map = {"healthy": 1.0, "concerning": 0.5, "critical": 0.1}
    scores["metric_health"] = health_map.get(metrics.get("overall_health", "critical"), 0.1)

    # 2. Criteria pass rate
    passed = pm.get("criteria_passed", 0)
    total = pm.get("criteria_total", 1)
    scores["criteria_pass_rate"] = passed / total

    # 3. Sentiment score (inverted negative ratio)
    neg = sentiment.get("sentiment", {}).get("negative_ratio", 1.0)
    scores["sentiment"] = max(0.0, 1.0 - (neg * 1.5))  # penalise heavily

    # 4. Risk level penalty
    risk_penalty = {"Critical": 0.1, "High": 0.4, "Medium": 0.65, "Low": 0.9}
    scores["risk_level"] = risk_penalty.get(
        critic.get("overall_risk_level", "Critical"), 0.1
    )

    # Weighted average
    weights = {
        "metric_health": 0.35,
        "criteria_pass_rate": 0.25,
        "sentiment": 0.20,
        "risk_level": 0.20,
    }
    confidence = sum(scores[k] * weights[k] for k in scores)
    confidence = round(max(0.0, min(1.0, confidence)), 3)

    breakdown = {
        pillar: {"score": round(scores[pillar], 3), "weight": weights[pillar]}
        for pillar in scores
    }
    return confidence, breakdown


def _arbitrate_decision(pm: dict, critic: dict, confidence: float) -> str:
    """
    Final arbitration between PM proposal and critic risk level.
    Critic can escalate severity; confidence can de-escalate.
    """
    pm_decision = pm.get("proposed_decision", "Pause")
    risk_level = critic.get("overall_risk_level", "High")
    critical_risks = critic.get("critical_risks", [])

    # If there are critical risks and PM says Proceed ➜ override to Roll Back
    if critical_risks and pm_decision == "Proceed":
        return "Roll Back"

    # If critical risk level and PM says Proceed or Pause ➜ Roll Back
    if risk_level == "Critical" and pm_decision in ("Proceed", "Pause"):
        return "Roll Back"

    # If confidence is very low and PM says Proceed ➜ at least Pause
    if confidence < 0.3 and pm_decision == "Proceed":
        return "Pause"

    return pm_decision


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High Confidence"
    if score >= 0.50:
        return "Moderate Confidence"
    if score >= 0.25:
        return "Low Confidence"
    return "Very Low Confidence"


def _build_rationale(
    metrics: dict, sentiment: dict, critic: dict, decision: str
) -> list[str]:
    rationale = []

    health = metrics.get("overall_health", "unknown")
    rationale.append(
        f"Metric health assessed as '{health}' across "
        f"{len(metrics.get('metrics_analysed', []))} tracked KPIs."
    )

    neg = sentiment.get("sentiment", {}).get("negative_ratio", 0)
    top_issues = sentiment.get("top_issues", [])
    rationale.append(
        f"User sentiment is {neg:.0%} negative. "
        f"Top user issue: '{top_issues[0]['issue'].replace('_', ' ')}' "
        f"({top_issues[0]['count']} mentions)."
        if top_issues else
        f"User sentiment is {neg:.0%} negative."
    )

    anomalies = metrics.get("anomaly_summary", [])
    if anomalies:
        rationale.append(
            f"{len(anomalies)} metric anomalies detected: {anomalies[0]}"
        )

    critical_count = len(critic.get("critical_risks", []))
    if critical_count:
        rationale.append(
            f"{critical_count} critical risks identified by CriticAgent. "
            "Decision reflects the need for immediate corrective action."
        )

    if decision == "Roll Back":
        rationale.append(
            "Decision: ROLL BACK. The combination of rising crash rates, "
            "retention collapse, and negative user sentiment makes continued "
            "rollout untenable. Rollback protects users and limits brand damage."
        )
    elif decision == "Pause":
        rationale.append(
            "Decision: PAUSE. Release has potential but current stability and "
            "sentiment metrics require intervention before further rollout."
        )
    else:
        rationale.append(
            "Decision: PROCEED. Metrics are within acceptable thresholds. "
            "Standard monitoring protocols should be maintained."
        )

    return rationale


def _build_communication_plan(decision: str, critic: dict) -> list[str]:
    plan = []

    if decision == "Roll Back":
        plan += [
            "[Internal] Immediately notify Engineering, Product, and Executive leadership of rollback.",
            "[Internal] Activate incident bridge and assign incident commander.",
            "[Internal] Engineering team to initiate rollback procedure to v3.1.x within 1 hour.",
            "[Internal] SRE to monitor rollback deployment and verify metric normalisation.",
            "[Customer] Publish status page incident: 'We are aware of issues affecting v3.2.0 and are rolling back.'",
            "[Customer] In-app banner acknowledging the issue and informing users of the fix timeline.",
            "[Customer] Email to affected users with apology and ETA for resolution.",
            "[Press] Prepare reactive comms statement if press inquiries arise.",
        ]
    elif decision == "Pause":
        plan += [
            "[Internal] Alert Engineering and Product leads to halt Phase 3 rollout.",
            "[Internal] Convene emergency sprint planning for hotfix prioritisation.",
            "[Internal] Daily war room standups until KPIs recover to target thresholds.",
            "[Customer] Update status page with 'Investigating reported issues in v3.2.0'.",
            "[Customer] Proactive in-app notification to affected users acknowledging known issues.",
        ]
    else:
        plan += [
            "[Internal] Share positive launch report with stakeholders.",
            "[Internal] Continue enhanced monitoring for 72 hours post-launch.",
            "[Customer] Announce feature highlights via push notification and blog post.",
        ]

    # Add risk-specific communications
    for risk in critic.get("critical_risks", [])[:2]:
        plan.append(
            f"[Internal] Track remediation of: '{risk['risk'][:80]}...' — assign to {_infer_owner(risk['category'])}."
        )

    return plan


def _infer_owner(category: str) -> str:
    mapping = {
        "Technical Stability": "Engineering / SRE",
        "Performance / SLO": "Backend Engineering",
        "Retention / Churn": "Product & Growth",
        "Operations": "Customer Support",
        "Brand / Reputation": "Marketing & Comms",
        "User Experience": "Engineering / Design",
        "Decision Risk": "Executive / War Room",
        "Known Bugs": "Engineering / Release",
    }
    return mapping.get(category, "Cross-functional Team")
