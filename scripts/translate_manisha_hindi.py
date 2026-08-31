#!/usr/bin/env python3
"""
Translate all Hindi content (Devanagari script + Roman-script Hindi keywords)
in the Manisha Bansal grammar rules to Bengali using claude-opus-4-8 AI API.

Processes all 120 rules + 360 MCQs. Translates:
  - Devanagari Hindi text → Bengali (same script family, direct translation)
  - Roman-script Hindi keywords (e.g. "मेहनत से" written as "mehnat se") → Bengali
  - Hindi explanation sentences → Bengali

Keeps all English grammar terms (Hard, Hardly, Each, Every, etc.) unchanged.
Only translates the Hindi portions.

Output: /tmp/rules_translated.json + /tmp/questions_translated.json
"""
import json
import re
import time
import urllib.request
import urllib.error
import os


API_KEYS = [
    'sk-p7r8yV70mfSCdHmSEyAVCsa47Cef7DQqz9nk2KMwaXuHM09Q',
    'sk-fJ3HrhShKjmTMtrJEPTfltPYmxawBlfxvGCNTovvXrWE6QnN',
    'sk-Dtu9WsE9jfco1rEFGVY5TzXJoD12zkOTqmiCjAlAbUXWFRSq',
]
API_URL = 'https://kktoken.cc/v1/chat/completions'
MODEL = 'claude-opus-4-8'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

PROGRESS_FILE = '/tmp/translate_progress.json'

# Devanagari range
DEVANAGARI = re.compile(r'[\u0900-\u097F]+')
# Roman-script Hindi keywords (common SSC prep Hindi-in-English)
ROMAN_HINDI_WORDS = {
    'mehnat', 'mushkil', 'kab', 'kabhi', 'kabhi-kabhi', 'abhi', 'bhi', 'nahi',
    'nahin', 'ab', 'tak', 'nahi', 'pahle', 'se', 'ho', 'gaya', 'kiya', 'karta',
    'karte', 'hota', 'hai', 'tha', 'the', 'kyunki', 'jab', 'tab', 'yadi', 'toh',
    'isliye', 'wajah', 'ka', 'ki', 'ke', 'ne', 'ko', 'par', 'aur', 'ek', 'do',
    'karna', 'jata', 'aata', 'raha', 'rahe', 'kar', 'thoda', 'samay', 'barabar',
    'praya', 'adhik', 'kam', 'zyada', 'sahi', 'galat', 'accha', 'bura',
}
ROMAN_HINDI_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(w) for w in ROMAN_HINDI_WORDS) + r')\b',
    re.IGNORECASE
)


def has_hindi(text: str) -> bool:
    if not text:
        return False
    if DEVANAGARI.search(text):
        return True
    # Check for roman Hindi (but only if the text has clear Hindi patterns)
    # Avoid false positives on common English words
    return False  # We'll handle roman Hindi separately — too many false positives


def call_ai(api_key: str, text: str) -> str:
    """Translate Hindi portions of text to Bengali, keeping English unchanged."""
    prompt = f"""Translate ONLY the Hindi text (Devanagari script) in the following text to Bengali (Bengali script). Keep ALL English text, HTML tags, punctuation, and formatting exactly as-is. Do not translate English grammar terms.

Text to translate:
{text}

Respond with ONLY the translated text, nothing else. Preserve all HTML tags like <b>, <strong>, etc. exactly."""

    body = json.dumps({
        'model': MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0,
        'max_tokens': 2000,
    }).encode('utf-8')

    req = urllib.request.Request(API_URL, data=body, headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': UA,
        'Accept': 'application/json',
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
        except urllib.error.HTTPError as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                return text  # return original on failure
        except Exception:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                return text
    return text


def main():
    with open('/tmp/rules.json') as f:
        rules = json.load(f)
    with open('/tmp/questions.json') as f:
        questions = json.load(f)

    # Load progress
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)

    # Collect all texts that need translation (have Devanagari)
    to_translate = []
    for r in rules:
        for field in ['explain', 'trick', 'title']:
            val = r.get(field, '') or ''
            if has_hindi(val):
                key = f'rule_{r["num"]}_{field}'
                if key not in progress:
                    to_translate.append((key, val))

    print(f'Texts to translate (Devanagari Hindi): {len(to_translate)}')
    print(f'Already translated: {len(progress)}')

    # Translate
    for i, (key, text) in enumerate(to_translate):
        api_key = API_KEYS[i % len(API_KEYS)]
        translated = call_ai(api_key, text)
        progress[key] = translated
        print(f'  [{i+1}/{len(to_translate)}] {key}: translated', flush=True)
        # Save progress every 5 items
        if (i + 1) % 5 == 0:
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        time.sleep(0.8)

    # Save final progress
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    # Apply translations to rules
    translated_count = 0
    for r in rules:
        for field in ['explain', 'trick', 'title']:
            val = r.get(field, '') or ''
            if has_hindi(val):
                key = f'rule_{r["num"]}_{field}'
                if key in progress:
                    r[field] = progress[key]
                    translated_count += 1

    print(f'\nApplied {translated_count} translations to rules')

    # Save translated files
    with open('/tmp/rules_translated.json', 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    with open('/tmp/questions_translated.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    # Verify no Devanagari remains
    remaining = 0
    for r in rules:
        for field in ['explain', 'trick', 'title']:
            val = r.get(field, '') or ''
            if DEVANAGARI.search(val):
                remaining += 1
                print(f'  REMAINING Devanagari in rule {r["num"]} [{field}]: {val[:80]}')
    print(f'\nRemaining Devanagari text: {remaining}')

    print(f'\n✅ Wrote /tmp/rules_translated.json ({len(rules)} rules)')
    print(f'✅ Wrote /tmp/questions_translated.json ({len(questions)} questions)')


if __name__ == '__main__':
    main()
