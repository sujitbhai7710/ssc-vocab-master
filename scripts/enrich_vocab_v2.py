#!/usr/bin/env python3
"""
Enrich vocabulary entries using:
1. SSC exam data + best-guess correct answer (from ssc_relations.json)
2. NLTK WordNet: definitions, parts of speech, additional synonyms/antonyms
3. Curated root-word + mnemonic database for top high-frequency words

Outputs (per-letter files under src/data/enriched/):
  enriched_<letter>.json

Each entry has:
  word, wordLower, definition, pos,
  ssSynonyms: [{ word, status: 'correct'|'distractor'|'added' }],
  ssAntonyms: [{ word, status: 'correct'|'distractor'|'added' }],
  root: { primary, meaning, family } | null,
  mnemonic: string
"""

import json
import os
import nltk

nltk.data.path.append('/home/z/nltk_data')
from nltk.corpus import wordnet

DATA_DIR = "/home/z/my-project/ssc-vocab-astro/public/data"

with open(os.path.join(DATA_DIR, "words.json")) as f:
    words = json.load(f)
with open(os.path.join(DATA_DIR, "ssc_relations.json")) as f:
    ssc_rel = json.load(f)

# Curated roots database (28 high-frequency words)
ROOTS_DB = {
    "loquacious": ("LOQU/LOCUT (Latin)", "to talk/speak",
                   ["Loquacious (adj): Talkative", "Elocution (n): Art of speaking clearly",
                    "Eloquence (n): Fluent, persuasive speech",
                    "Colloquial (adj): Informal, conversational",
                    "Soliloquy (n): Speaking thoughts aloud when alone",
                    "Circumlocution (n): Indirect, roundabout speech"]),
    "reticent": ("TIC/TAC (Latin)", "silent",
                 ["Reticent (adj): Reserved, reluctant to speak",
                  "Taciturn (adj): Habitually silent",
                  "Tacit (adj): Implied without words"]),
    "garrulous": ("GARR (Latin)", "chattering/prattle",
                  ["Garrulous (adj): Excessively talkative",
                   "Garrulity (n): The quality of being talkative"]),
    "verbose": ("VERB (Latin)", "word",
                ["Verbose (adj): Wordy, using too many words",
                 "Verbosity (n): Excessive wordiness",
                 "Verbatim (adv): Word for word",
                 "Verbal (adj): Of or in words"]),
    "taciturn": ("TAC/TIC (Latin)", "silent",
                 ["Taciturn (adj): Habitually silent",
                  "Reticent (adj): Reluctant to speak",
                  "Tacit (adj): Implied, unspoken"]),
    "ephemeral": ("EPHEMER (Greek)", "lasting only a day",
                  ["Ephemeral (adj): Short-lived, fleeting",
                   "Ephemera (n): Things that exist only briefly"]),
    "obstinate": ("OBSTIN (Latin)", "stubborn/stand firm",
                  ["Obstinate (adj): Stubbornly refusing to change",
                   "Obstinacy (n): Stubbornness"]),
    "meticulous": ("METICUL (Latin)", "fearful/extremely careful",
                   ["Meticulous (adj): Showing great care with details",
                    "Meticulosity (n): Extreme carefulness"]),
    "benevolent": ("BENE (Latin)", "well/good",
                   ["Benevolent (adj): Kind, charitable",
                    "Benefactor (n): One who gives help",
                    "Beneficial (adj): Producing good",
                    "Benign (adj): Gentle, kind"]),
    "malevolent": ("MALE (Latin)", "bad/evil",
                   ["Malevolent (adj): Wishing harm to others",
                    "Malice (n): Desire to cause harm",
                    "Malign (v): To speak evil of"]),
    "lucid": ("LUC/LUM (Latin)", "light",
              ["Lucid (adj): Clear, easy to understand",
               "Elucidate (v): To make clear",
               "Translucent (adj): Allowing light through",
               "Lucidity (n): Clarity"]),
    "voracious": ("VOR (Latin)", "to eat/devour",
                  ["Voracious (adj): Having a huge appetite",
                   "Voracity (n): Greedy craving",
                   "Carnivore (n): Meat-eater",
                   "Herbivore (n): Plant-eater"]),
    "luminous": ("LUM/LUC (Latin)", "light",
                 ["Luminous (adj): Emitting light, bright",
                  "Illuminate (v): To light up",
                  "Luminary (n): A person who inspires others"]),
    "audacious": ("AUD/AU (Latin)", "bold/daring",
                  ["Audacious (adj): Recklessly bold",
                   "Audacity (n): Boldness, daring"]),
    "tenacious": ("TEN/TIN (Latin)", "to hold",
                  ["Tenacious (adj): Holding firmly, persistent",
                   "Tenacity (n): Persistence",
                   "Tenant (n): One who holds property",
                   "Retain (v): To keep holding"]),
    "vehement": ("VEHE (Latin)", "carrying/forceful",
                 ["Vehement (adj): Showing strong feeling",
                  "Vehemence (n): Intense emotion"]),
    "frugal": ("FRUG (Latin)", "fruit/economical",
               ["Frugal (adj): Sparing, economical",
                "Frugality (n): The quality of being thrifty"]),
    "pensive": ("PENS (Latin)", "to weigh/think",
                ["Pensive (adj): Thoughtful, often with sadness",
                 "Pension (n): A periodic payment (originally 'weighed out')",
                 "Ponder (v): To think carefully"]),
    "novice": ("NOV (Latin)", "new",
               ["Novice (n): A beginner",
                "Novelty (n): The quality of being new",
                "Innovate (v): To introduce new things",
                "Renovate (v): To make new again"]),
    "placid": ("PLAC (Latin)", "calm/flat",
               ["Placid (adj): Calm, peaceful",
                "Placate (v): To calm down, soothe",
                "Complacent (adj): Self-satisfied"]),
    "candid": ("CAND (Latin)", "white/transparent",
               ["Candid (adj): Honest, direct",
                "Candidacy (n): Standing for election (originally in a white toga)",
                "Candle (n): Originally 'white light'"]),
    "gregarious": ("GREG (Latin)", "flock/herd",
                   ["Gregarious (adj): Sociable, fond of company",
                    "Congregate (v): To gather in a flock",
                    "Segregate (v): To separate from the flock"]),
    "obsolete": ("OBSO (Latin)", "worn out/against use",
                 ["Obsolete (adj): No longer used",
                  "Obsolescent (adj): Becoming obsolete"]),
    "frivolous": ("FRIVOL (Latin)", "silly/trifling",
                  ["Frivolous (adj): Not serious, trivial",
                   "Frivolity (n): Lack of seriousness"]),
    "intrepid": ("TREP (Latin)", "to tremble",
                 ["Intrepid (adj): Fearless, brave",
                  "Trepidation (n): Fear, trembling"]),
    "languid": ("LANGU (Latin)", "faint/sluggish",
                ["Languid (adj): Lacking energy",
                 "Languish (v): To lose strength",
                 "Languor (n): Lazy tiredness"]),
    "amiable": ("AMI (Latin)", "friend",
                ["Amiable (adj): Friendly, pleasant",
                 "Amicable (adj): Peaceable",
                 "Amity (n): Friendship",
                 "Enemy (n): (from in- + ami)"]),
    "ambiguous": ("AMBI (Latin)", "both/around",
                  ["Ambiguous (adj): Having two meanings",
                   "Ambidextrous (adj): Able to use both hands",
                   "Ambit (n): Scope, range"]),
    "edify": ("ED (Latin)", "to build/educate",
              ["Edify (v): To instruct morally",
               "Edifice (n): A large building (metaphorical)",
               "Edification (n): Moral improvement"]),
}

