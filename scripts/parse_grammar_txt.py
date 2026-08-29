#!/usr/bin/env python3
"""Parse ALL SSC txt files and extract grammar questions (NO Satwik data).

Extracts 4 grammar question types directly from the raw .txt papers:
  - error      : error spotting ("divided into parts" / "No error")
  - improvement: sentence improvement ("substitute the underlined segment" / "No substitution")
  - narration  : direct/indirect speech
  - voice      : active/passive voice

Excludes: comprehension, cloze test, vocab (syn/ant/ows/idiom/homonym/spelling),
para-jumble, spelling.

Output: /home/z/my-project/work/grammar/grammar_pyqs.json
        {error:[...], improvement:[...], narration:[...], voice:[...]}
Each question: {id, exam, year, qtype, prompt, sentence, options[4], correctIdx(unknown->null)}
"""
import os, re, json, glob
from collections import OrderedDict

TXT_DIR = "/home/z/my-project/ssc-txt"
OUT = "/home/z/my-project/work/grammar/grammar_pyqs.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ---- question-block splitter ----
# A block starts with a line like "Q12." or "Q12)" possibly at start of line.
Q_START = re.compile(r'^\s*Q\s*(\d+)\s*[.\):]\s*', re.MULTILINE)
OPT_LINE = re.compile(r'^\s*[\(\[]?\s*([A-Da-d1-4])\s*[\)\].:\-]\s*(.+)$')

def split_blocks(text):
    """Yield (qnum, block_text) for each question block."""
    # find all Q start positions
    marks = [(m.start(), m.group(1)) for m in Q_START.finditer(text)]
    for i, (start, qnum) in enumerate(marks):
        end = marks[i+1][0] if i+1 < len(marks) else len(text)
        block = text[start:end]
        yield qnum, block

def parse_block(qnum, block, exam, year):
    lines = [ln.rstrip() for ln in block.splitlines()]
    # drop the first "Qn." line
    if lines and re.match(r'^\s*Q\s*\d+', lines[0]):
        lines = lines[1:]
    # find option lines
    opt_indices = []
    for i, ln in enumerate(lines):
        m = OPT_LINE.match(ln)
        if m and m.group(1) in 'ABCDabcd1234':
            # ensure it's a real option (4 distinct labels expected)
            opt_indices.append((i, m.group(1).upper().replace('1','A').replace('2','B').replace('3','C').replace('4','D'), m.group(2)))
    # need at least 4 options; keep the LAST group of 4 contiguous-ish options
    if len(opt_indices) < 4:
        return None
    # take last 4 (in case question text mentions A/B/C/D earlier)
    opts4 = opt_indices[-4:]
    labels = [o[1] for o in opts4]
    # must be the 4 distinct labels A,B,C,D
    if set(labels) != {'A','B','C','D'}:
        return None
    first_opt_i = opts4[0][0]
    # prompt + sentence = everything before first option
    head = lines[:first_opt_i]
    # option texts: each option may span multiple lines until next option
    options = []
    for j,(idx,lab,txt) in enumerate(opts4):
        nxt = opts4[j+1][0] if j+1 < len(opts4) else len(lines)
        body = [txt] + lines[idx+1:nxt]
        body = [b.strip() for b in body if b.strip()]
        options.append(' '.join(body))
    # head: separate prompt from sentence. Heuristic: prompt = first 1-3 lines until a sentence
    # that looks like the actual question sentence. We'll keep prompt = all head joined, and
    # try to split sentence as the last line(s) that don't look like instruction.
    head_text = '\n'.join(h.strip() for h in head if h.strip())
    # classify
    qtype = classify(head_text, options)
    if qtype is None:
        return None
    # split prompt vs sentence
    prompt, sentence = split_prompt_sentence(head_text, qtype)
    # clean option labels
    options = [re.sub(r'^[\(\[]?\s*[A-Da-d1-4]\s*[\)\].:\-]\s*', '', re.sub(r'^[\(\[]?\s*[A-Da-d1-4]\s*[\)\].:\-]\s*','',o)) if False else o for o in options]
    q = {
        "id": None,
        "exam": exam,
        "year": year,
        "qtype": qtype,
        "prompt": _clean_prompt(prompt),
        "sentence": _clean_sentence(sentence),
        "options": options,
        "correctIdx": None,  # to be filled by AI later
    }
    return q

def _clean_prompt(p):
    p = re.sub(r'^\s*Q\s*\d+\s*[.):\-]?\s*', '', p).strip()
    p = re.sub(r'\s+', ' ', p)
    return p

