# AI War Room Decision System

> A production-quality **multi-agent AI system** that simulates a cross-functional war room during a product launch. It analyses time-series metrics, user feedback sentiment, and release notes to produce a structured decision: **Proceed / Pause / Roll Back**.

---

## 🏗️ Architecture Overview

```
main.py  ──►  orchestrator.py
                │
                ├── DataAnalystAgent   ──► MetricsAnalysisTool
                ├── MarketingAgent     ──► SentimentAnalysisTool
                ├── ProductManagerAgent (evaluates success criteria)
                ├── CriticAgent        (adversarial risk review)
                └── EvaluatorAgent     (confidence score + comms plan)
                │
                └──► output/war_room_decision.json
```

The system follows a **strict separation of concerns** — the Orchestrator owns sequencing and I/O, while each agent owns only its domain logic. Tools are independently callable and reusable.

---

## 📂 Project Structure

```
AI_War_Room_System/
│
├── agents/
│   ├── __init__.py
│   ├── data_analyst_agent.py      # Metrics trend & anomaly analysis
│   ├── marketing_agent.py         # User sentiment & perception
│   ├── product_manager_agent.py   # Success criteria evaluation
│   ├── critic_agent.py            # Adversarial risk register
│   └── evaluator_agent.py        # Confidence scoring & comms plan
│
├── tools/
│   ├── __init__.py
│   ├── metrics_tool.py            # Time-series analysis engine
│   └── sentiment_tool.py         # Rule-based sentiment classifier
│
├── data/
│   ├── metrics.json               # 14-day time-series KPIs
│   ├── feedback.txt               # 30 user feedback entries
│   └── release_notes.txt         # v3.2.0 release notes
│
├── output/                        # Auto-created on first run
│   └── war_room_decision.json
│
├── orchestrator.py               # Workflow controller
├── main.py                       # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🤖 Agent Responsibilities

| Agent | Role | Tool Used |
|---|---|---|
| **DataAnalystAgent** | Analyses time-series KPIs for trends, anomalies, and % changes | `MetricsAnalysisTool` |
| **MarketingAgent** | Classifies user sentiment, surfaces recurring issues | `SentimentAnalysisTool` |
| **ProductManagerAgent** | Evaluates pre-defined success criteria, proposes initial decision | — |
| **CriticAgent** | Adversarially challenges assumptions, builds risk register & action plan | — |
| **EvaluatorAgent** | Synthesises all outputs into a confidence-scored final decision + comms plan | — |
| **Orchestrator** | Sequences agents, loads data, aggregates output, writes JSON report | — |

---

## 🛠️ Tools

### `MetricsAnalysisTool`
- **Input**: List of daily metric records (JSON)
- **Output**:
  - `trend` per metric: `increasing` / `decreasing` / `stable`
  - `pct_change`: % change from first to last data point
  - `anomaly_detected`: z-score and consecutive-day spike detection
  - `overall_health`: `healthy` / `concerning` / `critical`

### `SentimentAnalysisTool`
- **Input**: List of user feedback strings
- **Output**:
  - `positive_ratio` / `negative_ratio`
  - `sentiment_label`: `positive` / `negative` / `mixed` / `neutral`
  - `top_issues`: ranked issue clusters with example quotes
  - `keyword_frequency`: top matched signal words

Both tools are **pure Python**, zero external dependencies, and independently testable.

---

## ⚙️ Setup

### Prerequisites
- Python 3.10 or higher

### 1. Clone / Download the project

```bash
git clone <repo-url>
cd AI_War_Room_System
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The core system uses only the Python standard library.
> `python-dotenv` is the only runtime dependency.

### 4. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env if you plan to integrate an LLM API
```

---

## 🚀 Run

```bash
# Default run (uses data/ directory)
python main.py

# Custom paths
python main.py --metrics data/metrics.json --feedback data/feedback.txt --notes data/release_notes.txt

# Custom output location
python main.py --output reports/launch_v3_2_0.json

# Help
python main.py --help
```

---

## 📤 Example Output

```json
{
  "decision": "Roll Back",
  "rationale": [
    "Metric health assessed as 'critical' across 6 tracked KPIs.",
    "User sentiment is 57% negative. Top user issue: 'app crash' (8 mentions).",
    "3 metric anomalies detected.",
    "4 critical risks identified by CriticAgent."
  ],
  "risk_register": [
    {
      "risk": "Crash rate is at 8.8% and still increasing — no recovery signal.",
      "severity": "Critical",
      "category": "Technical Stability",
      "mitigation": "Immediate rollback or targeted force-update with hotfix build."
    }
  ],
  "action_plan": [
    {
      "action": "Immediate rollback or targeted force-update with hotfix build.",
      "owner": "Engineering / SRE",
      "priority": "Critical"
    }
  ],
  "communication_plan": [
    "[Internal] Immediately notify Engineering, Product, and Executive leadership of rollback.",
    "[Customer] Publish status page incident: 'We are aware of issues affecting v3.2.0 and are rolling back.'"
  ],
  "confidence_score": 0.183
}
```

---

## 🔄 Workflow

```
[Orchestrator] Load inputs (metrics, feedback, release notes)
      │
      ▼
[DataAnalystAgent]  ──calls──►  MetricsAnalysisTool
      │                         → trend, anomalies, health score
      ▼
[MarketingAgent]    ──calls──►  SentimentAnalysisTool
      │                         → sentiment ratios, issue clusters
      ▼
[ProductManagerAgent]
      │                         → evaluate success criteria
      │                         → propose initial decision
      ▼
[CriticAgent]
      │                         → challenge PM assumptions
      │                         → build risk register + action plan
      ▼
[EvaluatorAgent]
      │                         → calculate confidence score
      │                         → arbitrate final decision
      │                         → generate communication plan
      ▼
[Orchestrator]
                                → compile & persist JSON report
```

---

## 🧾 Traceability

Every agent and tool logs its actions to stdout with structured prefixes:

```
[Orchestrator]        Loading inputs...
[DataAnalystAgent]    Running metrics analysis...
  [Tool:MetricsAnalysisTool]  dau: trend=increasing, pct_change=+27.4%
[MarketingAgent]      Running sentiment analysis...
  [Tool:SentimentAnalysisTool]  Sentiment=negative, neg=57%
[ProductManagerAgent] Evaluating decision against success criteria...
[CriticAgent]         Challenging assumptions and identifying risks...
[EvaluatorAgent]      Calculating confidence score...
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Run a specific tool test
pytest tests/test_metrics_tool.py -v
```

---

## 🔌 Extending the System

- **Add an agent**: Create `agents/my_agent.py` with a `run(**kwargs) -> dict` function, register in `agents/__init__.py`, and add a dispatch step in `orchestrator.py`.
- **Add a tool**: Create `tools/my_tool.py` with a `run(**kwargs) -> dict` function. Call it from the appropriate agent.
- **Integrate an LLM**: Replace rule-based logic in any agent with an API call. Use `.env` for the API key and `python-dotenv` to load it.

---

## 📋 Decision Logic Summary

| Condition | Decision |
|---|---|
| ≥3 critical criteria failures AND crash+sentiment both fail | Roll Back |
| ≥2 criteria failures OR critic finds critical risks | Pause → Roll Back |
| ≤1 failure, no critical risks | Proceed |
| Confidence < 0.30 despite Proceed proposal | Escalated to Pause |

---

## 📄 License

MIT License — see `LICENSE` for details.
