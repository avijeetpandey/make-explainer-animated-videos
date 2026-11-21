# Your audio libraries (not shipped: bring tracks you are allowed to use)

```
library/
  music/            drop .mp3/.wav tracks here, then:  python3 -I scripts/build_music_index.py library/music
  sfx/              optional. Sub-folders named after roles: whip/ hit_soft/ impact/ riser/ pop/ tick/ click/ notif/ success/ error/ negation/
```
Or point `music_dir` / `sfx_dir` in `config.local.json` at libraries you already have. Without an SFX library the skill synthesises a small original set (`scripts/make_sfx.py`); without a music library the video is built without music and says so.

**Licences are yours to check.** Free, no-attribution sources: [Mixkit](https://mixkit.co/license/) (free licence), the YouTube Audio Library (tracks marked "Attribution not required"), [Pixabay Music](https://pixabay.com/service/license-summary/). Put the licence line in the index (`--meta meta.json`): it is copied to `assets/music_credit.txt` for every video. Never use a streaming platform's in-app music.
