"""Render one day's Shorts and write metadata.

  python3 tools/make_day.py 2026-11-10            # 3 videos -> videos/<date>/, content/<date>/metadata.json

Seeds come from the date, so re-running a date gives the same races (safe to resume).
"""
import glob, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLOTS = ["3:00 PM", "8:00 PM", "11:30 PM"]          # Istanbul time (Studio, English UI)
REGION_CYCLE = ["europe", "asia", "americas", "africa_me"]
TITLES = [
    "Which Country Wins This Marble Race?",
    "30 Countries, Only 1 Winner | Marble Race",
    "Will Your Country Survive? | Country Marble Race",
    "Can Your Country Make It To The End?",
    "Country Marble Elimination Race",
    "Only One Country Can Win This Race",
    "Guess The Winner Before The End!",
]
REGION_TITLES = {
    "europe": "Europe Marble Race - Which Country Wins?",
    "asia": "Asia Marble Race - Which Country Wins?",
    "americas": "Americas Marble Race - Which Country Wins?",
    "africa_me": "Africa & Middle East Marble Race - Who Wins?",
}

def main(date):
    h = int(hashlib.sha1(date.encode()).hexdigest(), 16)
    day_no = h % 10007
    vids = os.path.join(ROOT, "videos", date); os.makedirs(vids, exist_ok=True)
    cont = os.path.join(ROOT, "content", date); os.makedirs(cont, exist_ok=True)
    music = sorted(glob.glob(os.path.join(ROOT, "music", "*.mp3")) + glob.glob(os.path.join(ROOT, "music", "*.m4a")))
    themes = ["world", REGION_CYCLE[day_no % len(REGION_CYCLE)], "world"]
    meta = []
    for i, theme in enumerate(themes):
        seed = (h >> (i * 20)) % 1_000_000
        name = f"race{i + 1}_{theme}"
        out = os.path.join(vids, name + ".mp4")
        js = os.path.join(cont, name + ".json")
        cmd = [sys.executable, os.path.join(ROOT, "tools", "race.py"), "--seed", str(seed), "--theme", theme, "--out", out, "--json", js]
        if music:
            cmd += ["--music", music[(day_no + i) % len(music)]]
        if not (os.path.exists(out) and os.path.exists(js)):
            subprocess.run(cmd, check=True)
        res = json.load(open(js))
        title = REGION_TITLES[theme] if theme != "world" else TITLES[(day_no * 2 + i) % len(TITLES)]
        n = res["countries"]
        desc = (f"{n} countries race through {len(res['courses'])} rounds of obstacles - only one survives! "
                f"Which country were you cheering for? Comment your country and it might be in the next race.\n\n"
                f"#marblerace #countries #flags #countryballs #shorts ")
        meta.append({"file": name + ".mp4", "title": title, "description": desc, "time": SLOTS[i],
                     "winner": res["winner"], "music": res["music"], "duration": res["duration"]})
    json.dump(meta, open(os.path.join(cont, "metadata.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(meta, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1])
