"""
CriticAgent (Risk / Critic)
---------------------------
Challenges assumptions from other agents, identifies risks,
gaps in evidence, and produces a structured risk register.
This agent acts as the adversarial reviewer in the war room.
"""

from __future__ import annotations

from typing import Any
import json

from utils.llm_client import call_llm

AGENT_NAME = "CriticAgent"

# Risk severity levels
_SEVERITY_CRITICAL = "Critical"
_SEVERITY_HIGH = "High"
_SEVERITY_MEDIUM = "Medium"
_SEVERITY_LOW = "Low"


def run(
    metrics_report: dict[str, Any],
    sentiment_report: dict[str, Any],
    pm_report: dict[str, Any],
    release_notes: str,
) -> dict[str, Any]:
    """
    Review all agent outputs and produce a structured risk register.

    Parameters
    ----------
    metrics_report   : output from DataAnalystAgent
    sentiment_report : output from MarketingAgent
    pm_report        : output from ProductManagerAgent
    release_notes    : raw release notes text

    Returns
    -------
    dict : risk_assessment
    """
    print(f"[{AGENT_NAME}] Challenging assumptions and identifying risks...")

    risks = []
    challenges = []
    missing_evidence = []

    # --- Technical risks ---
    risks.extend(_assess_technical_risks(metrics_report))

    # --- User experience risks ---
    risks.extend(_assess_ux_risks(sentiment_report))

    # --- Decision risks (challenge PM) ---
    pm_challenges, pm_risks = _challenge_pm_decision(pm_report, metrics_report)
    challenges.extend(pm_challenges)
    risks.extend(pm_risks)

    # --- Known issue risks ---
    risks.extend(_assess_known_issue_risks(release_notes))

    # --- Missing evidence ---
    missing_evidence.extend(_identify_missing_evidence(metrics_report, sentiment_report))

    # --- Action plan ---
    action_plan = _build_action_plan(risks)

    report: dict[str, Any] = {
        "agent": AGENT_NAME,
        "risk_register": risks,
        "risk_count": len(risks),
        "critical_risks": [r for r in risks if r["severity"] == _SEVERITY_CRITICAL],
        "challenges_to_pm": challenges,
        "missing_evidence": missing_evidence,
        "action_plan": action_plan,
        "overall_risk_level": _overall_risk_level(risks),
        "llm_critique": _call_llm_for_critique(pm_report, risks, missing_evidence),
    }

    critical_count = len(report["critical_risks"])
    print(
        f"[{AGENT_NAME}] Risk register built. "
        f"Total risks: {len(risks)}, "
        f"Critical: {critical_count}"
    )
    return report


# ---------------------------------------------------------------------------
# Internal risk assessment methods
# ---------------------------------------------------------------------------

