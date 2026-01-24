
import matplotlib.pyplot as plt
import pandas as pd
import os

# Create reports directory if it doesn't exist
# We'll use an absolute path to be safe
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(BASE_DIR, "visual_reports")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Data 1: Model Latency (TTFT)
latency_data = {
    'Model': ['Gemini 2.0 Flash', 'Gemini 3.0 Flash', 'Industry Avg (Pro)'],
    'Avg TTFT (ms)': [527, 1550, 1800]
}
df_latency = pd.DataFrame(latency_data)

plt.figure(figsize=(10, 6))
bars = plt.bar(df_latency['Model'], df_latency['Avg TTFT (ms)'], color=['#34A853', '#FBBC05', '#EA4335'])
plt.title('Time to First Token (TTFT) - Voice Optimization', fontsize=14, fontweight='bold')
plt.ylabel('Latency (ms)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add value labels
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 50, f'{yval}ms', ha='center', va='bottom', fontweight='bold')

plt.axhline(y=800, color='r', linestyle='--', label='Empathy Threshold (800ms)')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'model_latency.png'))
plt.close()

# Data 2: Security Latency (Model Armor)
security_data = {
    'Tier': ['No Security', 'Tier 1 (Prompt Scan)', 'Tier 2 (Bidirectional)'],
    'Latency (ms)': [0, 264, 510]
}
df_security = pd.DataFrame(security_data)

plt.figure(figsize=(10, 6))
bars = plt.bar(df_security['Tier'], df_security['Latency (ms)'], color=['#4285F4', '#4285F4', '#4285F4'])
plt.title('Google Model Armor Latency Overhead', fontsize=14, fontweight='bold')
plt.ylabel('Added Latency (ms)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 10, f'{yval}ms', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'security_overhead.png'))
plt.close()

# Data 3: Clinical Intelligence (Reasoning Baseline)
intelligence_data = {
    'Model': ['Gemini 3.0 Pro', 'Gemini 3.0 Flash', 'Gemini 2.0 Flash'],
    'Recall (%)': [98, 85, 82],
    'Precision (%)': [96, 88, 80],
    'Actionability (%)': [99, 82, 78]
}
df_intel = pd.DataFrame(intelligence_data)

ax = df_intel.plot(x='Model', kind='bar', figsize=(12, 7), rot=0, color=['#4285F4', '#EA4335', '#34A853'])
plt.title('Clinical Intelligence Suite - Complex Reasoning Score', fontsize=14, fontweight='bold')
plt.ylabel('Score (%)', fontsize=12)
plt.ylim(0, 110)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend(loc='lower right')

# Add values labels
for p in ax.patches:
    ax.annotate(str(p.get_height()) + '%', (p.get_x() * 1.005, p.get_height() * 1.02), fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'clinical_intelligence.png'))
plt.close()

print(f"✅ Visual reports generated in {output_dir}")