def _clean_sentence(s):
    s = re.sub(r'^\s*sentence\s*[:.]\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def classify(head, options):
    h = head.lower()
    # exclude vocab / spelling / comprehension / cloze / para-jumble
    if any(k in h for k in ['synonym','antonym','one-word','one word substitut','idiom','homonym','homophone','misspelt','incorrectly spelt','correctly spelt','spelling','cloze','comprehension','read the passage','arranges the given parts','meaningful and coherent paragraph','rearrange']):
        return None
    # narration
    if any(k in h for k in ['direct speech','indirect speech','change the narration','narration']):
        return 'narration'
    # voice
    if any(k in h for k in ['passive voice','active voice']):
        return 'voice'
    # error spotting
    if any(k in h for k in ['divided into parts','divided into three segments','divided into segments','contains the error','contains a grammatical error','contains an error','find any error','no error','spotting']):
        return 'error'
    if 'no error' in ' '.join(options).lower():
        return 'error'
    # improvement
    if any(k in h for k in ['substitute the underlined segment','no substitution','no need to substitute','most appropriate option to substitute','substitute the underlined part','improvement']):
        return 'improvement'
    # other grammar types we still capture under 'improvement'-like? keep focused.
    return None

def split_prompt_sentence(head_text, qtype):
    # The sentence is usually the line(s) after the instruction, containing the actual content.
    # Heuristic: prompt = leading instructional lines (until we hit a line that looks like a sentence).
    lines = [ln.strip() for ln in head_text.splitlines() if ln.strip()]
    if not lines:
        return '', ''
    # For error: sentence contains ' / ' separators often, or is a standalone sentence.
    # For voice/narration/improvement: sentence is a standalone sentence.
    # Heuristic: prompt = all lines except the last contiguous run of "content" lines.
    # Simpler: prompt = first line(s) up to the first line that does NOT start with a typical
    # instruction verb. We'll treat the LAST line(s) as sentence if they look like a sentence.
    # Very robust approach: prompt = everything, sentence = the last line if it doesn't end with
    # a question word and isn't an instruction. Otherwise sentence = ''.
    instr_words = ('select','the following','choose','identify','a sentence','convert','from the','pick','in the')
    # find first content line index = first line that doesn't look like an instruction
    content_start = None
    for i, ln in enumerate(lines):
        low = ln.lower()
        looks_instr = any(low.startswith(w) or low.startswith('the '+w) for w in instr_words) or any(k in low for k in ['given options','given sentence','mark','answer','error','substitute','voice','speech','narration','divided'])
        if not looks_instr and len(ln) > 12:
            content_start = i
            break
    if content_start is not None and content_start < len(lines):
        prompt = ' '.join(lines[:content_start])
        sentence = ' '.join(lines[content_start:])
    else:
        prompt = ' '.join(lines)
        sentence = ''
    return prompt, sentence

def exam_year(fname):
    base = os.path.basename(fname).replace('_EN.txt','')
    # SSC_CGL_Tier1_2023 -> exam=SSC CGL Tier1, year=2023
    m = re.match(r'(SSC_[A-Za-z_]+?)_(\d{4})', base)
    if m:
        exam = m.group(1).replace('_',' ')
        year = m.group(2)
        return exam, year
    return base, ''

def main():
    files = sorted(glob.glob(os.path.join(TXT_DIR, '*.txt')))
    buckets = {'error':[], 'improvement':[], 'narration':[], 'voice':[]}
    seen = set()  # dedup by normalized sentence+options
    total_blocks = 0
    for f in files:
        exam, year = exam_year(f)
        text = open(f, encoding='utf-8', errors='ignore').read()
        for qnum, block in split_blocks(text):
            total_blocks += 1
            q = parse_block(qnum, block, exam, year)
            if not q:
                continue
            # dedup key
            key = (q['qtype'], re.sub(r'\W+','', (q['sentence'] or q['prompt']).lower())[:80], tuple(re.sub(r'\W+','',o.lower())[:30] for o in q['options']))
            if key in seen:
                continue
            seen.add(key)
            buckets[q['qtype']].append(q)
    # assign ids
    for qt in buckets:
        for i,q in enumerate(buckets[qt]):
            q['id'] = f"{qt}_{i+1}"
    # stats
    print(f"Total Q-blocks scanned: {total_blocks}")
    for qt in buckets:
        print(f"  {qt}: {len(buckets[qt])}")
    with open(OUT,'w',encoding='utf-8') as fh:
        json.dump(buckets, fh, ensure_ascii=False, indent=1)
    print(f"-> {OUT}")
    # also save an "unmatched grammar" note: questions that looked like grammar but didn't classify
    # (not strictly needed; classification is keyword-based)

if __name__ == '__main__':
    main()
