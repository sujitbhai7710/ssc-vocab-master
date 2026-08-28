#!/usr/bin/env python3
"""Split enriched.json into per-letter files to reduce per-fetch size."""

import json
import os
from collections import defaultdict

INPUT = "/home/z/my-project/src/data/enriched.json"
OUT_DIR = "/home/z/my-project/public/data/enriched"

os.makedirs(OUT_DIR, exist_ok=True)

with open(INPUT) as f:
    enriched = json.load(f)

buckets = defaultdict(dict)
for word_lower, entry in enriched.items():
    first_letter = word_lower[0] if word_lower else "_"
    buckets[first_letter][word_lower] = entry

for letter, entries in buckets.items():
    out_path = os.path.join(OUT_DIR, f"enriched_{letter}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)
    print(f"  enriched_{letter}.json  {len(entries):4d} words")

print(f"\nWrote {len(buckets)} letter-bucketed files to {OUT_DIR}")
print(f"Total entries: {sum(len(v) for v in buckets.values())}")
