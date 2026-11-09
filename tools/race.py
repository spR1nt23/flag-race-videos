"""Vertical (1080x1920) country marble race generator.

Usage:
  python3 tools/race.py --seed 123 --theme world --out out.mp4 [--music music/x.mp3] [--json result.json]

Themes: world, europe, asia, americas, africa_me (Africa + Middle East).
A video = intro + 5 rounds (30 countries, 6 eliminated per round, final round of 6) + winner screen (~50 s).
"""
import argparse, json, math, os, random, subprocess, sys, shutil, tempfile
import cairo, pymunk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from countries import COUNTRIES

W, H, FPS = 1080, 1920, 30
R = 26
FINISH_Y = 1760
L, RX = 40, 1040            # play area x range
BLUE = (0.16, 0.55, 1.0)
GREEN = (0.15, 0.85, 0.2)
YELLOW = (1, 0.85, 0.15)
FONT = "DejaVu Sans"
NAME = {c: n for c, n in COUNTRIES}

REGIONS = {
    "europe": "tr de fr gb it es pt nl be ch at pl se no fi dk gr ua ro hr rs hu cz sk bg ie is al ba si ee lv lt az ge am".split(),
    "asia": "tr jp kr cn in id pk bd th vn ph my sg sa qa ae ir iq il jo lb kz uz mn np lk az ge am".split(),
    "americas": "us ca mx br ar co cl uy pe ve ec cu jm bo py pa cr do gt hn tt ht sv".split(),
    "africa_me": "eg ma dz tn ng gh sn ke et za cm sa qa ae ir iq jo lb tr il ly sd tz ug ci ml ao om kw bh ye sy".split(),
}
THEME_TITLE = {"world": "WORLD", "europe": "EUROPE", "asia": "ASIA", "americas": "AMERICAS", "africa_me": "AFRICA & MIDDLE EAST"}

_flag_cache = {}
def flag_img(code, size):
    k = (code, size)
    if k not in _flag_cache:
        _flag_cache[k] = cairo.ImageSurface.create_from_png(os.path.join(ROOT, "flags", f"{code}_{size}.png"))
    return _flag_cache[k]

def ordinal(n):
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"

# ---------------- courses (static segs, spinners, spawn box, bins) ----------------
def side_walls(y1=1600):
    return [((L, 240), (L, y1), 14), ((RX, 240), (RX, y1), 14)]

def channel(x0, x1, y0):
    return [((x0, y0), (x0, FINISH_Y), 14), ((x1, y0), (x1, FINISH_Y), 14)]

def pegs(rows, y0, dy, dx, xs=L + 90, xe=RX - 60, r=10):
    out = []
    for row in range(rows):
        off = 0 if row % 2 == 0 else dx / 2
        x = xs + off
        while x < xe:
            out.append(((x, y0 + row * dy), (x + 0.5, y0 + row * dy), 2 * r))
            x += dx
    return out

def c_funnel():
    s = side_walls(1150) + pegs(3, 520, 120, 140) + [((L, 1100), (450, 1450), 14), ((RX, 1100), (630, 1450), 14)] + channel(450, 630, 1450)
    return s, [], [(450, 630)], "FUNNEL"

def c_plinko():
    s = side_walls(1450) + pegs(9, 470, 100, 120) + [((L, 1400), (420, 1560), 14), ((RX, 1400), (660, 1560), 14)] + channel(420, 660, 1560)
    return s, [], [(420, 660)], "PLINKO"

def c_spinners():
    s = side_walls(1400) + [((L, 1350), (450, 1560), 14), ((RX, 1350), (630, 1560), 14)] + channel(450, 630, 1560)
    sp = [(300, 620, 330, 4, 1.8), (780, 620, 330, 4, -1.8), (540, 920, 300, 3, 2.3), (300, 1200, 300, 4, -1.6), (780, 1200, 300, 4, 1.6)]
    return s, sp, [(450, 630)], "SPINNERS"

def c_cups():
    s = [((L, 240), (L, 450), 14), ((RX, 240), (RX, 450), 14), ((L, 450), (90, 600), 14), ((RX, 450), (990, 600), 14)]
    for cx in (240, 540, 840):
        s += [((cx - 150, 600), (cx - 58, 790), 14), ((cx + 58, 790), (cx + 150, 600), 14)]
    s += pegs(2, 470, 0.1, 300, xs=240, xe=900)
    s += [((L, 850), (L, 1100), 14), ((RX, 850), (RX, 1100), 14),
          ((L, 1100), (470, 1450), 14), ((RX, 1100), (610, 1450), 14)] + channel(470, 610, 1450)
    s += pegs(1, 1000, 1, 150, xs=240, xe=900)
    return s, [], [(470, 610)], "CUPS"

