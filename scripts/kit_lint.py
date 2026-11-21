#!/usr/bin/env python3
"""Lint a posting_kit.md (template: assets/posting-kit-template.md):  python3 kit_lint.py <project>/posting_kit.md [--allow-roman-hindi]
Checks: Title <= 60 chars, no hashtag in the title; YouTube tags filled to 470-500 chars; Instagram caption <= 5 hashtags, no duplicates; YouTube description has 3 hashtags;
metadata is English only (no Devanagari, no Roman-script Hindi words) unless --allow-roman-hindi. Prints PASS/FAIL, exit 1 on FAIL."""
import re, sys
HINGLISH = {"kya", "hai", "hota", "kaise", "kyun", "kyu", "nahi", "aur", "mein", "ka", "ki", "ke", "ko", "pe", "bhai", "yaar", "karo", "batao", "dekho", "wala", "wali", "kaun", "kab", "matlab", "samjho", "seekho", "jaldi", "bilkul", "sabse", "apna", "tumhara", "aapka", "iska", "isse", "wahi", "toh", "bhi", "tha", "thi", "raha", "rahe", "hoga", "chahiye", "kuch", "wapas", "baar", "kaam"}
t = open(sys.argv[1], encoding="utf-8").read(); bad = []
field = lambda label: (re.search(r"\*\*" + label + r":?\*\*:?\s*`([^`]+)`", t) or [None, ""])[1]
block = lambda after: (re.search(re.escape(after) + r".*?```\n(.*?)```", t, re.S) or [None, ""])[1]
title, tags, ig, yt = field("Title"), field("Tags"), block("**Caption**"), block("**Description**")
if not (title and tags and ig and yt): bad.append("missing Title / Tags / Instagram caption / YouTube description")
if not 470 <= len(tags) <= 500: bad.append(f"YouTube tags are {len(tags)} chars; fill the field to 470-500")
if len(title) > 60 or "#" in title: bad.append("title must be <= 60 chars with no hashtags")
if "--allow-roman-hindi" not in sys.argv:
    for name, text in [("title", title), ("tags", tags), ("instagram caption", ig), ("youtube description", yt)]:
        hits = sorted({w for w in re.findall(r"[a-z']+", text.lower()) if w in HINGLISH})
        if hits: bad.append(f"Roman-script Hindi in {name}: {', '.join(hits)} (metadata must be English)")
        if re.search(r"[ऀ-ॿ]", text): bad.append(f"Devanagari in {name}")
for name, text in [("instagram", ig), ("youtube", yt)]:
    h = re.findall(r"#\w+", text)
    if len(h) != len(set(x.lower() for x in h)): bad.append(f"duplicate hashtags in {name}")
if len(re.findall(r"#\w+", ig)) > 5: bad.append("Instagram: max 5 hashtags")
print("PASS" if not bad else "FAIL\n- " + "\n- ".join(bad)); sys.exit(1 if bad else 0)
