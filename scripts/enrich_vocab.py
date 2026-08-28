#!/usr/bin/env python3
"""
Enrich vocabulary entries using:
1. SSC exam data itself: synonyms/antonyms extracted from related questions
2. NLTK WordNet: definitions, parts of speech, additional synonyms/antonyms
3. Heuristics: simple root word extraction, mnemonic generation (template-based)

Output: src/data/enriched.json — word -> {definition, pos, synonyms, antonyms, root, mnemonic, sscSynonyms, sscAntonyms}
"""

import json
import os
import re
import nltk

nltk.data.path.append('/home/z/nltk_data')
from nltk.corpus import wordnet

WORDS_FILE = "/home/z/my-project/src/data/words.json"
QUESTIONS_FILE = "/home/z/my-project/src/data/questions.json"
OUTPUT = "/home/z/my-project/src/data/enriched.json"

with open(WORDS_FILE) as f:
    words = json.load(f)
with open(QUESTIONS_FILE) as f:
    questions = json.load(f)

# Build a stem -> options map (and option -> stem map) for SSC synonyms/antonyms
ssc_syn = {}   # word -> set of words that appeared as SYNONYM-related
ssc_ant = {}   # word -> set of words that appeared as ANTONYM-related

# For synonym questions: stem and options are synonyms of each other
# For antonym questions: stem and options are antonyms of each other
# For one-word: the stem is a phrase; only the option words are vocab — they may be
#   related to the *phrase*, but we cannot reliably infer a "synonym" relationship
#   to other options. So skip one-word for now.

syn_q_count = 0
ant_q_count = 0
for q in questions:
    if q["qtype"] == "synonym":
        stem = q["stem"].strip().lower()
        opts = [o.strip().lower() for o in q["options"]]
        # Add bidirectional synonym relationships (stem <-> each option, and option <-> option)
        related = set([stem] + opts)
        for w in related:
            for other in related:
                if w != other:
                    ssc_syn.setdefault(w, set()).add(other)
        syn_q_count += 1
    elif q["qtype"] == "antonym":
        stem = q["stem"].strip().lower()
        opts = [o.strip().lower() for o in q["options"]]
        # stem is antonym of each option
        for o in opts:
            if stem and o:
                ssc_ant.setdefault(stem, set()).add(o)
                ssc_ant.setdefault(o, set()).add(stem)
        ant_q_count += 1

print(f"Synonym questions: {syn_q_count}, Antonym questions: {ant_q_count}")
print(f"SSC synonym map entries: {len(ssc_syn)}")
print(f"SSC antonym map entries: {len(ssc_ant)}")

# --- WordNet enrichment ---------------------------------------------------------
def get_wordnet_info(word):
    synsets = wordnet.synsets(word)
    if not synsets:
        return {"definition": "", "pos": "", "wn_synonyms": [], "wn_antonyms": []}

    # Use the first synset (most common sense)
    primary = synsets[0]
    definition = primary.definition()
    pos_map = {
        wordnet.NOUN: "Noun",
        wordnet.VERB: "Verb",
        wordnet.ADJ: "Adjective",
        wordnet.ADV: "Adverb",
    }
    pos = pos_map.get(primary.pos(), "")

    # Collect synonyms and antonyms across ALL synsets (top 10 each)
    wn_syn = set()
    wn_ant = set()
    for s in synsets[:3]:  # use top 3 senses for richer coverage
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

# --- Simple root/etymology heuristic -------------------------------------------
# We can't have a full etymology database, but we can give a few common Latin/Greek
# roots for select frequently-tested words. For other words, leave root blank.
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
                  "Tacit (adj): Implied without words",
                  "Retice (archaic verb): To keep silent"]),
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
    "ami": ("AMI (Latin)", "friend",
            ["Amiable (adj): Friendly",
             "Amicable (adj): Peaceable"]),
    "ambiguous": ("AMBI (Latin)", "both/around",
                  ["Ambiguous (adj): Having two meanings",
                   "Ambidextrous (adj): Able to use both hands",
                   "Ambit (n): Scope, range"]),
    "edify": ("ED (Latin)", "to build/educate",
              ["Edify (v): To instruct morally",
               "Edifice (n): A large building (metaphorical)",
               "Edification (n): Moral improvement"]),
}

# --- Mnemonic templates (simple, applicable to many common words) --------------
MNEMONIC_TEMPLATES = {
    # Templates are simple placeholder patterns
}

def generate_mnemonic(word):
    """Generate a simple phonetic mnemonic for a word."""
    # Use a simple heuristic: split word by syllable-like patterns and create a sentence
    # For demonstration, we use the first 3-5 letters as a "phrase"
    w = word.lower()
    # Some hand-crafted mnemonics for popular words
    crafted = {
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
    if w in crafted:
        return crafted[w]
    return ""

# --- Build enriched data --------------------------------------------------------
enriched = {}
total = len(words)
processed = 0
no_wordnet = 0

for w_entry in words:
    word = w_entry["word"]
    word_low = w_entry["wordLower"]
    processed += 1
    if processed % 500 == 0:
        print(f"  ... processed {processed}/{total}")

    # SSC synonyms/antonyms (intersect with our known word list)
    ssc_synonyms = sorted(ssc_syn.get(word_low, set()))
    ssc_antonyms = sorted(ssc_ant.get(word_low, set()))
    # Filter out multi-word phrases from SSC synonyms/antonyms (keep single words)
    ssc_synonyms = [s for s in ssc_synonyms if " " not in s and len(s) > 1]
    ssc_antonyms = [a for a in ssc_antonyms if " " not in a and len(a) > 1]
    # Limit to top 12 to keep UI clean
    ssc_synonyms = ssc_synonyms[:12]
    ssc_antonyms = ssc_antonyms[:12]

    # WordNet info
    wn = get_wordnet_info(word_low)
    if not wn["definition"]:
        no_wordnet += 1
    # Combine WordNet synonyms with SSC ones (dedup, mark source)
    combined_syn = []
    for s in ssc_synonyms:
        combined_syn.append({"word": s.capitalize(), "source": "ssc"})
    for s in wn["wn_synonyms"]:
        if s.lower() not in [x["word"].lower() for x in combined_syn]:
            combined_syn.append({"word": s.capitalize(), "source": "wordnet", "added": True})
    combined_ant = []
    for a in ssc_antonyms:
        combined_ant.append({"word": a.capitalize(), "source": "ssc"})
    for a in wn["wn_antonyms"]:
        if a.lower() not in [x["word"].lower() for x in combined_ant]:
            combined_ant.append({"word": a.capitalize(), "source": "wordnet", "added": True})

    # Root word
    root_info = ROOTS_DB.get(word_low, None)
    if root_info:
        root = {
            "primary": root_info[0],
            "meaning": root_info[1],
            "family": root_info[2],
            "added": False,
        }
    else:
        root = None

    # Mnemonic
    mnemonic = generate_mnemonic(word_low)

    enriched[word_low] = {
        "word": word,
        "wordLower": word_low,
        "definition": wn["definition"],
        "pos": wn["pos"],
        "ssSynonyms": combined_syn[:8],
        "ssAntonyms": combined_ant[:8],
        "root": root,
        "mnemonic": mnemonic,
    }

print(f"\nWords without a WordNet definition: {no_wordnet}")
print(f"Words with curated root info: {sum(1 for v in enriched.values() if v['root'])}")
print(f"Words with mnemonic: {sum(1 for v in enriched.values() if v['mnemonic'])}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(enriched, f, ensure_ascii=False, indent=2)

print(f"\nWrote {OUTPUT} ({len(enriched)} entries)")
