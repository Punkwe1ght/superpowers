#!/usr/bin/env python3
"""Download a sample from decompile-ghidra-100k for testing."""

from datasets import load_dataset
import json

# Load a small streaming sample
print("Loading dataset (streaming)...")
ds = load_dataset("LLM4Binary/decompile-ghidra-100k", split="train", streaming=True)

# Get first 10 samples
print("Fetching 10 samples...")
samples = []
for i, sample in enumerate(ds):
    if i >= 10:
        break
    samples.append(sample)
    print(f"  Sample {i+1}: {len(sample.get('ghidra_code', ''))} chars")

# Save samples
output_file = "samples.json"
with open(output_file, "w") as f:
    json.dump(samples, f, indent=2)

print(f"\nSaved {len(samples)} samples to {output_file}")

# Show first sample structure
print("\nSample structure:")
for key in samples[0].keys():
    val = samples[0][key]
    if isinstance(val, str):
        print(f"  {key}: {len(val)} chars")
    else:
        print(f"  {key}: {type(val).__name__}")
