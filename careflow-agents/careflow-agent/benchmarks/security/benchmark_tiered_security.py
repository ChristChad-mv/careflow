
import asyncio
import time
import os
import sys
import statistics
import logging

# Ensure we can import from the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from dotenv import load_dotenv

# Load Env
load_dotenv()

# Configure logging to show only critical errors during bench
logging.basicConfig(level=logging.ERROR)

from app.core.security.model_armor import ModelArmorClient

ITERATIONS = 50
TEST_PROMPT = "The patient John Doe (ID: 12345) has a history of hypertension and is taking Lisinopril."
TEST_RESPONSE = "Patient John Doe is stable. BP is 120/80. No adverse reactions to Lisinopril."

async def benchmark_tier_1_prompt_scan(client: ModelArmorClient):
    """Benchmark Prompt Scanning (Edge/Voice Tier)"""
    print("\n🛡️  Tier 1: Prompt Scanning (Input Protection)...")
    latencies = []
    
    for i in range(ITERATIONS):
        start = time.perf_counter()
        result = await client.scan_prompt(TEST_PROMPT)
        end = time.perf_counter()
        
        if result.get("error"):
            print(f"  ⚠️ Run {i} failed: {result['error']}")
            # If API is not configured, we can't benchmark real latency
            if "not initialized" in result['error']: 
                return None
        else:
            latencies.append((end - start) * 1000)
            
    return latencies

async def benchmark_tier_2_response_sanitize(client: ModelArmorClient):
    """Benchmark Response Sanitization (Backend/Pulse Tier)"""
    print("\n🔒 Tier 2: Response Sanitization (PII Redaction)...")
    latencies = []
    
    for i in range(ITERATIONS):
        start = time.perf_counter()
        result = await client.sanitize_response(TEST_RESPONSE)
        end = time.perf_counter()
        
        if result.get("error"):
             # If API is not configured, we can't benchmark real latency
             if "not initialized" in result['error']: 
                return None
        else:
            latencies.append((end - start) * 1000)

    return latencies

def print_stats(name: str, latencies: list):
    if not latencies:
        print(f"  ❌ {name}: No successful runs (Check ModelArmor config)")
        return

    avg = statistics.mean(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18] # 95th prob
    
    print(f"  ✅ {name} Latency:")
    print(f"     Avg: {avg:.2f} ms")
    print(f"     P95: {p95:.2f} ms")
    print(f"     Min: {min(latencies):.2f} ms")
    print(f"     Max: {max(latencies):.2f} ms")

async def main():
    print("🚀 Starting Security Latency Benchmark...")
    print("----------------------------------------")
    
    client = ModelArmorClient()
    
    if not client.client:
        print("❌ ModelArmor Client could not be initialized (Missing credentials or package).")
        print("   Cannot run benchmark.")
        return

    # Tier 1
    t1_results = await benchmark_tier_1_prompt_scan(client)
    print_stats("Prompt Scan (Tier 1)", t1_results)
    
    # Tier 2
    t2_results = await benchmark_tier_2_response_sanitize(client)
    print_stats("Response Sanitize (Tier 2)", t2_results)
    
    # Conclusion
    if t1_results and t2_results:
        t1_avg = statistics.mean(t1_results)
        t2_avg = statistics.mean(t2_results)
        overhead_diff = t2_avg - t1_avg
        print("\n💡 Insight:")
        print(f"   Full Redaction adds ~{overhead_diff:.2f}ms more latency than simple Prompt Scanning.")
        print(f"   Recommendation: Use Tier 1 for Voice Agent (save {overhead_diff:.2f}ms).")

if __name__ == "__main__":
    asyncio.run(main())
