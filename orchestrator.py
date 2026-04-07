"""
Orchestrator
------------
Central controller for the AI War Room Decision System.

Responsibilities:
  1. Load and validate all input data
  2. Sequence agent execution with structured logging
  3. Aggregate agent outputs into a single final decision payload
  4. Persist the JSON decision report to disk

This module is intentionally free of business logic — all analysis
and reasoning is delegated to the individual agents.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Agent imports
# ---------------------------------------------------------------------------
from agents import data_analyst_agent
from agents import marketing_agent
from agents import product_manager_agent
from agents import critic_agent
from agents import evaluator_agent

ORCHESTRATOR = "Orchestrator"
_OUTPUT_FILE = Path("output") / "war_room_decision.json"


# ===========================================================================
# Public API
# ===========================================================================

def run(
    metrics_path: str | Path = "data/metrics.json",
    feedback_path: str | Path = "data/feedback.txt",
    release_notes_path: str | Path = "data/release_notes.txt",
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Execute the full war-room workflow and return the structured decision.

    Parameters
    ----------
    metrics_path        : path to the time-series JSON file
    feedback_path       : path to the plaintext user-feedback file
    release_notes_path  : path to the release notes file
    output_path         : override output path (default: output/war_room_decision.json)

    Returns
    -------
    dict : final decision payload (also written to output_path as JSON)
    """
    out_path = Path(output_path) if output_path else _OUTPUT_FILE

    _banner("AI WAR ROOM — DECISION SYSTEM v1.0.0")
    _log("Loading inputs...")

    # ------------------------------------------------------------------
    # Step 1: Load inputs
    # ------------------------------------------------------------------
    time_series = _load_json(metrics_path)
    feedback_entries = _load_feedback(feedback_path)
    release_notes = _load_text(release_notes_path)

    _log(
        f"Inputs loaded — "
        f"metrics: {len(time_series)} days, "
        f"feedback: {len(feedback_entries)} entries, "
        f"release notes: {len(release_notes.splitlines())} lines"
    )
    _separator()

    # ------------------------------------------------------------------
    # Step 2: DataAnalystAgent
    # ------------------------------------------------------------------
    _log("Dispatching DataAnalystAgent...")
    metrics_report = data_analyst_agent.run(time_series)
    _log(
        f"DataAnalystAgent complete — "
        f"health={metrics_report['overall_health']}, "
        f"findings={len(metrics_report['key_findings'])}"
    )
    _separator()

    # ------------------------------------------------------------------
    # Step 3: MarketingAgent
    # ------------------------------------------------------------------
    _log("Dispatching MarketingAgent...")
    sentiment_report = marketing_agent.run(feedback_entries)
    _log(
        f"MarketingAgent complete — "
        f"perception={sentiment_report['perception_status']}, "
        f"neg_ratio={sentiment_report['sentiment']['negative_ratio']:.0%}"
    )
    _separator()

    # ------------------------------------------------------------------
    # Step 4: ProductManagerAgent
    # ------------------------------------------------------------------
    _log("Dispatching ProductManagerAgent...")
    pm_report = product_manager_agent.run(metrics_report, sentiment_report, release_notes)
    _log(
        f"ProductManagerAgent complete — "
        f"proposed_decision={pm_report['proposed_decision']}, "
        f"criteria_passed={pm_report['criteria_passed']}/{pm_report['criteria_total']}"
    )
    _separator()

    # ------------------------------------------------------------------
    # Step 5: CriticAgent
    # ------------------------------------------------------------------
    _log("Dispatching CriticAgent...")
    critic_report = critic_agent.run(
        metrics_report, sentiment_report, pm_report, release_notes
    )
    _log(
        f"CriticAgent complete — "
        f"risks={critic_report['risk_count']}, "
        f"critical={len(critic_report['critical_risks'])}, "
        f"overall_risk={critic_report['overall_risk_level']}"
    )
    _separator()

    # ------------------------------------------------------------------
    # Step 6: EvaluatorAgent
    # ------------------------------------------------------------------
    _log("Dispatching EvaluatorAgent...")
    eval_report = evaluator_agent.run(
        metrics_report, sentiment_report, pm_report, critic_report
    )
    _log(
        f"EvaluatorAgent complete — "
        f"final_decision={eval_report['final_decision']}, "
        f"confidence={eval_report['confidence_score']:.2f} "
        f"({eval_report['confidence_label']})"
    )
    _separator()

    # ------------------------------------------------------------------
    # Step 7: Compile final output
    # ------------------------------------------------------------------
    _log("Compiling final war-room decision report...")
    decision_payload = _compile_output(
        eval_report, metrics_report, sentiment_report, pm_report, critic_report
    )

    # ------------------------------------------------------------------
    # Step 8: Persist to disk
    # ------------------------------------------------------------------
    _persist_output(decision_payload, out_path)
    _log(f"Decision report written to: {out_path.resolve()}")

    _banner(f"FINAL DECISION: {decision_payload['decision']}")
    _log(f"Confidence Score : {decision_payload['confidence_score']}")
    _log(f"Risk Level       : {critic_report['overall_risk_level']}")
    _log(f"Output File      : {out_path.resolve()}")
    _separator()

    return decision_payload


