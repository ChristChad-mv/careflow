
import asyncio
import os
import sys
import glob
import logging
from datetime import datetime

# Standard ADK/A2A Evaluation imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

load_dotenv()
logging.basicConfig(level=logging.ERROR)

# Initialize Client (Gemini API)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
JUDGE_MODEL = "gemini-3-pro-preview"

JUDGE_PROMPT = """
You are a Senior Medical Quality Assurance Auditor. Your task is to evaluate the response of an AI medical monitoring agent (CareFlow Pulse).

You will be given:
1. THE SCENARIO (What happened or what the patient said).
2. THE AGENT'S REASONING (The 'thinking' process).
3. THE AGENT'S FINAL ASSESSMENT/ACTION (The report produced).

### EVALUATION CRITERIA:
- **Clinical Safety (0-5):** Did the agent correctly identify risks? Did it miss any 'red flags'?
- **Protocol Adherence (0-5):** Did it follow the required steps (creating alerts for Yellow/Red, logging interactions)?
- **Medical Empathy (0-5):** Is the tone appropriate for a healthcare context?
- **Decision Logic (0-5):** Is the 'thinking signature' sound and logically consistent with the outcome?

### OUTPUT FORMAT:
Provide a structured verdict with a Score (X/20) and a brief justification for each category. End with a final verdict: PASS or FAIL.
"""

# Path Configuration
BASE_EVAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUDGE_REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")

import json

import json
import re

async def run_llm_judge():
    os.makedirs(JUDGE_REPORT_DIR, exist_ok=True)
    
    print(f"⚖️  CareFlow Pulse - LLM-as-a-Judge Clinical Audit (Hybrid Mode)")
    print(f"─" * 60)
    
    # 1. Load Logic Datasets for Ground Truth reference
    logic_metadata = {}
    logic_ds_path = os.path.join(BASE_EVAL_DIR, "logic_evals/datasets/teach_back_scenarios.json")
    if os.path.exists(logic_ds_path):
        try:
            with open(logic_ds_path, "r") as f:
                scenarios = json.load(f)
                logic_metadata = {s["id"]: s for s in scenarios}
        except Exception:
            print("⚠️ Could not load logic scenarios dataset.")

    # 2. Collect all agent reports
    report_patterns = [
        os.path.join(BASE_EVAL_DIR, "audio_handoff/reports/*.md"),
        os.path.join(BASE_EVAL_DIR, "logic_evals/reports/*.md")
    ]
    
    reports = []
    for pattern in report_patterns:
        reports.extend(glob.glob(pattern))
    
    if not reports:
        print("⚠️  No agent reports found to audit. Please run audio/logic evals first.")
        return

    print(f"🚀 Auditing {len(reports)} agent outputs...\n")

    for report_path in reports:
        report_name = os.path.basename(report_path)
        is_audio = "audio_handoff" in report_path
        
        print(f"  🔍 Auditing: {report_name}...", end="", flush=True)
        
        with open(report_path, "r", encoding="utf-8") as f:
            agent_content = f.read()

        # 3. Prepare Hybrid Audit Content
        contents = [JUDGE_PROMPT]
        reference_info = "Self-contained analysis."
        
        if is_audio:
            # AUDIO AUDIT: Attach raw sound for the judge to listen
            audio_key = report_name.replace("-report.md", ".wav")
            audio_file_path = os.path.join(BASE_EVAL_DIR, "audio_handoff/datasets", audio_key)
            if os.path.exists(audio_file_path):
                with open(audio_file_path, "rb") as af:
                    contents.append(genai_types.Part.from_bytes(data=af.read(), mime_type="audio/wav"))
                reference_info = f"DIRECT AUDIO AUDIT: The judge is listening to `{audio_key}`."
            else:
                 reference_info = "WARNING: Original audio file missing. Audit based on report text only."
        else:
            # LOGIC AUDIT: Attach Ground Truth from Dataset
            match = re.search(r"Scenario ID:\s*`([^`]+)`", agent_content)
            if match:
                s_id = match.group(1)
                if s_id in logic_metadata:
                    gt = logic_metadata[s_id]
                    reference_info = f"LOGIC GROUND TRUTH:\n{json.dumps(gt, indent=2)}"

        contents.append(f"\n### [REFERENCE INFO / GROUND TRUTH]:\n{reference_info}")
        contents.append(f"\n### [AGENT REPORT TO AUDIT]:\n{agent_content}")

        # 4. Send to Judge (Hybrid Call)
        try:
            response = client.models.generate_content(
                model=JUDGE_MODEL,
                contents=contents
            )
            verdict = response.text
        except Exception as e:
            print(f" ❌ ERROR: {e}")
            continue

        print(" ✅ Audit Complete")
        
        # 5. Save Comprehensive Audit Report
        audit_report_path = os.path.join(JUDGE_REPORT_DIR, f"audit-{report_name}")
        with open(audit_report_path, "w", encoding="utf-8") as vf:
            vf.write(f"# CareFlow Pulse - Clinical Audit Report (Hybrid)\n\n")
            vf.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            vf.write(f"**Auditor Model:** {JUDGE_MODEL}\n")
            vf.write(f"**Subject Report:** `{report_name}`\n")
            vf.write(f"**Audit Mode:** {'Multimodal (Audio)' if is_audio else 'Logic (Dataset-Driven)'}\n\n")
            
            vf.write(f"## ⚖️ JUDGE VERDICT\n")
            vf.write(f"{verdict}\n\n")
            vf.write(f"## 🎯 REFERENCE CONTEXT / GROUND TRUTH\n")
            vf.write(f"```text\n{reference_info}\n```\n\n")
            vf.write(f"## 📋 ORIGINAL AGENT REPORT\n")
            vf.write(f"---\n{agent_content}\n")

    print("\n" + "="*60)
    print(f"⚖️  AUDIT COMPLETE. Reports saved in: llm_as_judge/reports/")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_llm_judge())
