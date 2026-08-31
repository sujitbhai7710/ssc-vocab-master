#!/usr/bin/env python3
"""
Apply carefully-curated root corrections to roots.json.

The AI's second pass flagged 45 words for removal, but its own etymology
explanations showed ~20 of those were actually CORRECT mappings (the AI was
too literal — it didn't recognize that roots have spelling variants like
caput→CAP, caedere→CID, planus→PLAN, potio→POT, salsa→SAL).

This script applies ONLY the removals where the etymology clearly confirms
the word does NOT derive from the assigned root:
  - Words of Old English/Germanic origin (name, star, renew, withdraw, etc.)
  - Clear typos / non-words (inflamous, condencing)
  - Words from a definitively different root (aficionado→FID, impair→PAR,
    ambassador→AMBI, violence→VIS-see, attacking→TACT, etc.)
"""
import json
import os
import sys


# Manually curated: only remove words where etymology CLEARLY shows no connection.
# (Reviewed against the AI's etymology explanations — removed the AI's false positives
# like maintain/decisive/plain/poison/sauce/kennel/inculcate/etc. where the AI's own
# etymology confirmed the word DOES derive from the root.)
CONFIRMED_REMOVALS = {
    # Old English / Germanic origin — cannot be from Latin/Greek roots
    ('NOM', 'name'): 'Old English nama, Germanic',
    ('ASTR', 'star'): 'Old English steorra, Germanic',
    ('NOV', 'renew'): 'Old English niwe, Germanic',
    ('TRA', 'withdraw'): 'Old English',
    ('CORP', 'embody'): 'Old English body',
    ('MENT', 'unmindful'): 'Old English mynd',
    ('MENT', 'minded'): 'Old English gemynd',
    ('MEMOR', 'reminder'): 'Old English gemynd (mind), not Latin memor',
    ('GRAT', 'regrettable'): 'Old French regreter, Germanic origin',

    # Clear typos / non-words
    ('FAM', 'inflamous'): 'not a real word (typo of infamous)',
    ('DENS', 'condencing'): 'unclear typo',

    # Definitively different root (etymology confirms different origin)
    ('FID', 'aficionado'): 'Spanish afición, not Latin fidere (trust)',
    ('PAR', 'impair'): 'from Late Latin pejor (worse), not parare',
    ('AMBI', 'ambassador'): 'from ambactus, not ambi (both)',
    ('VIS', 'violence'): 'from vis (force), not videre (see) — different VIS root',
    ('VIT', 'vicious'): 'from vitium (vice/fault), not vita (life) — different VIT root',
    ('TACT', 'attacking'): 'from Italian attaccare, not Latin tangere (touch)',
    ('ACUT', 'accentuate'): 'from accentus (ad+canere sing), not acutus (sharp)',
    ('DULC', 'indulgent'): 'from indulgere, not dulcis (sweet)',
    ('PROB', 'improve'): 'from Old French emprower (profit), not probus (good)',
    ('PROB', 'improved'): 'same as improve',
}


def main():
    with open('public/data/roots.json') as f:
        roots = json.load(f)

    print(f"Loaded {len(roots)} root families, {sum(len(r['words']) for r in roots)} total word mappings")

    removed_count = 0
    removed_details = []

    for fam in roots:
        root = fam['root']
        original_len = len(fam['words'])
        kept_words = []
        for w in fam['words']:
            word_lower = w['w'].lower()
            if (root, word_lower) in CONFIRMED_REMOVALS:
                removed_count += 1
                removed_details.append({
                    'root': root,
                    'word': w['w'],
                    'reason': CONFIRMED_REMOVALS[(root, word_lower)],
                })
            else:
                kept_words.append(w)
        fam['words'] = kept_words

    # Remove any root families that are now empty
    before = len(roots)
    roots = [r for r in roots if len(r['words']) > 0]
    empty_removed = before - len(roots)

    print(f"\n=== Corrections applied ===")
    print(f"Words removed: {removed_count}")
    print(f"Empty root families removed: {empty_removed}")
    print(f"Final root families: {len(roots)}")
    print(f"Final word mappings: {sum(len(r['words']) for r in roots)}")

    print(f"\n=== Removed words (with reasons) ===")
    for r in removed_details:
        print(f"  {r['root']:8s} <- {r['word']:20s} ({r['reason']})")

    # Write the corrected roots.json
    with open('public/data/roots.json', 'w', encoding='utf-8') as f:
        json.dump(roots, f, ensure_ascii=False, separators=(',', ':'))
    print(f"\n✅ Wrote corrected public/data/roots.json")
    print(f"   File size: {os.path.getsize('public/data/roots.json'):,} bytes")


if __name__ == '__main__':
    main()
