"""
MetricsAnalysisTool
-------------------
Analyzes time-series product metrics to detect trends, anomalies,
and percentage changes. Designed as a reusable, testable tool.
"""

from __future__ import annotations

import statistics
from typing import Any

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

TOOL_NAME = "MetricsAnalysisTool"
TOOL_VERSION = "1.0.0"


def run(time_series: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyse a list of daily metric records.

    Parameters
    ----------
    time_series : list[dict]
        Each element must contain a ``date`` key plus one or more
        numeric metric keys (e.g. ``dau``, ``retention_d1``, etc.).

    Returns
    -------
    dict with keys
        - metrics_analysed  : list of metric names processed
        - per_metric        : detailed stats per metric
        - overall_health    : "healthy" | "concerning" | "critical"
        - anomaly_summary   : list of human-readable anomaly strings
    """
    print(f"    [Tool:{TOOL_NAME}] Starting analysis on {len(time_series)} data points...")

    if not time_series:
        raise ValueError("time_series must not be empty")

    # Collect all numeric metric names (excluding the date field)
    metric_keys = [k for k in time_series[0].keys() if k != "date"]

    per_metric: dict[str, Any] = {}
    anomaly_summary: list[str] = []
    health_scores: list[int] = []  # 0 = OK, 1 = concerning, 2 = critical

    for key in metric_keys:
        values = [record[key] for record in time_series if key in record]
        analysis = _analyse_single_metric(key, values)
        per_metric[key] = analysis

        if analysis["anomaly_detected"]:
            anomaly_summary.append(
                f"[{key}] Anomaly: {analysis['anomaly_reason']} "
                f"(trend={analysis['trend']}, Δ={analysis['pct_change']:+.1f}%)"
            )

        # Score the metric health
        health_scores.append(_score_metric(key, analysis))
        print(
            f"    [Tool:{TOOL_NAME}]   {key}: trend={analysis['trend']}, "
            f"pct_change={analysis['pct_change']:+.1f}%, "
            f"anomaly={analysis['anomaly_detected']}"
        )

    # Overall health roll-up
    max_score = max(health_scores) if health_scores else 0
    overall_health = {0: "healthy", 1: "concerning", 2: "critical"}[max_score]

    result = {
        "metrics_analysed": metric_keys,
        "per_metric": per_metric,
        "overall_health": overall_health,
        "anomaly_summary": anomaly_summary,
    }

    print(
        f"    [Tool:{TOOL_NAME}] Analysis complete. "
        f"Overall health: {overall_health}. "
        f"Anomalies found: {len(anomaly_summary)}"
    )
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _analyse_single_metric(name: str, values: list[float]) -> dict[str, Any]:
    """Return trend, pct_change, anomaly flags, and basic stats for one metric."""
    if len(values) < 2:
        return {
            "trend": "insufficient_data",
            "pct_change": 0.0,
            "anomaly_detected": False,
            "anomaly_reason": None,
            "first_value": values[0] if values else None,
            "last_value": values[-1] if values else None,
            "mean": values[0] if values else None,
            "std_dev": 0.0,
        }

    first_val = values[0]
    last_val = values[-1]

    # Trend and percentage change
    if first_val == 0:
        pct_change = 0.0
    else:
        pct_change = ((last_val - first_val) / abs(first_val)) * 100.0

    trend = "increasing" if pct_change > 1 else ("decreasing" if pct_change < -1 else "stable")

    # Basic stats
    mean_val = statistics.mean(values)
    std_dev = statistics.stdev(values) if len(values) > 1 else 0.0

    # Anomaly detection via z-score on last 3 values
    anomaly_detected, anomaly_reason = _detect_anomaly(values, mean_val, std_dev, name)

    return {
        "trend": trend,
        "pct_change": round(pct_change, 2),
        "anomaly_detected": anomaly_detected,
        "anomaly_reason": anomaly_reason,
        "first_value": round(first_val, 4),
        "last_value": round(last_val, 4),
        "mean": round(mean_val, 4),
        "std_dev": round(std_dev, 4),
        "raw_values": values,
    }


def _detect_anomaly(
    values: list[float], mean_val: float, std_dev: float, name: str
) -> tuple[bool, str | None]:
    """
    Flag an anomaly if:
    - The most recent value deviates > 2σ from the historical mean, OR
    - A sudden spike/drop > 30% occurs in consecutive days.
    """
    if std_dev == 0:
        return False, None

    # Z-score check on last data point
    last_z = abs((values[-1] - mean_val) / std_dev)
    if last_z > 2.0:
        direction = "spike" if values[-1] > mean_val else "dip"
        return True, f"z-score {last_z:.2f} ({direction} vs historical mean)"

    # Consecutive-day delta check
    if len(values) >= 2:
        prev, curr = values[-2], values[-1]
        if prev != 0:
            day_delta = abs((curr - prev) / abs(prev)) * 100
            if day_delta > 30:
                direction = "jump" if curr > prev else "drop"
                return True, f"single-day {direction} of {day_delta:.1f}%"

    return False, None


def _score_metric(name: str, analysis: dict[str, Any]) -> int:
    """
    Heuristic health scoring (0=OK, 1=concerning, 2=critical).
    Metrics where *lower is better* (crash_rate, latency, support_tickets)
    are inverted.
    """
    lower_is_better = {"crash_rate", "latency", "support_tickets"}
    trend = analysis["trend"]
    pct = analysis["pct_change"]
    anomaly = analysis["anomaly_detected"]

    bad_trend = (name in lower_is_better and trend == "increasing") or (
        name not in lower_is_better and trend == "decreasing"
    )
    bad_pct = (name in lower_is_better and pct > 20) or (
        name not in lower_is_better and pct < -20
    )

    if anomaly and bad_trend:
        return 2  # critical
    if bad_trend or bad_pct or anomaly:
        return 1  # concerning
    return 0  # OK
