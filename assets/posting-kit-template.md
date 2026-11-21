# Posting kit — <Video title in English>
<!-- Fill for every video → <project>/posting_kit.md, then run `python3 scripts/kit_lint.py <project>/posting_kit.md` (must print PASS). -->

## Step 0 — research first (never write the kit from memory)
1. `python3 -I scripts/seo_research.py "<primary topic>" "<related term>" --out <project>/seo_research.json` (YouTube + Google autosuggest: what people really type).
2. Web searches: what is trending around the topic this week; what the top videos/titles look like (gap?); verify every fact the copy will state against a primary source (docs, papers, vendor documentation).
3. Curate: drop noise (other meanings of the words), keep phrases a learner types. Choose **1 primary + 3 secondary keywords**. Save `research_notes.md` (what you found, what you could NOT verify, the keyword decision).

## Rules
- **Never claim what you could not source.** If a claim is an illustration, say it is one.
- **Keywords first, brand last.** The first sentence of every caption/description is the primary keyword in plain English; ~125 characters show before "more".
- **YouTube title:** primary keyword in the first 40 chars, <= 60 chars, no hashtags.
- **YouTube description:** 150-250 words; line 1 = primary keyword sentence; 2-3 sentences using secondary keywords; 3 bullets of what the viewer learns; one question; exactly 3 specific hashtags.
- **YouTube tags:** fill the field to **470-500 characters** (`", ".join(tags)`), every tag describing THIS video.
- **Instagram caption:** line 1 = keyword claim (<= 125 chars); 2-4 short lines; save / send / question CTAs; one plain-text keyword line; **max 5 hashtags**, specific, never #fyp #viral #reels.
- **Alt text:** one sentence containing the primary + one secondary keyword.
- **Language:** write the metadata in one language (English by default; `kit_lint.py --allow-roman-hindi` relaxes the English-only check). Subtitles mirror the spoken language.
- **Strongest signals:** YouTube = stayed-to-watch and average % viewed; Instagram = shares, saves, then comments. The CTA asks for a send or save of THIS idea.
- **Schedule** at the slots your audience is awake; never two uploads on one platform within 12 h.

## Thumbnail A/B
- A (curiosity): `<name>_thumbnail.jpg` · B (bold claim): `<name>_thumbnail_b.jpg`. Covers are separate uploads, never part of the video.

## 📸 Instagram
**Caption**
```
<Primary keyword claim, <= 125 chars>

<2-4 short lines with the secondary keywords>

💾 Save this for <use case>
📤 Send it to a friend who <situation>
💬 <question> 👇

<primary> · <secondary 1> · <secondary 2> · <secondary 3> · <secondary 4>

Follow <@handle> for <promise>.

#<broad> #<format> #<topic> #<topic2> #<adjacent>
```
**Alt text:** `<one sentence with primary + one secondary keyword>`
**Pinned comment:** `<question>`
**Story after posting:** poll sticker: `<question>`
**Audio name:** `<creator> · <short topic>`
**Schedule:** `<day, time>`

## ▶️ YouTube Shorts
**Title:** `<primary keyword title, <= 60 chars>`
**Description**
```
<Primary keyword sentence.>

<Intro line if you want one.> <2-3 sentences using secondary keywords.>

In this Short:
- <what you learn, with a keyword>
- <what you learn, with a keyword>
- <what you learn, with a keyword>

<question> 👇

#<hashtag1> #<hashtag2> #<hashtag3>
```
**Tags:** `<tag, tag, ... 470-500 chars>`
**Subtitles:** `<name>.srt` · **Category:** <category> · **Audience:** not made for kids
**Schedule:** `<day, time>`

## 💼 LinkedIn
See `linkedin_post.md` (+ `linkedin_image.png` from `scripts/make_linkedin_image.py`).

## Sources
- <primary sources for every concept stated>

## After posting (growth checklist)
- [ ] Pin the question comment on every platform; reply to every comment in the first hour.
- [ ] Share to Story with the poll sticker.
- [ ] 48 h later log: YouTube stayed-to-watch % and average % viewed; Instagram views, shares, saves.
