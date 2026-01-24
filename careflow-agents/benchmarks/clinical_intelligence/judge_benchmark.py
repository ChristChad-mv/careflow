
import asyncio
import os
import sys
import glob
import base64
from datetime import datetime
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

load_dotenv()

# Path to the careflow-agent app for imports if needed
CAREFLOW_AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../careflow-agent"))
sys.path.append(CAREFLOW_AGENT_DIR)

# Directories
REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "reports"))
DATASET_DIR = os.path.join(CAREFLOW_AGENT_DIR, "tests/evals/audio_handoff/datasets")
JUDGE_REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "judge_reports"))

# Models
JUDGE_MODEL = "gemini-3-pro-preview"

async def run_judge():
    os.makedirs(JUDGE_REPORT_DIR, exist_ok=True)
    
    print(f"⚖️ CareFlow Pulse - LLM-as-a-Judge Clinical Benchmark")
    print(f"Using {JUDGE_MODEL} to audit and rank model performance")
    print(f"─" * 60)
    
    # 1. Collect all reports
    report_files = glob.glob(os.path.join(REPORT_DIR, "*-report.md"))
    if not report_files:
        print(f"⚠️ No reports found in {REPORT_DIR}. Run benchmark_reasoning.py first.")
        return

    # 2. Group reports by audio file
    # Format: { 'audio-test-1': { 'gemini-3-pro-preview': 'content', 'gpt-4o': 'content' } }
    grouped_reports = {}
    for rf in report_files:
        file_name = os.path.basename(rf)
        # Extract model and audio base name
        # benchmark_reasoning.py saves as: [model_name]-[audio_base]-report.md
        parts = file_name.replace("-report.md", "").split("-")
        # Find where the audio name starts (assuming audio files start with 'audio-')
        audio_index = -1
        for i, p in enumerate(parts):
            if p == "audio":
                audio_index = i
                break
        
        if audio_index != -1:
            model_name = "-".join(parts[:audio_index])
            audio_base = "-".join(parts[audio_index:])
            
            if audio_base not in grouped_reports:
                grouped_reports[audio_base] = {}
            
            with open(rf, "r") as f:
                grouped_reports[audio_base][model_name] = f.read()

    # 3. Initialize Gemini Client for Judging
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    for audio_base, models in grouped_reports.items():
        print(f"\n👨‍⚖️ JUDGING SCENARIO: {audio_base}")
        
        audio_path = os.path.join(DATASET_DIR, f"{audio_base}.wav")
        if not os.path.exists(audio_path):
            print(f"  ⚠️ Audio file not found: {audio_path}")
            continue

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Construct the Judge Prompt
        judge_prompt = (
            "You are a Senior Medical Auditor and Clinical Quality Judge. "
            "Your task is to evaluate several AI agents based on their analysis of a patient interaction audio recording.\n\n"
            "### EVALUATION CRITERIA:\n"
            "1. **Clinical Accuracy:** Did the agent identify critical red flags and medication issues?\n"
            "2. **Adherence to Protocol:** Did the agent correctly suggest using tools for risk updates and alerts?\n"
            "3. **Nuance & Insight:** Did the agent notice subtle verbal cues, hesitations, or confusing statements?\n"
            "4. **Actionability:** Are the recommended clinical steps safe and appropriate?\n\n"
            "### AGENT REPORTS TO EVALUATE:\n"
        )
        
        for model_handle, report_content in models.items():
            judge_prompt += f"\n--- AGENT: {model_handle} ---\n{report_content}\n"

        judge_prompt += (
            "\n### FINAL JUDGMENT INSTRUCTIONS:\n"
            "1. Listen to the provided original audio recording.\n"
            "2. Read each agent's report carefully.\n"
            "3. Rank the agents from best to worst.\n"
            "4. Provide a detailed justification for the winner, highlighting exactly what they caught that others missed.\n"
            "5. Provide a 'FAIL' list for agents that missed life-threatening or high-risk signals.\n"
            "6. Conclude with a recommendation on which model is most suitable for production healthcare use."
        )

        print(f"  ⌛ {JUDGE_MODEL} is auditing the reports...", end="", flush=True)

        try:
            response = client.models.generate_content(
                model=JUDGE_MODEL,
                contents=[
                    genai_types.Part.from_text(text=judge_prompt),
                    genai_types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
                ]
            )
            
            judgment_text = response.text
            print(" ✅")
            
            # Save Judgment Report
            judgment_path = os.path.join(JUDGE_REPORT_DIR, f"{audio_base}-judgment.md")
            with open(judgment_path, "w") as f:
                f.write(f"# CareFlow Pulse - Benchmark Judgment Report\n\n")
                f.write(f"**Scenario:** `{audio_base}`\n")
                f.write(f"**Judge Model:** `{JUDGE_MODEL}`\n")
                f.write(f"**Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n")
                f.write(f"## 🏆 The Verdict\n\n")
                f.write(judgment_text)
            
            print(f"  📄 Judgment saved: judge_reports/{os.path.basename(judgment_path)}")

        except Exception as e:
            print(f" ❌ JUDGE ERROR: {e}")

    print(f"\n" + "="*60)
    print(f"🏁 JUDGING COMPLETE")
    print(f"Results are available in: {JUDGE_REPORT_DIR}")
    print(f"="*60)

if __name__ == "__main__":
    asyncio.run(run_judge())