def c_zigzag():
    s = [((L, 240), (L, FINISH_Y), 14), ((RX, 240), (RX, FINISH_Y), 14),
         ((L, 380), (860, 640), 14), ((RX, 720), (220, 980), 14),
         ((L, 1060), (860, 1320), 14), ((RX, 1400), (220, 1660), 14)]
    return s, [], [(L, 220)], "ZIGZAG"

def c_hourglass():
    s = side_walls(1200) + [((L, 520), (440, 800), 14), ((RX, 520), (640, 800), 14),
                            ((L, 1150), (470, 1450), 14), ((RX, 1150), (610, 1450), 14)] + channel(470, 610, 1450)
    s += pegs(2, 950, 110, 160, xs=150)
    return s, [(540, 1060, 280, 2, 2.6)], [(470, 610)], "HOURGLASS"

COURSES = [c_funnel, c_plinko, c_spinners, c_cups, c_zigzag, c_hourglass]

# ---------------- drawing ----------------
def text(ctx, s, x, y, size, rgb=(1, 1, 1), align="left", alpha=1.0, outline=False):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    if align == "center": x -= ext.x_advance / 2
    elif align == "right": x -= ext.x_advance
    if outline:
        ctx.move_to(x, y); ctx.text_path(s); ctx.set_source_rgba(0, 0, 0, alpha); ctx.set_line_width(size / 7); ctx.stroke()
    ctx.move_to(x, y); ctx.set_source_rgba(*rgb, alpha); ctx.show_text(s)
    return ext.x_advance

def fit_text(ctx, s, x, y, size, maxw, **kw):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    while ctx.text_extents(s).x_advance > maxw and size > 20:
        size -= 2; ctx.set_font_size(size)
    return text(ctx, s, x, y, size, **kw)

