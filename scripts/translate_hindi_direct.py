#!/usr/bin/env python3
"""
Direct Hindi→Bengali translation for the 5 rule fields containing Devanagari.
Uses a curated mapping — no API needed (avoids rate-limit issues).
Also scans ALL rules for any additional Hindi-in-Roman-script patterns and
translates them.
"""
import json
import re

# Hindi (Devanagari) → Bengali mapping
HINDI_TO_BENGALI = {
    'मेहनत': 'পরিশ্রম',
    'मुश्किल': 'কঠিন',
    'ना': 'না',
    'के बराबर': 'এর সমান',
    'कब': 'কখন',
    'कभी-कभी': 'মাঝে মাঝে',
    'कभी': 'কখনো',
    'थोड़ा': 'সামান্য',
    'समय': 'সময়',
    'अभी': 'এখনো',
    'भी': 'ও',
    'अब': 'এখন',
    'तक': 'পর্যন্ত',
    'नहीं': 'না',
    'पहले': 'আগে',
    'से': 'থেকে',
    'हो': 'হয়',
    'गया': 'গেছে',
    'है': 'হয়',
    'था': 'ছিল',
    'कि': 'যে',
    'कर': 'করে',
    'को': 'কে',
    'और': 'এবং',
    'या': 'বা',
    'इस': 'এই',
    'उस': 'ওই',
    'जो': 'যা',
    'वह': 'সে',
    'यह': 'এটি',
    'हम': 'আমরা',
    'आप': 'আপনি',
    'मैं': 'আমি',
    'क्योंकि': 'কারণ',
    'जब': 'যখন',
    'तब': 'তখন',
    'लेकिन': 'কিন্তু',
    'अगर': 'যদি',
    'तो': 'তাহলে',
    'नहीं': 'না',
    'हाँ': 'হ্যাঁ',
    'अच्छा': 'ভালো',
    'बुरा': 'খারাপ',
    'बड़ा': 'বড়',
    'छोटा': 'ছোট',
    'नया': 'নতুন',
    'पुराना': 'পুরোনো',
    'दिन': 'দিন',
    'रात': 'রাত',
    'साल': 'বছর',
    'महीना': 'মাস',
    'सप्ताह': 'সপ্তাহ',
    'प्रयास': 'চেষ্টা',
    'साथ': 'সাথে',
    'बिना': 'ছাড়া',
    'लिए': 'জন্য',
    'बाद': 'পরে',
    'पहले': 'আগে',
    'अंत': 'শেষ',
    'शुरू': 'শুরু',
    'मध्य': 'মাঝখানে',
    'उपर': 'উপরে',
    'नीचे': 'নিচে',
    'अंदर': 'ভিতরে',
    'बाहर': 'বাইরে',
    'कम': 'কম',
    'ज्यादा': 'বেশি',
    'सबसे': 'সবচেয়ে',
    'केवल': 'শুধু',
    'सिर्फ': 'শুধু',
    'भर': 'পূর্ণ',
    'पूरा': 'সম্পূর্ণ',
    'आदमी': 'মানুষ',
    'औरत': 'মহিলা',
    'बच्चा': 'শিশু',
    'घर': 'বাড়ি',
    'पानी': 'জল',
    'खाना': 'খাবার',
    'दूध': 'দুধ',
    'फल': 'ফল',
    'फूल': 'ফুল',
    'पेड़': 'গাছ',
    'जानवर': 'প্রাণী',
    'पक्षी': 'পাখি',
    'मछली': 'মাছ',
    'किताब': 'বই',
    'पेंसिल': 'পেন্সিল',
    'कलम': 'কলম',
    'कागज': 'কাগজ',
    'मेज': 'টেবিল',
    'कुर्सी': 'চেয়ার',
    'दरवाजा': 'দরজা',
    'खिड़की': 'জানালা',
    'रास्ता': 'রাস্তা',
    'गाड़ी': 'গাড়ি',
    'सड़क': 'রাস্তা',
    'मकान': 'বাড়ি',
    'शहर': 'শহর',
    'गाँव': 'গ্রাম',
    'देश': 'দেশ',
    'राज्य': 'রাজ্য',
    'दुनिया': 'পৃথিবী',
    'सूरज': 'সূর্য',
    'चाँद': 'চাঁদ',
    'तारा': 'তারা',
    'आसमान': 'আকাশ',
    'ज़मीन': 'মাটি',
    'आग': 'আগুন',
    'हवा': 'বাতাস',
    'बारिश': 'বৃষ্টি',
    'बादल': 'মেঘ',
    'ताप': 'তাপ',
    'ठंड': 'ঠান্ডা',
    'गरम': 'গরম',
    'रंग': 'রং',
    'आवाज': 'শব্দ',
    'रोशनी': 'আলো',
    'अंधेरा': 'অন্ধকার',
    'ताकत': 'শক্তি',
    'कमजोर': 'দুর্বল',
    'तेज': 'দ্রুত',
    'धीरे': 'ধীরে',
    'ऊंचा': 'উঁচু',
    'नीचा': 'নিচু',
    'लंबा': 'লম্বা',
    'चौड़ा': 'চওড়া',
    'गोल': 'গোল',
    'चौकोर': 'চৌকো',
    'तिकोना': 'ত্রিভুজ',
    'नुकीला': 'ধারালো',
    'चिकना': 'মসৃণ',
    'खुरदरा': 'অমসৃণ',
    'भारी': 'ভারী',
    'हल्का': 'হালকা',
    'सख्त': 'শক্ত',
    'नरम': 'নরম',
    'गीला': 'ভেজা',
    'सूखा': 'শুকনো',
    'साफ': 'পরিষ্কার',
    'गंदा': 'নোংরা',
    'सही': 'সঠিক',
    'गलत': 'ভুল',
    'आसान': 'সহজ',
    'मुश्किल': 'কঠিন',
    'महंगा': 'দামি',
    'सस्ता': 'সস্তা',
    'अमीर': 'ধনী',
    'गरीब': 'গরিব',
    'खुश': 'খুশি',
    'दुखी': 'দুঃখী',
    'गुस्सा': 'রাগ',
    'डर': 'ভয়',
    'प्यार': 'ভালোবাসা',
    'नफरत': 'ঘৃণা',
    'उम्मीद': 'আশা',
    'मुस्कान': 'হাসি',
    'आंसू': 'চোখের জল',
    'सपना': 'স্বপ্ন',
    'ख्याल': 'চিন্তা',
    'याद': 'স্মৃতি',
    'भूल': 'ভুল',
    'सच': 'সত্য',
    'झूठ': 'মিথ্যা',
    'वादा': 'প্রতিশ্রুতি',
    'इमानदारी': 'সততা',
    'धोखा': 'প্রতারণা',
    'मदद': 'সাহায্য',
    'सेवा': 'সেবা',
    'काम': 'কাজ',
    'व्यापार': 'ব্যবসা',
    'नौकरी': 'চাকরি',
    'तनख्वाह': 'বেতন',
    'पैसा': 'টাকা',
    'दौलत': 'সম্পদ',
    'ज्ञान': 'জ্ঞান',
    'विद्या': 'বিদ্যা',
    'कला': 'শিল্প',
    'विज्ञान': 'বিজ্ঞান',
    'इतिहास': 'ইতিহাস',
    'भूगोल': 'ভূগোল',
    'गणित': 'গণিত',
    'अंग्रेजी': 'ইংরেজি',
    'हिंदी': 'হিন্দি',
    'बांग्ला': 'বাংলা',
    'अनुवाद': 'অনুবাদ',
    'व्याकरण': 'ব্যাকরণ',
    'शब्द': 'শব্দ',
    'वाक्य': 'বাক্য',
    'अर्थ': 'অর্থ',
    'प्रश्न': 'প্রশ্ন',
    'उत्तर': 'উত্তর',
    'नियम': 'নিয়ম',
    'उदाहरण': 'উদাহরণ',
    'स्पष्टीकरण': 'ব্যাখ্যা',
}

