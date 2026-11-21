#!/usr/bin/env python3
"""Publish-readiness checklist (the explainer's version of reel-edit's checkpoint-2 gates):  python3 -I publish_check.py <project_dir>
Lists what is done and what is missing before anything may go to Drive. It never uploads."""
import json, os, subprocess, sys
proj = os.path.abspath(sys.argv[1]); name = os.path.basename(proj); A = lambda *p: os.path.join(proj, *p); ok = True
def row(done, label, note=""):
    global ok; ok &= bool(done); print(("  [x] " if done else "  [ ] ") + label + (f"  {note}" if note else ""))
sc = json.load(open(A("scenes.json"), encoding="utf-8")); m = sc.get("meta", {}); print(f"publish readiness: {name}")
row(os.path.exists(A("renders", f"{name}_final.mp4")), "final video renders/<name>_final.mp4")
row(bool(m.get("headline")), "frame-0 headline (meta.headline)", "" if m.get("headline") else "add: {\"lines\": [\"Belief?\", \"Twist!\"], \"t1\": 2.3}")
row(os.path.exists(A("covers", "cover_a.jpg")) and os.path.exists(A("covers", "cover_b.jpg")), "covers A + B (make_cover.py)")
row(os.path.exists(A("renders", f"{name}.srt")), "subtitles .srt (make_srt.py)")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import config
kit = A("posting_kit.md"); here = os.path.dirname(os.path.abspath(__file__)); lints = [os.path.join(here, "kit_lint.py")]
extra = config.get("kit_lint"); lints += [extra] if extra and os.path.exists(extra) else []                      # optional extra linter from your own pipeline
if os.path.exists(kit):
    for lint in lints:      # run WITHOUT -I: a linter may import its sibling modules
        r = subprocess.run([sys.executable, lint, kit], capture_output=True, text=True, cwd=os.path.dirname(lint)); row(r.stdout.startswith("PASS"), f"posting kit passes {os.path.basename(lint)}", r.stdout.strip().replace("\n", " ")[:160])
else: row(False, "posting kit (posting_kit.md) + kit_lint PASS", "run seo_research.py first, English-only metadata, tags 470-500 chars")
row(os.path.exists(A("research_notes.md")) or os.path.exists(A("seo_research.json")), "keyword research saved (seo_research.json / research_notes.md)")
row(os.path.exists(A("linkedin_post.md")), "LinkedIn post (optional but recommended: linkedin_post.md + linkedin_image.png)")
f = A("assets", "facts.json"); fx = json.load(open(f)) if os.path.exists(f) else []
unc = [x for x in fx if x["status"] == "unchecked"]; row(not unc, "every on-screen number sourced or labelled", f"{len(unc)} unverified: " + ", ".join(str(x['value'])[:28] for x in unc[:4]) if unc else f"{len(fx)} facts registered")
row(os.path.exists(A("qa", "safe_sheet.jpg")), "safe-zone sheet reviewed (safe_zone_check.py)")
row(os.path.exists(A("assets", "music_credit.txt")), "music licence line recorded", open(A("assets", "music_credit.txt")).read().strip()[:90] if os.path.exists(A("assets", "music_credit.txt")) else "")
row(os.path.exists(A("assets", "voice_edit.json")), "voice cleanup report (assets/voice_edit.json) read")
print("\n" + ("READY: show the creator the video + covers; after they approve BOTH run upload_drive.sh --approved-video --approved-cover" if ok else "NOT READY: finish the unchecked items first") + "\nUploads: never before approval of the video AND the cover; new subfolder <drive_dest>/<reel>/ (re-edits in /vN/).")
sys.exit(0 if ok else 1)
