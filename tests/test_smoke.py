import importlib.util, json, os, shutil, subprocess, sys, tempfile, unittest, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); K = os.path.dirname(HERE); S = os.path.join(K, "scripts"); sys.path.insert(0, S)


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(S, name + ".py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


class T(unittest.TestCase):
    def test_everything_compiles(self):
        for f in os.listdir(S):
            if f.endswith(".py"): compile(open(os.path.join(S, f), encoding="utf-8").read(), f, "exec")
        r = subprocess.run(["node", "--check", os.path.join(S, "engine.js")], capture_output=True); self.assertEqual(r.returncode, 0, r.stderr)

    def test_tokens_markers_and_punctuation(self):
        b = load("build_explainer")
        t = b.tokens("It is *load balancer*, and _fast_ ^ok^ now.")
        self.assertEqual([x[0] for x in t], ["It", "is", "load", "balancer,", "and", "fast", "ok", "now."])
        self.assertTrue(t[2][1] and t[3][1] and not t[1][1]); self.assertTrue(t[5][2]); self.assertTrue(t[6][3])

    def test_fuzzy_align_survives_spelling_drift(self):
        b = load("build_explainer"); S_ = ["kyu", "dikhne", "lagti", "hai"]; A = [(1.0, 1.2, "kyun"), (1.2, 1.6, "dikhne"), (1.6, 1.9, "lakti"), (1.9, 2.0, "hai.")]
        t, cov = b.fuzzy_align(S_, A); self.assertGreaterEqual(cov, .75); self.assertEqual(t[1], 1.2)

    def test_island_times_monotonic_and_inside(self):
        b = load("build_explainer"); script = [(w, False, False, False, 0) for w in "ek do teen. char paanch chhe,".split()]
        isl = [(0.1, 1.2), (1.5, 3.0)]; t = b.island_times(script, isl)
        self.assertEqual(len(t), 6); self.assertEqual(t, sorted(t)); self.assertTrue(0.05 <= t[0] <= 1.3 and t[-1] <= 3.1)

    def test_kit_lint(self):
        good = "**Title:** `Object Pooling Explained`\n**Tags:** `%s`\n**Caption**\n```\nhello\n#a #b\n```\n**Description**\n```\nworld\n#a #b #c\n```\n" % ", ".join(["tag number %d" % i for i in range(34)])[:480]
        p = os.path.join(tempfile.mkdtemp(), "k.md"); open(p, "w").write(good)
        r = subprocess.run([sys.executable, os.path.join(S, "kit_lint.py"), p], capture_output=True, text=True); self.assertIn("PASS", r.stdout, r.stdout)
        open(p, "w").write(good.replace("hello", "yeh kya hai bhai")); r = subprocess.run([sys.executable, os.path.join(S, "kit_lint.py"), p], capture_output=True, text=True); self.assertIn("FAIL", r.stdout)

    def test_config_env_override(self):
        c = load("config"); os.environ["EXPLAINER_HANDLE"] = "@test"; self.assertEqual(c.get("handle"), "@test"); del os.environ["EXPLAINER_HANDLE"]

    def test_worlds_have_required_keys(self):
        w = json.load(open(os.path.join(K, "assets", "worlds.json")))
        for n, d in w.items():
            for k in ("bg", "glow", "tones", "caption", "overlay", "trans"): self.assertIn(k, d, n)
            self.assertEqual(set(d["tones"]), {"white", "red", "blue", "yellow", "green", "violet"})

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg needed")
    def test_clean_voice_caps_long_pauses(self):
        cv = load("clean_voice"); sr = 48000; rng = np.random.default_rng(1)
        def talk(sec):
            t = np.arange(int(sec * sr)) / sr; env = (np.sin(2 * np.pi * 3.5 * t) ** 2) * .6 + .1; return (np.sin(2 * np.pi * 140 * t) * env * .35 + rng.standard_normal(len(t)) * .01)
        quiet = lambda s: rng.standard_normal(int(s * sr)) * .0015
        x = np.r_[quiet(.4), talk(1.2), quiet(.9), talk(1.2), quiet(1.1), talk(1.0), quiet(.5)]
        d = tempfile.mkdtemp(); w = wave.open(os.path.join(d, "voice.wav"), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
        st, rem = cv.clean(d, chain=False); self.assertLess(st["clean_s"], st["original_s"] - 1.0); self.assertLessEqual(st["longest_pause_after_s"], .32); self.assertGreaterEqual(st["pauses_capped"], 2)
        self.assertTrue(os.path.exists(os.path.join(d, "voice_clean.wav")))

    def test_builder_recleans_when_edit_list_is_missing(self):
        src = open(os.path.join(S, "build_explainer.py"), encoding="utf-8").read()
        self.assertIn('not os.path.exists(os.path.join(a, "voice_edit.json"))', src)     # regression: deleting assets/ used to crash the build


if __name__ == "__main__":
    unittest.main()