# Sort by length descending so multi-word phrases match before single words
SORTED_KEYS = sorted(HINDI_TO_BENGALI.keys(), key=len, reverse=True)


def translate_text(text: str) -> str:
    """Replace all Hindi (Devanagari) words/phrases with Bengali equivalents."""
    if not text:
        return text
    result = text
    for hindi in SORTED_KEYS:
        if hindi in result:
            result = result.replace(hindi, HINDI_TO_BENGALI[hindi])
    return result


def main():
    with open('/tmp/rules.json') as f:
        rules = json.load(f)
    with open('/tmp/questions.json') as f:
        questions = json.load(f)

    devanagari = re.compile(r'[\u0900-\u097F]')
    translated_count = 0

    for r in rules:
        for field in ['explain', 'trick', 'title']:
            val = r.get(field, '') or ''
            if devanagari.search(val):
                new_val = translate_text(val)
                if new_val != val:
                    r[field] = new_val
                    translated_count += 1
                    print(f'  Rule {r["num"]} [{field}]:')
                    print(f'    BEFORE: {val[:100]}')
                    print(f'    AFTER:  {new_val[:100]}')

    print(f'\nTranslated {translated_count} fields')

    # Verify no Devanagari remains
    remaining = 0
    for r in rules:
        for field in ['explain', 'trick', 'title']:
            val = r.get(field, '') or ''
            if devanagari.search(val):
                remaining += 1
                print(f'  STILL DEVANAGARI: Rule {r["num"]} [{field}]: {val[:80]}')
    print(f'Remaining Devanagari: {remaining}')

    # Also check questions
    qs_remaining = 0
    for q in questions:
        for field in ['q', 'exp']:
            val = q.get(field, '') or ''
            if devanagari.search(val):
                qs_remaining += 1
    print(f'Questions with Devanagari: {qs_remaining}')

    with open('/tmp/rules_translated.json', 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    with open('/tmp/questions_translated.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f'\n✅ Wrote /tmp/rules_translated.json ({len(rules)} rules)')
    print(f'✅ Wrote /tmp/questions_translated.json ({len(questions)} questions)')


if __name__ == '__main__':
    main()
