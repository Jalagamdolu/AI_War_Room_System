"""
main.py — AI War Room Decision System
--------------------------------------
CLI entry point. Accepts optional overrides for data file paths
and output location via command-line arguments.

Usage:
    python main.py
    python main.py --metrics data/metrics.json --feedback data/feedback.txt
    python main.py --output reports/my_run.json
    python main.py --help
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv

import orchestrator


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ai-war-room",
        description=(
            "AI War Room Decision System — Multi-Agent Product Launch Evaluator\n"
            "Analyses metrics, user feedback, and release notes to produce a\n"
            "structured decision: Proceed / Pause / Roll Back."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("data/metrics.json"),
        help="Path to the time-series metrics JSON file (default: data/metrics.json)",
    )
    parser.add_argument(
        "--feedback",
        type=Path,
        default=Path("data/feedback.txt"),
        help="Path to the user feedback text file (default: data/feedback.txt)",
    )
    parser.add_argument(
        "--notes",
        type=Path,
        default=Path("data/release_notes.txt"),
        help="Path to the release notes file (default: data/release_notes.txt)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/war_room_decision.json"),
        help="Path to write the JSON decision report (default: output/war_room_decision.json)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    load_dotenv()
    args = _parse_args()

    # Validate inputs exist before handing off to orchestrator
    for label, path in [
        ("metrics", args.metrics),
        ("feedback", args.feedback),
        ("release notes", args.notes),
    ]:
        if not path.exists():
            print(
                f"[ERROR] {label} file not found: {path}\n"
                "       Run from the project root directory or supply --{label} <path>",
                file=sys.stderr,
            )
            return 1

    try:
        result = orchestrator.run(
            metrics_path=args.metrics,
            feedback_path=args.feedback,
            release_notes_path=args.notes,
            output_path=args.output,
        )
        print(f"\n✅  War room complete. Decision: {result['decision']}")
        print(f"    Confidence : {result['confidence_score']:.2f}")
        print(f"    Report     : {args.output.resolve()}\n")
        return 0

    except KeyboardInterrupt:
        print("\n[main] Session interrupted by user.", file=sys.stderr)
        return 130

    except Exception:
        print("\n[main] Unexpected error during war-room execution:", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