def _assess_technical_risks(metrics: dict) -> list[dict]:
    risks = []
    pm = metrics.get("per_metric", {})

    # Crash rate escalation risk
    crash = pm.get("crash_rate", {})
    crash_val = crash.get("last_value", 0)
    crash_trend = crash.get("trend", "stable")
    if crash_val > 0.05 and crash_trend == "increasing":
        risks.append({
            "risk": "Crash rate is at {:.1%} and still increasing — no recovery signal.".format(crash_val),
            "severity": _SEVERITY_CRITICAL,
            "category": "Technical Stability",
            "mitigation": "Immediate rollback or targeted force-update with hotfix build.",
            "evidence": f"crash_rate={crash_val:.1%}, trend={crash_trend}",
        })
    elif crash_val > 0.02:
        risks.append({
            "risk": "Crash rate ({:.1%}) exceeds acceptable threshold of 2%.".format(crash_val),
            "severity": _SEVERITY_HIGH,
            "category": "Technical Stability",
            "mitigation": "Deploy emergency patch targeting BUG-1091. Monitor crash-free sessions.",
            "evidence": f"crash_rate={crash_val:.1%}",
        })

    # Latency degradation risk
    lat = pm.get("latency_ms", {})
    lat_val = lat.get("last_value", 0)
    lat_trend = lat.get("trend", "stable")
    if lat_val >= 450:
        risks.append({
            "risk": f"Latency at {lat_val:.0f}ms (SLO = 300ms) — requests may begin timing out.",
            "severity": _SEVERITY_CRITICAL,
            "category": "Performance / SLO",
            "mitigation": "Scale backend horizontally. Profile and optimise hot code paths immediately.",
            "evidence": f"latency_ms={lat_val:.0f}, trend={lat_trend}",
        })
    elif lat_val >= 310:
        risks.append({
            "risk": f"Latency ({lat_val:.0f}ms) is approaching SLO ceiling of 300ms.",
            "severity": _SEVERITY_HIGH,
            "category": "Performance / SLO",
            "mitigation": "Enable request caching layer. Investigate database query plans.",
            "evidence": f"latency_ms={lat_val:.0f}",
        })

    # Retention freefall risk
    ret_d1 = pm.get("retention_d1", {})
    ret_pct = ret_d1.get("pct_change", 0)
    if ret_pct < -40:
        risks.append({
            "risk": f"D1 retention collapsed {ret_pct:+.1f}% — product is failing first-day experience.",
            "severity": _SEVERITY_CRITICAL,
            "category": "Retention / Churn",
            "mitigation": "Audit first-run experience. Fix crashes on onboarding flows.",
            "evidence": f"retention_d1 pct_change={ret_pct:.1f}%",
        })

    # Support surge risk
    tix = pm.get("support_tickets", {})
    tix_pct = tix.get("pct_change", 0)
    if tix_pct > 1000:
        risks.append({
            "risk": f"Support tickets surged {tix_pct:+.0f}% — support team will be overwhelmed.",
            "severity": _SEVERITY_HIGH,
            "category": "Operations",
            "mitigation": "Activate overflow support response. Publish a known-issues status page.",
            "evidence": f"support_ticket pct_change={tix_pct:.0f}%",
        })

    return risks


def _assess_ux_risks(sentiment: dict) -> list[dict]:
    risks = []
    neg = sentiment.get("sentiment", {}).get("negative_ratio", 0)
    top_issues = sentiment.get("top_issues", [])

    if neg >= 0.55:
        risks.append({
            "risk": f"User sentiment is {neg:.0%} negative — brand perception may be permanently damaged.",
            "severity": _SEVERITY_CRITICAL,
            "category": "Brand / Reputation",
            "mitigation": (
                "Publish executive-level incident acknowledgement. "
                "Offer affected users compensation or service credits."
            ),
            "evidence": f"negative_ratio={neg:.1%}",
        })
    elif neg >= 0.35:
        risks.append({
            "risk": f"Negative sentiment ({neg:.0%}) signals widespread dissatisfaction.",
            "severity": _SEVERITY_HIGH,
            "category": "Brand / Reputation",
            "mitigation": "Proactive user communication via email and in-app notification.",
            "evidence": f"negative_ratio={neg:.1%}",
        })

    # App crash mentions in feedback
    for issue in top_issues:
        if issue["issue"] == "app_crash" and issue["count"] >= 5:
            risks.append({
                "risk": f"App crash mentioned in {issue['count']} feedback entries — users actively affected.",
                "severity": _SEVERITY_HIGH,
                "category": "User Experience",
                "mitigation": "Instrument crash reporter; isolate reproducible scenario for hotfix.",
                "evidence": f"feedback issue count={issue['count']}",
            })
            break

    return risks


def _challenge_pm_decision(pm: dict, metrics: dict) -> tuple[list[str], list[dict]]:
    """Produce adversarial challenges against the PM's proposed decision."""
    challenges = []
    risks = []
    decision = pm.get("proposed_decision", "Unknown")
    failures = [k for k, v in pm.get("criteria_evaluation", {}).items() if not v["passed"]]

    if decision == "Proceed":
        challenges.append(
            "CHALLENGE: PM proposes 'Proceed' but metrics show a CRITICAL health state. "
            "Growth in DAU does not compensate for rising crash rates and retention collapse."
        )
        risks.append({
            "risk": "Proceeding despite critical metric failures creates legal and reputational liability.",
            "severity": _SEVERITY_HIGH,
            "category": "Decision Risk",
            "mitigation": "Revisit decision in emergency war room meeting with engineering leads.",
            "evidence": f"PM proposed Proceed; criteria failures={failures}",
        })
    elif decision == "Pause":
        pm_val = pm.get("per_metric", {})
        crash_val = metrics.get("per_metric", {}).get("crash_rate", {}).get("last_value", 0)
        if crash_val > 0.07:
            challenges.append(
                "CHALLENGE: PM proposes 'Pause' but crash rate exceeds 7%. "
                "Pause is insufficient — a rollback may be necessary to protect active users."
            )

    if len(failures) > 3 and decision != "Roll Back":
        challenges.append(
            f"CHALLENGE: {len(failures)} criteria have failed yet the decision is not 'Roll Back'. "
            "Consider the compounding effect of simultaneous metric degradation."
        )

    return challenges, risks