def flag(ctx, code, x, y, r, alpha=1.0):
    img = flag_img(code, 256 if r > 40 else 64)
    sc = 2 * r / img.get_width()
    ctx.save(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.clip()
    ctx.translate(x - r, y - r); ctx.scale(sc, sc)
    ctx.set_source_surface(img, 0, 0); ctx.paint_with_alpha(alpha); ctx.restore()
    ctx.set_line_width(2); ctx.set_source_rgba(0, 0, 0, 0.55 * alpha)
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.stroke()

def border(ctx):
    ctx.set_source_rgb(*BLUE); ctx.set_line_width(18); ctx.rectangle(9, 9, W - 18, H - 18); ctx.stroke()

def new_frame():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_source_rgb(0, 0, 0); ctx.paint()
    return surf, ctx

class Enc:
    def __init__(self, path):
        self.path = path; self.tmp = path[:-4] + ".tmp.mp4"
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "21", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", self.tmp], stdin=subprocess.PIPE)
        self.n = 0
    def put(self, surf): self.p.stdin.write(bytes(surf.get_data())); self.n += 1
    def close(self):
        self.p.stdin.close()
        if self.p.wait() != 0: raise RuntimeError("ffmpeg failed")
        os.replace(self.tmp, self.path)

# ---------------- scenes ----------------
def run_round(ri, nrounds, course_fn, alive, n_elim, rng, enc, snap=None):
    segs, spinners, bins, cname = course_fn()
    space = pymunk.Space(); space.gravity = (0, 1700)
    for a, b, t in segs:
        sh = pymunk.Segment(space.static_body, a, b, t / 2); sh.elasticity = 0.45; sh.friction = 0.25; space.add(sh)
    spin = []
    for cx, cy, ln, arms, om in spinners:
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC); body.position = (cx, cy); body.angular_velocity = om * rng.choice([1, -1])
        shs = []
        for k in range(arms):
            ang = 2 * math.pi * k / arms
            sh = pymunk.Segment(body, (0, 0), (ln / 2 * math.cos(ang), ln / 2 * math.sin(ang)), 8); sh.elasticity = 0.5; sh.friction = 0.4
            shs.append(sh)
        space.add(body, *shs); spin.append((body, ln, arms))
    order = alive[:]; rng.shuffle(order)
    sx0, sx1 = (L + 30, 840) if cname == "ZIGZAG" else (L + 30, RX - 30)
    cols = int((sx1 - sx0) // (2 * R + 6))
    gate_y = 245 + ((len(order) - 1) // cols + 1) * (2 * R + 4) + 6
    gate = pymunk.Segment(space.static_body, (L, gate_y), (RX, gate_y), 4); space.add(gate)
    marbles = {}
    for i, c in enumerate(order):
        x = sx0 + R + (i % cols) * (2 * R + 6) + rng.uniform(-3, 3)
        y = gate_y - R - 4 - (i // cols) * (2 * R + 4)
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, R)); b.position = (x, y)
        sh = pymunk.Circle(b, R); sh.elasticity = 0.45; sh.friction = 0.2
        space.add(b, sh); marbles[c] = [b, sh, 0.0]
    final = n_elim == 0
    n_go = len(alive) if final else len(alive) - n_elim
    finished, t, gate_open, sub = [], 0.0, False, 4
    dt = 1 / (FPS * sub)
    while True:
        if not gate_open and t > 0.9: space.remove(gate); gate_open = True
        for _ in range(sub): space.step(dt)
        t += 1 / FPS
        for c, m in list(marbles.items()):
            b = m[0]
            if b.position.y > FINISH_Y + R:
                finished.append(c); space.remove(b, m[1]); del marbles[c]; continue
            if not (0 < b.position.x < W) or b.position.y < 0:
                b.position = (540, 300); b.velocity = (0, 0)
            m[2] = m[2] + 1 / FPS if gate_open and b.velocity.length < 30 else 0
            if m[2] > 0.8:
                b.apply_impulse_at_local_point((rng.uniform(-500, 500), -rng.uniform(500, 800))); m[2] = 0
        surf, ctx = new_frame()
        for x0, x1 in bins:
            ctx.set_source_rgb(*GREEN); ctx.rectangle(x0, FINISH_Y, x1 - x0, 60); ctx.fill()
        ctx.set_source_rgb(*BLUE); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for a, b, th in segs:
            ctx.set_line_width(th); ctx.move_to(*a); ctx.line_to(*b); ctx.stroke()
        ctx.set_line_width(16)
        for body, ln, arms in spin:
            for k in range(arms):
                ang = body.angle + 2 * math.pi * k / arms
                ctx.move_to(*body.position); ctx.line_to(body.position.x + ln / 2 * math.cos(ang), body.position.y + ln / 2 * math.sin(ang)); ctx.stroke()
        if not gate_open:
            ctx.set_source_rgb(0.9, 0.9, 0.9); ctx.set_line_width(5); ctx.move_to(L, gate_y); ctx.line_to(RX, gate_y); ctx.stroke()
        for c, m in marbles.items():
            flag(ctx, c, m[0].position.x, m[0].position.y, R)
        border(ctx)
        label = "FINAL ROUND" if final else f"ROUND {ri + 1}/{nrounds}"
        text(ctx, label, W / 2, 120, 64, align="center", rgb=YELLOW if final else (1, 1, 1))
        if final:
            text(ctx, "First to finish wins!", W / 2, 190, 40, align="center", rgb=(0.7, 1, 0.7))
        else:
            text(ctx, f"Top {n_go} qualify  -  {len(finished)}/{n_go}", W / 2, 190, 40, align="center", rgb=(0.7, 1, 0.7))
        text(ctx, "Comment your country!", W / 2, 1880, 44, align="center", rgb=(0.85, 0.85, 0.85))
        enc.put(surf)
        if snap is not None and enc.n in snap: surf.write_to_png(f"snap_{ri + 1}_{enc.n}.png")
        if final and len(finished) >= 1 and t > 1.5 and (len(finished) >= n_go or t > 13): break
        if not final and (len(finished) >= n_go or t > 14): break
    for _ in range(int(FPS * 0.4)): enc.put(surf)
    rest = sorted(marbles, key=lambda c: -marbles[c][0].position.y)
    allr = finished + rest
    return allr[:n_go] if not final else allr, allr[n_go:]

def results_card(enc, ri, elim, start_place):
    for f in range(int(FPS * 2.8)):
        surf, ctx = new_frame()
        a = min(1, f / 8)
        text(ctx, f"ROUND {ri + 1}", W / 2, 300, 70, align="center", alpha=a)
        text(ctx, "ELIMINATED", W / 2, 400, 80, rgb=(1, 0.3, 0.3), align="center", alpha=a)
        for i, c in enumerate(elim):
            al = max(0, min(1, (f - 8 - i * 5) / 6))
            y = 560 + i * 170
            text(ctx, ordinal(start_place + i), 230, y + 20, 56, rgb=(0.8, 0.8, 0.8), align="right", alpha=al)
            flag(ctx, c, 320, y, 55, alpha=al)
            fit_text(ctx, NAME[c], 400, y + 20, 60, 620, rgb=(0.9, 0.9, 0.9), alpha=al)
        border(ctx)
        enc.put(surf)

def intro(enc, alive, theme):
    for f in range(int(FPS * 2.5)):
        surf, ctx = new_frame()
        a = min(1, f / 8)
        text(ctx, "WHICH COUNTRY", W / 2, 300, 96, align="center", alpha=a)
        text(ctx, "WINS?", W / 2, 420, 120, align="center", rgb=YELLOW, alpha=a)
        text(ctx, f"{THEME_TITLE[theme]} MARBLE RACE", W / 2, 520, 50, align="center", rgb=(0.6, 0.85, 1), alpha=a)
        cols = 6
        for i, c in enumerate(alive):
            al = max(0, min(1, (f - i * 0.8) / 5))
            flag(ctx, c, 150 + (i % cols) * 156, 700 + (i // cols) * 160, 60, alpha=al)
        text(ctx, f"{len(alive)} countries  -  1 winner", W / 2, 1560, 56, align="center", alpha=a)
        text(ctx, "Comment your country!", W / 2, 1680, 56, align="center", rgb=(0.7, 1, 0.7), alpha=a)
        border(ctx)
        enc.put(surf)

def outro(enc, ranking):
    w = ranking[0]
    for f in range(int(FPS * 4.5)):
        surf, ctx = new_frame()
        p = min(1, f / 15); e = 1 - (1 - p) ** 3
        text(ctx, "WINNER", W / 2, 330, 120, rgb=YELLOW, align="center", alpha=p)
        flag(ctx, w, W / 2, 700, 60 + 180 * e)
        fit_text(ctx, NAME[w], W / 2, 1080, 110, 960, align="center", alpha=p)
        for i, c in enumerate(ranking[1:3]):
            al = max(0, min(1, (f - 25 - i * 8) / 8))
            y = 1260 + i * 150
            text(ctx, ordinal(i + 2), 250, y + 20, 60, rgb=(0.8, 0.8, 0.8), align="right", alpha=al)
            flag(ctx, c, 340, y, 52, alpha=al)
            fit_text(ctx, NAME[c], 420, y + 20, 60, 600, rgb=(0.85, 0.85, 0.85), alpha=al)
        al = max(0, min(1, (f - 50) / 10))
        text(ctx, "Subscribe for the next race!", W / 2, 1700, 56, rgb=(1, 0.4, 0.4), align="center", alpha=al)
        border(ctx)
        enc.put(surf)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--theme", default="world", choices=["world"] + list(REGIONS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--music", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--snap", default="")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    pool = [c for c, _ in COUNTRIES] if a.theme == "world" else REGIONS[a.theme][:]
    n = min(30, len(pool))
    alive = rng.sample(pool, n)
    nrounds = 5
    k = n - 6                      # eliminated before the final, spread over 4 rounds
    elims = [k // 4 + (1 if i < k % 4 else 0) for i in range(4)] + [0]
    courses = rng.sample(COURSES, nrounds) if nrounds <= len(COURSES) else [rng.choice(COURSES) for _ in range(nrounds)]
    snap = {int(x) for x in a.snap.split(",") if x} or None
    tmp = tempfile.mkdtemp(prefix="race_")
    parts = []
    e = Enc(os.path.join(tmp, "00.mp4")); intro(e, alive, a.theme); e.close(); parts.append(e.path)
    place_bottom, ranking, log = len(alive), None, []
    for ri in range(nrounds):
        e = Enc(os.path.join(tmp, f"{ri + 1:02d}.mp4"))
        safe, elim = run_round(ri, nrounds, courses[ri], alive, elims[ri], rng, e, snap)
        if elims[ri]:
            results_card(e, ri, elim, place_bottom - len(elim) + 1)
            place_bottom -= len(elim); alive = [c for c in alive if c in safe]
            log.append({"round": ri + 1, "eliminated": [NAME[c] for c in elim]})
        else:
            ranking = safe
        e.close(); parts.append(e.path)
    e = Enc(os.path.join(tmp, "99.mp4")); outro(e, ranking); e.close(); parts.append(e.path)
    with open(os.path.join(tmp, "list.txt"), "w") as fh:
        for p in parts: fh.write(f"file '{p}'\n")
    silent = os.path.join(tmp, "silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"), "-c", "copy", silent], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", silent]))
    out_tmp = a.out[:-4] + ".tmp.mp4"
    if a.music:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", a.music,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-af", f"afade=t=in:d=0.3,afade=t=out:st={dur - 1.5:.2f}:d=1.5", "-t", f"{dur:.3f}", out_tmp], check=True)
    else:
        shutil.copy(silent, out_tmp)
    os.replace(out_tmp, a.out)
    shutil.rmtree(tmp)
    res = {"seed": a.seed, "theme": a.theme, "countries": n, "winner": NAME[ranking[0]],
           "podium": [NAME[c] for c in ranking[:3]], "duration": round(dur, 1),
           "courses": [c.__name__[2:] for c in courses], "music": os.path.basename(a.music) if a.music else None, "rounds": log}
    if a.json:
        with open(a.json, "w") as fh: json.dump(res, fh, indent=1, ensure_ascii=False)
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()
