# 🎓 All-in-One Campus Assistant

An enterprise multi-agent intent router and domain orchestration system built with **Google Gemini (`gemini-2.5-flash`)**, **Python**, and **Streamlit**.

---

## 🚀 Overview
Navigating university administrative services often forces students and staff to jump across fragmented portals for IT, Fees, HR, and Maintenance. The **Campus Assistant** serves as a unified, intelligent "Front Door" that automatically:
- Classifies user intent into structured JSON using `gemini-2.5-flash`.
- Routes requests to grounded domain policy agents (`.md` files) with section-level citations.
- Handles multi-topic queries by splitting intents across departments.
- Applies confidence thresholds to trigger clarification prompts or human escalation.

---

## ✨ Features & Architecture
- **Intent Router (`router/classifier.py`)**: Uses Gemini JSON mode (`temperature=0.0`) to generate confidence scores, predicted domains, and clarification flags.
- **Orchestrator (`router/orchestrator.py`)**:
  - **High Confidence ($\ge 0.65$)**: Fetches answer from grounded knowledge base (`domain_skills/`).
  - **Moderate Confidence ($0.40 - 0.65$)**: Triggers targeted clarification.
  - **Low Confidence ($< 0.40$)**: Escalates to human support (`support@campus.edu`).
- **Grounded Domain Skills**: Dedicated markdown policy files (`it_skill.md`, `fees_skill.md`, `hr_skill.md`, `facilities_skill.md`) to prevent hallucinations.
- **Evaluation Benchmark (`eval/evaluate_routing.py`)**: Automated test suite measuring routing accuracy across single-topic, multi-topic, ambiguous, and out-of-bounds cases.

---

## 🛠️ Project Structure
```text
campus-assistant/
├── app.py                      # Streamlit Web UI
├── requirements.txt            # Python Dependencies
├── .gitignore                  # Excluded files (.env)
├── router/
│   ├── __init__.py
│   ├── classifier.py           # Gemini Intent Classifier
│   └── orchestrator.py         # Multi-agent Domain Orchestrator
├── domain_skills/              # Grounded Policy Knowledge Bases
│   ├── it_skill.md
│   ├── fees_skill.md
│   ├── hr_skill.md
│   └── facilities_skill.md
└── eval/                       # Benchmark Evaluation Suite
    ├── evaluate_routing.py
    └── evaluate_routing.json