MNEMONICS_DB = {
    "loquacious": "LOQUA sounds like \"Local Quack\" — imagine a talkative doctor who never stops chatting.",
    "reticent": "RETI + CENT — RETIre from spending a CENT on words; very quiet, won't speak.",
    "garrulous": "GARR sounds like \"Garrr\" — a pirate who talks too much, never stops chattering.",
    "verbose": "VERB is a word; VERBOSE = too many words (verbs).",
    "taciturn": "TACIT + TURN — silently TURNing away from conversation.",
    "ephemeral": "E (out) + HEMERA (a day) — lasting only a day; fleeting.",
    "obstinate": "OB (against) + STIN (stand) — standing against, refusing to move.",
    "meticulous": "METICUL sounds like \"meh-tick-you-lus\" — careful that not even a tick lands on you.",
    "benevolent": "BENE (good) + VOL (will) — wishing good for others.",
    "malevolent": "MALE (bad) + VOL (will) — wishing harm to others.",
    "lucid": "LUCID = clearly \"loo-side\" — easily seen on the bright side.",
    "voracious": "VOR (devour) — like a voracious reader devours books.",
    "luminous": "LUMIN = \"loom-in-us\" — a bright glow looming inside us.",
    "audacious": "AUD (bold) — audaciously stepping onto the stage.",
    "tenacious": "TEN (hold) — TENacious holds on with TEN fingers, never letting go.",
    "vehement": "VEHEMENT sounds like \"wee-mint\" — a strong, forceful mint flavor.",
    "frugal": "FRUGAL = \"few-gal\" — only a FEW GALlons used; very economical.",
    "pensive": "PENS (think) — PENsive person is deep in thought.",
    "novice": "NOV (new) — a NOVice is NEW to the game.",
    "placid": "PLACID = \"play-sid\" — calm kid playing quietly on the side.",
    "candid": "CAND (white) — pure, honest, transparent like a candle.",
    "gregarious": "GREG (flock) — a GREGarious person loves being in a flock of friends.",
    "obsolete": "OB + SOLETE — \"so-leet\" — worn out and useless now.",
    "frivolous": "FRIVOL = \"free-vol\" — freely wasting time on trivial matters.",
    "intrepid": "IN (not) + TREP (tremble) — never trembling, fearless.",
    "languid": "LANGUID = \"lang-wid\" — too lazy to widen one's eyes, sluggish.",
    "amiable": "AMI (friend) — AMIable person is friendly like a pal.",
    "ambiguous": "AMBI (both) — AMBiguous means BOTH meanings possible.",
    "edify": "ED (build) — EDify builds up the mind with moral instruction.",
}

