#!/usr/bin/env python3
"""
Build a comprehensive roots.json from ALL enriched vocab data.

Sources (every word that has an enriched entry with a 'root' field):
  - synonym/antonym stems (Module 1)
  - synonym/antonym options (Module 2)
  - OWS words + OWS options
  - idiom stems + idiom options
  - homonym words + homonym options
  - spelling words + spelling options

This replaces the old roots.json (1,603 families from Satwik only) with a
comprehensive index built from the enriched data we already have.

Output: public/data/roots.json (overwrites the old one)
"""
import json
import os
import sys
from collections import defaultdict


def main():
    enriched_dir = 'public/data/enriched'
    words_json_path = 'public/data/words.json'

    # Load words.json to get frequency counts
    print("Loading words.json for frequency data...", flush=True)
    with open(words_json_path) as f:
        words_data = json.load(f)
    word_freq = {}
    for w in words_data:
        word_freq[w['wordLower']] = {
            'total': w.get('total', 0),
            'asStem': w.get('asStem', 0),
            'asOption': w.get('asOption', 0),
        }

    # Build root -> {words} index from ALL enriched files
    print("Scanning all enriched files for root info...", flush=True)
    roots = defaultdict(lambda: {
        'rm': '',           # root meaning (English)
        'rbn': '',          # root meaning (Bengali)
        'words': [],        # list of word entries
    })
    total_words_with_root = 0
    total_enriched_words = 0

    for letter in 'abcdefghijklmnopqrstuvwxyz':
        path = os.path.join(enriched_dir, f'enriched_{letter}.json')
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        total_enriched_words += len(data)
        for word, e in data.items():
            root = (e.get('root') or '').strip()
            if not root:
                continue
            total_words_with_root += 1
            # Normalize root (uppercase, strip non-alphanumerics)
            root_norm = ''.join(c for c in root.upper() if c.isalnum())
            if not root_norm:
                continue
            entry = roots[root_norm]
            # Take the first non-empty meaning we find
            if not entry['rm'] and e.get('rootMeaning', '').strip():
                entry['rm'] = e['rootMeaning'].strip()
            if not entry['rbn'] and e.get('rootBn', '').strip():
                entry['rbn'] = e['rootBn'].strip()
            # Get frequency from words.json (0 if not in main index — it's an option-only word)
            freq = word_freq.get(word, {'total': 0, 'asStem': 0, 'asOption': 0})
            entry['words'].append({
                'w': word,
                'wLower': word.lower(),
                'pos': e.get('pos', ''),
                'mean': e.get('definition', ''),
                'bn': e.get('bn', ''),
                'mn': e.get('mnemonic', ''),
                'n': freq['total'],
                'nm': freq['asStem'],
                'no': freq['asOption'],
            })

    print(f"Total enriched words scanned: {total_enriched_words}", flush=True)
    print(f"Words with root info: {total_words_with_root}", flush=True)
    print(f"Unique root families: {len(roots)}", flush=True)

    # Filter out roots with no words (shouldn't happen, but safety)
    roots = {k: v for k, v in roots.items() if v['words']}

    # Sort words within each root by frequency (desc), then alphabetical
    for root, entry in roots.items():
        entry['words'].sort(key=lambda w: (-w['n'], w['w']))

    # Convert to list and sort by family size (desc), then root name
    roots_list = []
    for root, entry in roots.items():
        roots_list.append({
            'root': root,
            'rm': entry['rm'] or '(meaning not available)',
            'rbn': entry['rbn'],
            'words': entry['words'],
        })
    roots_list.sort(key=lambda r: (-len(r['words']), r['root']))

    # Count roots missing meanings (candidates for AI enrichment)
    missing_meaning = sum(1 for r in roots_list if r['rm'] == '(meaning not available)')
    print(f"\nRoots missing English meaning: {missing_meaning}", flush=True)
    print(f"Roots with meaning: {len(roots_list) - missing_meaning}", flush=True)

    # Write the new roots.json
    out_path = 'public/data/roots.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(roots_list, f, ensure_ascii=False, separators=(',', ':'))
    print(f"\n✅ Wrote {out_path}: {len(roots_list)} root families", flush=True)
    print(f"   File size: {os.path.getsize(out_path):,} bytes", flush=True)

    # Print top 10 for verification
    print("\n=== Top 10 root families by size ===")
    for r in roots_list[:10]:
        print(f"  {r['root']}: {len(r['words'])} words, meaning={r['rm']!r}")


if __name__ == '__main__':
    main()
