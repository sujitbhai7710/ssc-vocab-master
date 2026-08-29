#!/usr/bin/env python3
"""
Audit roots.json — find words that don't share a recognizable substring with
their assigned root. These are 'suspicious' — could be a legitimate etymology
(e.g. 'elegant' in LEG from Latin 'eligere') OR a data error (word wrongly
assigned to a root).

Output: /tmp/root_audit.json with suspicious entries for AI verification.
"""
import json
import re
from collections import defaultdict


def main():
    with open('public/data/roots.json') as f:
        roots = json.load(f)

    print(f"Total root families: {len(roots)}")
    total_words = sum(len(r['words']) for r in roots)
    print(f"Total word mappings: {total_words}")

    suspicious = []  # list of {root, rm, word, mean}
    clean = 0

    for fam in roots:
        root = fam['root']
        rm = fam['rm']
        root_lower = root.lower()
        # Also try common etymology transformations: drop vowels, etc.
        # A word "belongs" to a root if the root (3+ letters) appears as a substring,
        # OR if a recognizable consonant cluster matches.
        for w in fam['words']:
            word = w['w'].lower()
            # Direct substring check (most reliable)
            if root_lower in word:
                clean += 1
                continue
            # For short roots (2 chars), require substring match (too noisy otherwise)
            if len(root_lower) <= 2:
                suspicious.append({
                    'root': root, 'rm': rm, 'word': w['w'],
                    'mean': w.get('mean', '')[:80], 'bn': w.get('bn', ''),
                    'reason': 'short_root_no_substring'
                })
                continue
            # For 3+ char roots, check if the root's letters appear in order
            # (handles cases like 'leg' in 'elegant' via 'l-e-g')
            # But this is too permissive. Let's just flag non-substring matches.
            suspicious.append({
                'root': root, 'rm': rm, 'word': w['w'],
                'mean': w.get('mean', '')[:80], 'bn': w.get('bn', ''),
                'reason': 'no_substring_match'
            })

    print(f"\nClean (root appears as substring): {clean}")
    print(f"Suspicious (no substring match): {len(suspicious)}")

    # Group suspicious by root for batch AI verification
    by_root = defaultdict(list)
    for s in suspicious:
        by_root[s['root']].append(s)

    print(f"Suspicious roots: {len(by_root)}")
    print(f"\n=== Top 15 suspicious roots (by count) ===")
    top = sorted(by_root.items(), key=lambda x: len(x[1]), reverse=True)[:15]
    for root, entries in top:
        print(f"\n  {root} ({entries[0]['rm']!r}) — {len(entries)} suspicious words:")
        for e in entries[:5]:
            print(f"    - {e['word']!r}: {e['mean']!r}")

    # Save for AI verification
    out = {
        'total_families': len(roots),
        'total_words': total_words,
        'clean': clean,
        'suspicious_count': len(suspicious),
        'suspicious_by_root': {
            root: [{'word': e['word'], 'mean': e['mean'], 'bn': e['bn']} for e in entries]
            for root, entries in by_root.items()
        }
    }
    with open('/tmp/root_audit.json', 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Wrote /tmp/root_audit.json ({len(by_root)} roots to verify)")


if __name__ == '__main__':
    main()