def get_wordnet_info(word):
    synsets = wordnet.synsets(word)
    if not synsets:
        return {"definition": "", "pos": "", "wn_synonyms": [], "wn_antonyms": []}
    primary = synsets[0]
    definition = primary.definition()
    pos_map = {
        wordnet.NOUN: "Noun",
        wordnet.VERB: "Verb",
        wordnet.ADJ: "Adjective",
        wordnet.ADV: "Adverb",
    }
    pos = pos_map.get(primary.pos(), "")
    wn_syn = set()
    wn_ant = set()
    for s in synsets[:3]:
        for lemma in s.lemmas():
            wn_syn.add(lemma.name().replace("_", " "))
            for ant in lemma.antonyms():
                wn_ant.add(ant.name().replace("_", " "))
    return {
        "definition": definition,
        "pos": pos,
        "wn_synonyms": sorted(wn_syn)[:10],
        "wn_antonyms": sorted(wn_ant)[:10],
    }

def main():
    # Build enriched entries
    enriched = {}
    no_wordnet = 0

    # Convert sets to lists for status lookup
    syn_correct = ssc_rel["syn_correct"]
    syn_distractor = ssc_rel["syn_distractor"]
    ant_correct = ssc_rel["ant_correct"]
    ant_distractor = ssc_rel["ant_distractor"]

    for w_entry in words:
        word = w_entry["word"]
        word_low = w_entry["wordLower"]
        wn = get_wordnet_info(word_low)
        if not wn["definition"]:
            no_wordnet += 1

        # Build synonyms list with status
        # 1. Correct SSC synonyms → green
        # 2. Distractor SSC synonyms → red
        # 3. WordNet-only synonyms → gray (added)
        ss_synonyms = []
        seen = set()
        for s in syn_correct.get(word_low, []):
            if s and s != word_low and s not in seen:
                ss_synonyms.append({"word": s.capitalize(), "status": "correct"})
                seen.add(s)
        for s in syn_distractor.get(word_low, []):
            if s and s != word_low and s not in seen:
                ss_synonyms.append({"word": s.capitalize(), "status": "distractor"})
                seen.add(s)
        for s in wn["wn_synonyms"]:
            s_low = s.lower()
            if s_low not in seen and s_low != word_low:
                ss_synonyms.append({"word": s.capitalize(), "status": "added"})
                seen.add(s_low)
        ss_synonyms = ss_synonyms[:12]

        ss_antonyms = []
        seen = set()
        for a in ant_correct.get(word_low, []):
            if a and a != word_low and a not in seen:
                ss_antonyms.append({"word": a.capitalize(), "status": "correct"})
                seen.add(a)
        for a in ant_distractor.get(word_low, []):
            if a and a != word_low and a not in seen:
                ss_antonyms.append({"word": a.capitalize(), "status": "distractor"})
                seen.add(a)
        for a in wn["wn_antonyms"]:
            a_low = a.lower()
            if a_low not in seen and a_low != word_low:
                ss_antonyms.append({"word": a.capitalize(), "status": "added"})
                seen.add(a_low)
        ss_antonyms = ss_antonyms[:12]

        # Root
        root_info = ROOTS_DB.get(word_low)
        root = None
        if root_info:
            root = {
                "primary": root_info[0],
                "meaning": root_info[1],
                "family": root_info[2],
                "added": False,
            }
        # Mnemonic
        mnemonic = MNEMONICS_DB.get(word_low, "")

        enriched[word_low] = {
            "word": word,
            "wordLower": word_low,
            "definition": wn["definition"],
            "pos": wn["pos"],
            "ssSynonyms": ss_synonyms,
            "ssAntonyms": ss_antonyms,
            "root": root,
            "mnemonic": mnemonic,
        }

    print(f"Words without a WordNet definition: {no_wordnet}")
    print(f"Words with curated root info: {sum(1 for v in enriched.values() if v['root'])}")
    print(f"Words with mnemonic: {sum(1 for v in enriched.values() if v['mnemonic'])}")

    # Split per letter
    out_dir = os.path.join(DATA_DIR, "enriched")
    os.makedirs(out_dir, exist_ok=True)

    # Clear old per-letter files
    for f in glob_existing_letter_files(out_dir):
        os.remove(f)

    buckets = defaultdict(dict)
    for word_low, entry in enriched.items():
        letter = word_low[0] if word_low else "_"
        buckets[letter][word_low] = entry
    for letter, entries in buckets.items():
        out_path = os.path.join(out_dir, f"enriched_{letter}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False)
    print(f"Wrote {len(buckets)} letter-bucketed files to {out_dir}")
    print(f"Total entries: {sum(len(v) for v in buckets.values())}")

    # Also write the full enriched.json (for backward compat / download)
    with open(os.path.join(DATA_DIR, "enriched.json"), "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

def glob_existing_letter_files(d):
    import glob
    return glob.glob(os.path.join(d, "enriched_*.json"))

if __name__ == "__main__":
    from collections import defaultdict
    main()
