"""Channel avatar (800x800) and banner (2560x1440) for Flag Marble Race."""
import math, os, random, sys
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from race import flag, text, BLUE, GREEN, YELLOW, ROOT

def funnel(ctx, cx, top, w, gap, depth, lw):
    ctx.set_source_rgb(*BLUE); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx - w / 2, top); ctx.line_to(cx - gap / 2, top + depth); ctx.line_to(cx - gap / 2, top + depth + lw * 4); ctx.stroke()
    ctx.move_to(cx + w / 2, top); ctx.line_to(cx + gap / 2, top + depth); ctx.line_to(cx + gap / 2, top + depth + lw * 4); ctx.stroke()

def avatar(path):
    S = 800
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); ctx = cairo.Context(surf)
    ctx.set_source_rgb(0, 0, 0); ctx.paint()
    funnel(ctx, 400, 360, 620, 150, 220, 22)
    ctx.set_source_rgb(*GREEN); ctx.rectangle(325, 680, 150, 40); ctx.fill()
    pos = [(250, 270, "tr"), (350, 230, "us"), (455, 255, "br"), (555, 290, "de"), (300, 360, "jp"),
           (410, 345, "fr"), (515, 380, "gb"), (400, 470, "it"), (180, 200, "in"), (620, 200, "mx"), (400, 600, "kr")]
    for x, y, c in pos:
        flag(ctx, c, x, y, 52)
    surf.write_to_png(path)

def banner(path):
    Wb, Hb = 2560, 1440
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, Wb, Hb); ctx = cairo.Context(surf)
    ctx.set_source_rgb(0, 0, 0); ctx.paint()
    rng = random.Random(4)
    codes = "tr us br de jp fr gb it in mx kr es ar ca au eg ng za sa id pk nl se pl ua gr pt ch ma co".split()
    # flags spread across the full banner (TV area), sparser in the centre safe area
    for i in range(140):
        x, y = rng.uniform(40, Wb - 40), rng.uniform(40, Hb - 40)
        if 380 < x < 2180 and 420 < y < 1020: continue
        flag(ctx, rng.choice(codes), x, y, rng.uniform(28, 46), alpha=0.85)
    # safe area 1546x423 centred: (507,508)-(2053,931)
    ctx.set_source_rgba(0, 0, 0, 0.85); ctx.rectangle(500, 500, 1560, 440); ctx.fill()
    ctx.set_source_rgb(*BLUE); ctx.set_line_width(12); ctx.rectangle(500, 500, 1560, 440); ctx.stroke()
    text(ctx, "FLAG MARBLE RACE", Wb / 2, 685, 128, align="center")
    text(ctx, "Which country wins?  New races every day", Wb / 2, 810, 64, rgb=YELLOW, align="center")
    for i, c in enumerate("tr us br de jp fr gb in".split()):
        flag(ctx, c, Wb / 2 - 7 * 55 + i * 110, 880, 34)
    surf.write_to_png(path)

if __name__ == "__main__":
    out = os.path.join(ROOT, "branding"); os.makedirs(out, exist_ok=True)
    avatar(os.path.join(out, "avatar.png")); banner(os.path.join(out, "banner.png"))
    print("ok")
