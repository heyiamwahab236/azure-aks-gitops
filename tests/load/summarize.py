"""Summarize JMeter CSV; non-zero exit when requests fail or p95 exceeds one second."""
import csv
import json
import sys

rows = list(csv.DictReader(open(sys.argv[1], newline='', encoding='utf-8-sig')))
if not rows:
    raise SystemExit('No samples')
groups = {}
for row in rows:
    groups.setdefault(row['label'], []).append(row)
results = {}
for name, samples in groups.items():
    elapsed = sorted(int(row['elapsed']) for row in samples)
    errors = sum(row['success'].lower() != 'true' for row in samples)
    results[name] = {'samples':len(samples),'errors':errors,'p50_ms':elapsed[len(elapsed)//2], 'p95_ms':elapsed[min(len(elapsed)-1,int(len(elapsed)*0.95))], 'max_ms':max(elapsed)}
print(json.dumps(results,indent=2))
if any(row['errors'] or row['p95_ms'] > 1000 for row in results.values()):
    raise SystemExit(1)
