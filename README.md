# 🚀 AI War Room Decision System

## 📌 Overview

The **AI War Room Decision System** is a production-quality multi-agent AI system designed to simulate real-world cross-functional decision-making during a product launch.

It analyzes:

* 📊 Time-series product metrics
* 💬 User feedback sentiment
* 📄 Release notes

And produces a structured decision:
👉 **Proceed / Pause / Roll Back**

---

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
│   ├── data_analyst_agent.py
│   ├── marketing_agent.py
│   ├── product_manager_agent.py
│   ├── critic_agent.py
│   └── evaluator_agent.py
│
├── tools/
│   ├── __init__.py
│   ├── metrics_tool.py
│   └── sentiment_tool.py
│
├── data/
│   ├── metrics.json
│   ├── feedback.txt
│   └── release_notes.txt
│
├── output/
│   └── war_room_decision.json
│
├── orchestrator.py
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🤖 Agent Responsibilities

| Agent                   | Role                                                               | Tool Used             |
| ----------------------- | ------------------------------------------------------------------ | --------------------- |
| **DataAnalystAgent**    | Analyses time-series KPIs for trends, anomalies, and % changes     | MetricsAnalysisTool   |
| **MarketingAgent**      | Classifies user sentiment, surfaces recurring issues               | SentimentAnalysisTool |
| **ProductManagerAgent** | Evaluates success criteria, proposes initial decision              | —                     |
| **CriticAgent**         | Challenges assumptions, builds risk register & action plan         | —                     |
| **EvaluatorAgent**      | Generates final decision, confidence score, and communication plan | —                     |
| **Orchestrator**        | Controls workflow, integrates outputs, writes final JSON           | —                     |

---

## 🛠️ Tools

### MetricsAnalysisTool

* Trend detection (increasing/decreasing/stable)
* Percentage change calculation
* Z-score anomaly detection
* Overall KPI health evaluation

### SentimentAnalysisTool

* Keyword-based sentiment classification
* Positive/negative ratio
* Issue clustering and severity detection

---

## ⚙️ Setup

### Prerequisites

* Python 3.10+

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Run

```bash
python main.py
```

Optional:

```bash
python main.py --metrics data/metrics.json --feedback data/feedback.txt --notes data/release_notes.txt
```

---

## 📤 Output

Generated file:

```
output/war_room_decision.json
```

### Example Output

```json
{
  "decision": "Roll Back",
  "rationale": [
    "Metric health assessed as critical",
    "User sentiment is 57% negative",
    "Multiple critical risks identified"
  ],
  "risk_register": [...],
  "action_plan": [...],
  "communication_plan": [...],
  "confidence_score": 0.23
}
```

---

## 🔄 Workflow

```
Orchestrator
   ↓
DataAnalystAgent → MetricsAnalysisTool
   ↓
MarketingAgent → SentimentAnalysisTool
   ↓
ProductManagerAgent
   ↓
CriticAgent
   ↓
EvaluatorAgent
   ↓
Final JSON Output
```

---

## 🧾 Traceability

Example logs:

```
[Orchestrator] Loading inputs...
[DataAnalystAgent] Running metrics analysis...
[MarketingAgent] Running sentiment analysis...
[ProductManagerAgent] Evaluating decision...
[CriticAgent] Identifying risks...
[EvaluatorAgent] Calculating confidence score...
```

---

## 📋 Decision Logic Summary

| Condition            | Decision  |
| -------------------- | --------- |
| ≥3 critical failures | Roll Back |
| ≥2 failures          | Pause     |
| ≤1 failure           | Proceed   |
| Low confidence       | Escalate  |

---

## 🔌 Extending the System

* Add new agents in `/agents`
* Add new tools in `/tools`
* Integrate LLM using `.env`

---

## 👨‍💻 Author

**Jalagam Dolender**

---

## 📌 Summary

This project demonstrates how **multi-agent AI + tool-based reasoning** can simulate high-stakes product decisions in real-world systems.
