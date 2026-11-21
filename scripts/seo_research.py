#!/usr/bin/env python3
"""Keyword research for a video's posting kit (YouTube + Google autosuggest: free, no login, only your topic words are sent).

  python3 -I seo_research.py "object pooling" ["game memory management" ...] [--out project/seo_research.json]

Prints the phrases people really type, ranked by how many query patterns surface them, plus a tag list filled to ~480 characters.
Write the kit FROM this output plus a web search for what is trending; never from memory. Then run kit_lint.py."""
import argparse, json, re, urllib.parse, urllib.request
from collections import Counter

PATTERNS = ["{s}", "what is {s}", "how does {s} work", "{s} explained", "{s} interview questions", "{s} system design", "{s} for beginners", "{s} real life example", "{s} vs", "{s} tutorial", "why {s}", "{s} example"]
ASCII_EN = re.compile(r"^[a-z0-9 .+#/&'-]+$")
UA = {"User-Agent": "Mozilla/5.0 (explainer-skill keyword research)"}


def suggest(q, client):
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode({"client": client, "ds": "yt" if client == "youtube" else "", "q": q, "hl": "en"})
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=8).read().decode("utf-8", "ignore")
        return [x if isinstance(x, str) else x[0] for x in json.loads(raw[raw.index("["):])[1]]
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("seeds", nargs="+"); ap.add_argument("--out"); ap.add_argument("--tag-chars", type=int, default=480); a = ap.parse_args()
    yt, gg = Counter(), Counter()
    for s in a.seeds:
        for p in PATTERNS:
            q = p.format(s=s)
            for x in suggest(q, "youtube"): yt[x.lower().strip()] += 1
            for x in suggest(q, "firefox"): gg[x.lower().strip()] += 1
    ok = lambda t: bool(ASCII_EN.match(t)) and 2 < len(t) < 70
    ytl = [t for t, _ in yt.most_common(60) if ok(t)]; ggl = [t for t, _ in gg.most_common(60) if ok(t)]
    tags, seen = [], set()
    for t in [*a.seeds, *ytl, *ggl]:
        t = t.lower().strip()
        if t in seen or not ok(t): continue
        if len(", ".join(tags + [t])) > a.tag_chars: continue
        tags.append(t); seen.add(t)
    res = {"seeds": a.seeds, "youtube_search_phrases": ytl[:40], "google_search_phrases": ggl[:40], "tags": tags}
    if a.out: json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res, indent=1)); print(f"\n{len(', '.join(tags))} tag characters, {len(tags)} tags. Curate: drop other meanings of the words, keep what a learner types. Choose 1 primary + 3 secondary keywords.")


if __name__ == "__main__":
    main()
