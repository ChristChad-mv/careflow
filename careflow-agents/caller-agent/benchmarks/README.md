# ⚡ Gemini Model Latency Benchmark for CareFlow Pulse

**Date:** January 14, 2026  
**Context:** Evaluating model selection for the **CareFlow Caller Agent** (Real-time Voice) vs. **CareFlow Pulse Agent** (Medical Reasoning).

Due to the strict latency requirements of real-time voice interactions (TTS + STT overhead), we benchmarked the new Google Gemini 3 and 2.5 series against the current version.

## 📊 Benchmark Results

| Model | Avg TTFT (ms) | Stability (Std Dev) | Suitability for Voice |
| :--- | :--- | :--- | :--- |
| **gemini-2.0-flash** | **~527 ms** | High | 🟢 **Ideal** |
| **gemini-2.5-flash** | ~1,228 ms | Moderate | 🟡 Acceptable (barely) |
| **gemini-3.0-flash** | ~1,550 ms | Moderate | 🔴 Too Slow for Real-time |
| **gemini-3.0-pro** | ~4,200 ms | Low | ❌ Reasoning Only |

*TTFT = Time To First Token (The delay before the agent starts speaking).*

## 🧠 Strategic Trade-offs

### 1. Caller Agent (Voice Interface)

**Goal:** Minimizing "dead air" silence on the phone.

* **Recommendation: `gemini-2.0-flash`**
* **Reasoning:** Voice interactions require sub-800ms response times to feel natural.
  * **Pros:** Usable latency, good enough instruction following for triage.
  * **Cons:** Less "reasoning" capability than v3.
  * **Mitigation:** We offload complex decisions to the Pulse Agent.

* *Why not Gemini 3 Flash?* A 1.5s delay + ElevenLabs TTS generation (~500ms) = **~2 seconds of silence** after every patient sentence. This feels like a broken connection.

### 2. Pulse Agent (Medical Brain)

**Goal:** Accurate clinical reasoning and complex data synthesis.

* **Recommendation: `gemini-3-pro-preview`**
* **Reasoning:** This agent processes data asynchronously (background tasks). Latency is irrelevant; correctness is everything.
  * **Pros:** Massive reasoning bump, better at medical nuance (MedGemma alternative).
  * **Cons:** Slower.
  * **Fit:** perfect for the "Gemini 3 Hackathon" requirement.

## 🏁 Final Architecture Decision

We will adopt a **Hybrid Model Strategy**:

1. **Frontend Brain (Caller):** `gemini-2.0-flash` for speed.
2. **Backend Brain (Pulse):** `gemini-3-pro-preview` for intelligence.

This maximizes both User Experience (speed) and Clinical Accuracy (reasoning).
