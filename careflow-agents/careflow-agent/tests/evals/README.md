# 🩺 CareFlow Pulse - Clinical Evaluation Suite

This framework provides a comprehensive, automated pipeline for auditing the clinical intelligence and protocol adherence of the CareFlow Pulse Agent.

## 📂 Architecture

The suite is organized into three specialized layers, moving from raw input to final clinical verification:

### 1. 🎙️ Audio Handoff (`evals/audio_handoff/`)

**Objective:** Test the agent's ability to process and analyze raw patient audio directly using Gemini 3's multimodal capabilities.

- **Datasets:** Contains real `.wav` patient recordings.
- **Process:** Injects local audio bytes directly into the agent's execution context.
- **Output:** Generates a detailed report containing the agent's **Thinking Signature** and final clinical assessment.

### 2. 🧩 Logic & Protocol (`evals/logic_evals/`)

**Objective:** Test medical reasoning through text-based scenarios (e.g., Teach-Back failures, red-flag detection).

- **Datasets:** JSON-based scenarios (e.g., `teach_back_scenarios.json`).
- **Process:** Simulates complex nurse-patient dialogues and measures the agent's triage logic.
- **Output:** Detailed Markdown reports mapped to specific Scenario IDs.

### 3. ⚖️ LLM-as-a-Judge (`evals/llm_as_judge/`)

**Objective:** The "Double-Check" layer. A senior auditor model (Gemini 3 Pro) reviews everything.

- **Hybrid Auditing:**
  - **For Audio:** The Judge **listens** to the original audio and verifies if the Agent understood it correctly.
  - **For Logic:** The Judge compares the Agent's report against a defined **Ground Truth** (the clinical standard).
- **Evaluation Criteria:** Clinical Safety, Protocol Adherence, Medical Empathy, and Decision Logic.
- **Output:** Integrated Audit Reports with a final **PASS/FAIL** verdict.

## 🚀 Execution Guide

Always run in this order to ensure the Judge has reports to audit:

```bash
# Level 1: Generate Clinical Reports
uv run tests/evals/logic_evals/eval.py
uv run tests/evals/audio_handoff/eval.py

# Level 2: Run Clinical Audit (Multimodal)
uv run tests/evals/llm_as_judge/eval.py
```

## 🧠 Clinical Feedback Loop

While this environment is a "Cold Test" (no memory persistence to ensure unbiased results), the **verdicts** generated in `llm_as_judge/reports/` are used to refine the Pulse Agent's medical prompts and decision boundaries.

---
*CareFlow Pulse Clinical Validation Framework v3.4*
