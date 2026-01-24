# 📊 CareFlow Agent Performance Benchmarks

This directory contains the definitive performance logs and benchmarking suites for the CareFlow Pulse ecosystem. Our architectural decisions are driven by three distinct benchmark tiers.

---

## 1. 🛡️ Security Latency Benchmark

**Goal:** Measure the overhead of Google Cloud Model Armor for Real-time vs. Async tasks.

* **Tier 1 (Prompt Only):** ~264ms (Used by Caller Agent).
* **Tier 2 (Bidirectional):** ~510ms (Used by Pulse Agent).

---

## 2. ⚡ Model Latency Benchmark

**Goal:** Measure Time To First Token (TTFT) for Voice UX optimization.

| Model | Avg TTFT (ms) | Status |
| :--- | :--- | :--- |
| **gemini-2.0-flash** | **~527 ms** | 🟢 Recommended for Voice |
| **gemini-3.0-flash** | ~1,550 ms | 🔴 Too slow for phone calls |

---

## 3. 🧠 Clinical Intelligence Benchmark (The "Complex Reasoning" Suite)

**Goal:** Prove the superiority of Gemini 3.0 Pro in identifying "Weak Signals" and lethal clinical errors in complex interactions.

* **Protocol:** We simulate a 10-minute "Stress-Test" interaction filled with medication errors, disguised CHF red flags, and logistical barriers.
* **Audit Layer:** We use Gemini 3.0 Pro as a Medical QA Judge to score models on **Recall, Precision, and Actionability**.

---

## 🏃 How to Run the Suites

```bash
# 1. Run Security Benchmarks
python benchmarks/security/benchmark_tiered_security.py

# 2. Run Latency Benchmarks
python benchmarks/latency/latency_benchmark.py

# 3. Run Clinical Reasoning Benchmarks
python benchmarks/clinical_intelligence/benchmark_reasoning.py
```

## 🧠 Final Global Architecture Decision

Based on these three pillars, CareFlow Pulse uses a **Dual-Brain Strategy**:
* **The Voice (Caller Agent):** Powered by `gemini-2.0-flash` (Tier 1 Security) to maintain sub-800ms "Empathy Loops".
* **The Intelligence (Pulse Agent):** Powered by **`gemini-3-pro-preview`** (Tier 2 Security) to ensure zero-fail clinical auditing and complex medical reasoning.