def _assess_known_issue_risks(notes: str) -> list[dict]:
    """Convert known high-severity bugs into risk register entries."""
    risks = []
    lines = notes.splitlines()
    for line in lines:
        if "HIGH" in line and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                bug_id = parts[0]
                description = parts[2]
                risks.append({
                    "risk": f"Known HIGH severity bug still open: {description} ({bug_id})",
                    "severity": _SEVERITY_HIGH,
                    "category": "Known Bugs",
                    "mitigation": f"Escalate {bug_id} to on-call engineering. Patch must ship in next 24h.",
                    "evidence": f"Documented in release notes: {bug_id}",
                })
    return risks


def _identify_missing_evidence(metrics: dict, sentiment: dict) -> list[str]:
    """Flag gaps in available evidence that weaken the decision."""
    gaps = []
    pm = metrics.get("per_metric", {})

    if "revenue" not in pm:
        gaps.append("Revenue and GMV impact data not available. Financial risk unquantified.")
    if "churn_rate" not in pm:
        gaps.append("Churn rate not tracked. Long-term retention impact unknown.")
    if sentiment.get("sentiment", {}).get("total_entries", 0) < 50:
        gaps.append(
            "Feedback sample size is small (<50 entries). "
            "Sentiment ratios may not represent full user base."
        )
    if "beta_test_results" not in metrics:
        gaps.append("No beta test baseline provided. Before/after comparison unavailable.")

    return gaps


def _build_action_plan(risks: list[dict]) -> list[dict[str, str]]:
    """Derive a prioritised action plan from the risk register."""
    plan = []
    seen_categories: set[str] = set()

    priority_order = [_SEVERITY_CRITICAL, _SEVERITY_HIGH, _SEVERITY_MEDIUM, _SEVERITY_LOW]
    sorted_risks = sorted(risks, key=lambda r: priority_order.index(r["severity"]))

    for risk in sorted_risks:
        cat = risk["category"]
        if cat not in seen_categories:
            seen_categories.add(cat)
            plan.append({
                "action": risk["mitigation"],
                "owner": _infer_owner(cat),
                "priority": risk["severity"],
            })

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


def _overall_risk_level(risks: list[dict]) -> str:
    severities = {r["severity"] for r in risks}
    if _SEVERITY_CRITICAL in severities:
        return "Critical"
    if _SEVERITY_HIGH in severities:
        return "High"
    if _SEVERITY_MEDIUM in severities:
        return "Medium"
    return "Low"


def _call_llm_for_critique(pm: dict, risks: list[dict], gaps: list[str]) -> str | None:
    system_prompt = (
        "You are an adversarial Risk Assessor in a war room. "
        "Review the Product Manager's decision, the identified risks, and missing evidence. "
        "Highlight the most severe risk, challenge any flawed assumptions in the decision, "
        "and point out what data is missing. "
        "Do NOT output JSON. Output formatting as markdown bullet points."
    )
    
    # Strip down context to avoid massive token usage
    pm_decision = pm.get("proposed_decision", "Unknown")
    top_risks = [r["risk"] for r in risks if r["severity"] in ("Critical", "High")][:3]

    user_prompt = f"""
PM Decision: {pm_decision}

Key Risks:
{json.dumps(top_risks, indent=2)}

Missing Evidence:
{json.dumps(gaps, indent=2)}
"""
    return call_llm(system_prompt, user_prompt)

