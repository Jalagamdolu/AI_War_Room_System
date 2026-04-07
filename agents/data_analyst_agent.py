"""
DataAnalystAgent
----------------
Responsible for analysing time-series product metrics.
Calls MetricsAnalysisTool and produces a structured metrics report
with trend commentary and anomaly highlights.
"""

from __future__ import annotations

from typing import Any

from tools import metrics_tool

AGENT_NAME = "DataAnalystAgent"

# Thresholds for human-readable assessments
_CRITICAL_CRASH_RATE = 0.05      # 5%
_CONCERNING_CRASH_RATE = 0.02    # 2%
_CRITICAL_LATENCY_MS = 400
_CONCERNING_LATENCY_MS = 300
_CRITICAL_RETENTION_DROP = -30   # % change
_CONCERNING_RETENTION_DROP = -15


def run(time_series: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyse product metrics and return a structured report.

    Parameters
    ----------
    time_series : list of daily metric records (from metrics.json)

    Returns
    -------
    dict : metrics_report
    """
    print(f"[{AGENT_NAME}] Starting metrics analysis...")
    print(f"[{AGENT_NAME}] Calling MetricsAnalysisTool with {len(time_series)} data points...")

    raw = metrics_tool.run(time_series)

    print(f"[{AGENT_NAME}] Processing tool output...")

    # Build human-readable commentary
    comments: list[str] = []
    key_findings: list[str] = []
    per_metric = raw["per_metric"]

    # --- Crash rate assessment ---
    crash = per_metric.get("crash_rate", {})
    if crash:
        last_crash = crash.get("last_value", 0)
        crash_pct = crash.get("pct_change", 0)
        if last_crash >= _CRITICAL_CRASH_RATE:
            comments.append(
                f"CRITICAL: Crash rate at {last_crash:.1%} ({crash_pct:+.1f}% vs baseline). "
                "Well above 2% acceptable threshold."
            )
            key_findings.append(f"Crash rate critical at {last_crash:.1%}")
        elif last_crash >= _CONCERNING_CRASH_RATE:
            comments.append(
                f"CONCERN: Crash rate at {last_crash:.1%} ({crash_pct:+.1f}%). Above normal range."
            )
            key_findings.append(f"Crash rate elevated at {last_crash:.1%}")

    # --- Latency assessment ---
    lat = per_metric.get("latency_ms", {})
    if lat:
        last_lat = lat.get("last_value", 0)
        lat_pct = lat.get("pct_change", 0)
        if last_lat >= _CRITICAL_LATENCY_MS:
            comments.append(
                f"CRITICAL: Latency at {last_lat:.0f}ms ({lat_pct:+.1f}%). "
                "Severely degraded — SLO breached."
            )
            key_findings.append(f"Latency critical at {last_lat:.0f}ms")
        elif last_lat >= _CONCERNING_LATENCY_MS:
            comments.append(
                f"CONCERN: Latency at {last_lat:.0f}ms ({lat_pct:+.1f}%). Approaching SLO boundary."
            )

    # --- Retention assessment ---
    for key_name in ("retention_d1", "retention_d7"):
        ret = per_metric.get(key_name, {})
        if ret:
            pct = ret.get("pct_change", 0)
            if pct <= _CRITICAL_RETENTION_DROP:
                label = "D1" if key_name == "retention_d1" else "D7"
                comments.append(
                    f"CRITICAL: {label} retention declined {pct:+.1f}% since launch. "
                    "Severe user abandonment signal."
                )
                key_findings.append(f"{label} retention dropped {pct:+.1f}%")
            elif pct <= _CONCERNING_RETENTION_DROP:
                label = "D1" if key_name == "retention_d1" else "D7"
                comments.append(
                    f"CONCERN: {label} retention down {pct:+.1f}%. Needs monitoring."
                )

    # --- DAU trend ---
    dau = per_metric.get("dau", {})
    if dau:
        dau_pct = dau.get("pct_change", 0)
        dau_trend = dau.get("trend")
        if dau_trend == "increasing":
            comments.append(
                f"POSITIVE: DAU grew {dau_pct:+.1f}%, indicating growing user adoption."
            )
        elif dau_trend == "decreasing":
            comments.append(
                f"CONCERN: DAU declining ({dau_pct:+.1f}%) — users may be churning post-exposure."
            )
            key_findings.append(f"DAU declining {dau_pct:+.1f}%")

    # --- Support tickets ---
    tix = per_metric.get("support_tickets", {})
    if tix:
        tix_pct = tix.get("pct_change", 0)
        if tix_pct > 200:
            comments.append(
                f"CRITICAL: Support tickets surged {tix_pct:+.1f}% — strong user frustration signal."
            )
            key_findings.append(f"Support tickets surged {tix_pct:+.1f}%")

    report: dict[str, Any] = {
        "agent": AGENT_NAME,
        "overall_health": raw["overall_health"],
        "metrics_analysed": raw["metrics_analysed"],
        "anomaly_summary": raw["anomaly_summary"],
        "per_metric": per_metric,
        "key_findings": key_findings,
        "commentary": comments,
        "recommendation": _derive_recommendation(raw["overall_health"]),
    }

    print(
        f"[{AGENT_NAME}] Analysis complete. "
        f"Health={report['overall_health']}, "
        f"Findings={len(key_findings)}, "
        f"Anomalies={len(raw['anomaly_summary'])}"
    )
    return report


def _derive_recommendation(health: str) -> str:
    mapping = {
        "healthy": "Metrics look stable. Continue rollout with standard monitoring.",
        "concerning": "Metrics show degradation. Recommend pause and investigation.",
        "critical": "Metrics in critical state. Immediate rollback or hotfix required.",
    }
    return mapping.get(health, "Insufficient data to make recommendation.")
