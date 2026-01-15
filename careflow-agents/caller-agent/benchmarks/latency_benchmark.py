
import asyncio
import time
import os
import json
import statistics
from typing import List, Dict
import google.genai.types as genai_types
from google.genai import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
models_to_test = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash"
] 

PROMPT = "You are a helpful medical assistant. A patient asks: 'I have a headache and I took 2 aspirin but it still hurts. Should I take more?' Provide a concise, safe response."

ITERATIONS = 5

async def benchmark_model(model_name: str, client: Client) -> Dict:
    print(f"\n--- Benchmarking {model_name} ---")
    ttft_times = []
    total_times = []
    
    for i in range(ITERATIONS):
        start_time = time.time()
        first_token_time = None
        
        try:
            # Using streaming to measure Time to First Token (TTFT)
            # Note: client.models.generate_content_stream signature might differ slightly depending on SDK version
            # For google-genai SDK 0.3+:
            response = client.models.generate_content_stream(
                model=model_name,
                contents=PROMPT,
                config=genai_types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=150
                )
            )
            
            chunk_count = 0
            # Iterate to trigger the stream
            for chunk in response:
                if chunk_count == 0:
                    first_token_time = time.time()
                chunk_count += 1
                
            end_time = time.time()
            
            if first_token_time:
                ttft = (first_token_time - start_time) * 1000 # ms
                total = (end_time - start_time) * 1000 # ms
                ttft_times.append(ttft)
                total_times.append(total)
                print(f"  Run {i+1}: TTFT={ttft:.2f}ms, Total={total:.2f}ms")
            else:
                print(f"  Run {i+1}: Failed to stream or empty response.")

        except Exception as e:
            print(f"  Run {i+1}: Error - {e}")
            time.sleep(1) # Backoff slightly
            
    if not ttft_times:
        return {"model": model_name, "error": "All runs failed"}

    return {
        "model": model_name,
        "avg_ttft_ms": statistics.mean(ttft_times),
        "min_ttft_ms": min(ttft_times),
        "max_ttft_ms": max(ttft_times),
        "avg_total_ms": statistics.mean(total_times),
        "std_dev_ttft": statistics.stdev(ttft_times) if len(ttft_times) > 1 else 0
    }

async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        return

    print(f"✅ Using Google AI Studio API Key (Vertex AI Disabled for this test)")
    
    # Initialize client strictly with API Key
    try:
        client = Client(api_key=api_key)
    except Exception as e:
        print(f"Failed to init client: {e}")
        return

    results = []
    
    # One loop - no regions, just the API
    for model in models_to_test:
        result = await benchmark_model(model, client)
        results.append(result)
        
    # Validation / Report
    print("\n" + "="*80)
    print(f"{'Model':<30} | {'Avg TTFT (ms)':<15} | {'Std Dev':<10}")
    print("-" * 80)
    for res in results:
        if "error" in res:
            print(f"{res['model']:<30} | {'ERROR':<15} | {'-':<10}")
        else:
            print(f"{res['model']:<30} | {res['avg_ttft_ms']:<15.2f} | {res['std_dev_ttft']:<10.2f}")
    print("="*80)
    
    # JSON Export
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())
