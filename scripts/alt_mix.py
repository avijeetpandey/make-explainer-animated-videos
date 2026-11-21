#!/usr/bin/env python3
"""A/B another music bed in seconds, without re-rendering the picture.

  python3 -I alt_mix.py <project_dir> <track from the shared library, e.g. mixkit/hazy-after-hours-132.mp3> [picture.mp4]

Builds the same mix (same voice, same SFX, same level solver) with the other track, muxes it onto the existing picture and writes
<project>/renders/alt_<track>.mp4 plus the balance numbers. List candidates with:  python3 -I audio_lib.py --rank premium
(The picture's punches were snapped to the first track's beat grid; for the final pick, rebuild with meta.music_file so the grid matches.)"""
import json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import audio_lib
proj = os.path.abspath(sys.argv[1]); track = sys.argv[2]; a = os.path.join(proj, "assets")
pic = sys.argv[3] if len(sys.argv) > 3 else next((os.path.join(proj, "renders", f) for f in sorted(os.listdir(os.path.join(proj, "renders"))) if f.startswith("picture")), None)
plan = json.load(open(os.path.join(a, "audio_plan.json"))); tmp = os.path.join(proj, "_alt"); shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(os.path.join(tmp, "assets", "audio"), exist_ok=True); shutil.copytree(os.path.join(a, "audio", "sfx"), os.path.join(tmp, "assets", "audio", "sfx")); shutil.copy(os.path.join(a, "audio", "voice.wav"), os.path.join(tmp, "assets", "audio", "voice.wav"))
m = audio_lib.pick_music(plan["total"], os.path.basename(proj) + "__alt", force=track, out=os.path.join(tmp, "assets", "audio", "bgm.mp3"), log=False)
if not m: sys.exit("track not found in the library index: " + track)
plan["music"] = {"path": "assets/audio/bgm.mp3", **{k: v for k, v in m.items() if k != "beats"}}; json.dump(plan, open(os.path.join(tmp, "assets", "audio_plan.json"), "w"))
subprocess.run([sys.executable, "-I", os.path.join(HERE, "mix_audio.py"), tmp], check=True, capture_output=True)
r = json.load(open(os.path.join(tmp, "assets", "mix_report.json"))); name = os.path.basename(track).replace(".mp3", "")
out = os.path.join(proj, "renders", f"alt_{name}.mp4")
subprocess.run(["bash", os.path.join(HERE, "finalize.sh"), pic, out, os.path.join(tmp, "assets", "audio", "master.wav")], check=True, capture_output=True)
print(f"{out}\n  {track}: voice over music+SFX median {r['voice_over_music_sfx_db_median']} dB, min {r['voice_over_music_sfx_db_min']} dB, {r['lufs']} LUFS  (genre {m.get('genre')}, {m['bpm']} BPM)")
shutil.rmtree(tmp, ignore_errors=True)
