#!/usr/bin/env python3
"""Translate the 5 Hindi-containing rule fields to Bengali. Direct prompt."""
import json, re, time, urllib.request, os

API_KEY = 'sk-p7r8yV70mfSCdHmSEyAVCsa47Cef7DQqz9nk2KMwaXuHM09Q'
API_URL = 'https://kktoken.cc/v1/chat/completions'
MODEL = 'claude-opus-4-8'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

texts = {
    'rule_68_trick': '<strong>Hard</strong> = मेहनत से | <strong>Hardly</strong> = मुश्किल से / ना के बराबर',
    'rule_91_explain': 'Final review with Hindi keywords: <b>Hard</b> = मेहनत से (with effort). <b>Hardly</b> = मुश्किल से / ना के बराबर (barely/scarcely).',
    'rule_91_trick': '<strong>Hard</strong> = मेहनत से | <strong>Hardly</strong> = मुश्किल से',
    'rule_101_trick': '<strong>Sometime</strong> = कब? | <strong>Sometimes</strong> = कभी-कभी | <strong>Some time</strong> = थोड़ा समय',
    'rule_106_trick': '<strong>Still</strong> = अभी भी | <strong>Yet</strong> = अब तक नहीं | <strong>Already</strong> = पहले से हो गया',
}

def translate(text):
    prompt = f"""You are a Hindi-to-Bengali translator. The following text contains Hindi words in Devanagari script. Replace EVERY Hindi word with its Bengali equivalent. Keep all English words and HTML tags unchanged.

Hindi to Bengali reference:
- मेहनत → পরিশ্রম
- मुश्किल → কঠিন
- ना → না
- के बराबर → এর সমান
- कब → কখন
- कभी-कभी → মাঝে মাঝে
- कभी → কখনো
- थोड़ा → সামান্য
- समय → সময়
- अभी → এখনো
- भी →ও
- अब → এখন
- तक → পর্যন্ত
- नहीं → না
- पहले → আগে
- से → থেকে
- हो → হয়
- गया → গেছে

Text to translate (replace all Hindi with Bengali):
{text}

Output ONLY the result with Hindi replaced by Bengali. Keep English + HTML tags exactly as-is."""

    body = json.dumps({
        'model': MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0,
        'max_tokens': 500,
    }).encode('utf-8')
    req = urllib.request.Request(API_URL, data=body, headers={
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'User-Agent': UA,
    })
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f'  retry: {e}')
            time.sleep(2)
    return text

results = {}
for key, text in texts.items():
    result = translate(text)
    results[key] = result
    print(f'{key}:')
    print(f'  IN:  {text}')
    print(f'  OUT: {result}')
    print()
    time.sleep(1)

with open('/tmp/translate_progress.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('Saved /tmp/translate_progress.json')