# ===========================================================================
# Private helpers — data loading
# ===========================================================================

def _load_json(path: str | Path) -> Any:
    """Load and parse a JSON file; fail loudly on missing or invalid data."""
    p = Path(path)
    _log(f"  Reading JSON: {p}")
    if not p.exists():
        _fatal(f"File not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            _fatal(f"Invalid JSON in {p}: {exc}")


def _load_feedback(path: str | Path) -> list[str]:
    """Read feedback file and return a list of non-empty lines."""
    p = Path(path)
    _log(f"  Reading feedback: {p}")
    if not p.exists():
        _fatal(f"File not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def _load_text(path: str | Path) -> str:
    """Read a plaintext file."""
    p = Path(path)
    _log(f"  Reading text: {p}")
    if not p.exists():
        _fatal(f"File not found: {p}")
    return p.read_text(encoding="utf-8")


# ===========================================================================
# Private helpers — output compilation
# ===========================================================================

def _compile_output(
    eval_report: dict,
    metrics_report: dict,
    sentiment_report: dict,
    pm_report: dict,
    critic_report: dict,
) -> dict[str, Any]:
    """
    Assemble the mandatory structured JSON output plus extended metadata.
    """
    # Core fields (as specified in requirements)
    output: dict[str, Any] = {
        "decision": eval_report["final_decision"],
        "rationale": eval_report["decision_rationale"],
        "risk_register": [
            {
                "risk": r["risk"],
                "severity": r["severity"],
                "category": r["category"],
                "mitigation": r["mitigation"],
            }
            for r in critic_report["risk_register"]
        ],
        "action_plan": [
            {
                "action": item["action"],
                "owner": item["owner"],
                "priority": item["priority"],
            }
            for item in critic_report["action_plan"]
        ],
        "communication_plan": eval_report["communication_plan"],
        "confidence_score": eval_report["confidence_score"],
        "llm_reasoning": pm_report.get("llm_reasoning"),
        "llm_critique": critic_report.get("llm_critique"),
    }

    # Extended metadata for traceability
    output["_metadata"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": "AI War Room Decision System v1.0.0",
        "agents_involved": [
            "DataAnalystAgent",
            "MarketingAgent",
            "ProductManagerAgent",
            "CriticAgent",
            "EvaluatorAgent",
        ],
        "confidence_label": eval_report["confidence_label"],
        "overall_metric_health": metrics_report["overall_health"],
        "overall_risk_level": critic_report["overall_risk_level"],
        "anomalies_detected": metrics_report["anomaly_summary"],
        "criteria_passed": f"{pm_report['criteria_passed']}/{pm_report['criteria_total']}",
        "sentiment_label": sentiment_report["sentiment"]["label"],
        "negative_ratio": sentiment_report["sentiment"]["negative_ratio"],
        "pm_proposed_decision": pm_report["proposed_decision"],
        "critic_challenges": critic_report["challenges_to_pm"],
        "missing_evidence": critic_report["missing_evidence"],
        "confidence_breakdown": eval_report["confidence_breakdown"],
    }

    return output


def _persist_output(payload: dict, path: Path) -> None:
    """Write the decision payload as indented JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


# ===========================================================================
# Private helpers — console logging
# ===========================================================================

def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ORCHESTRATOR}] [{ts}] {msg}")


def _separator() -> None:
    print(f"[{ORCHESTRATOR}] " + "─" * 60)


def _banner(title: str) -> None:
    width = 64
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def _fatal(msg: str) -> None:
    print(f"[{ORCHESTRATOR}] [FATAL] {msg}", file=sys.stderr)
    sys.exit(1)
