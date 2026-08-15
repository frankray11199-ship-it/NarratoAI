#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《说谎的爱人》程序化影像渲染引擎
================================

完全离线：不依赖任何外部素材站、图库或生图接口。
每一帧画面由数学函数生成，每一个音符由加法合成产生。

视觉母题全部取自剧本伏笔：
    水中月 / 金缮裂纹 / 承重墙裂缝 / 沉戒 / 取景框 / 台风雨夜 /
    碎玻璃 / 金粉 / 慢四分钟的表 / 路灯 / 时间流逝

依赖: numpy, Pillow, ffmpeg(imageio-ffmpeg)
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 24

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

_font_cache = {}


def font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return _font_cache[size]


# ---------------------------------------------------------------- 工具

def grid():
    """归一化坐标网格，X∈[-1,1] 按宽高比拉伸，Y∈[0,1] 自上而下"""
    x = np.linspace(-W / H, W / H, W, dtype=np.float32)
    y = np.linspace(0.0, 1.0, H, dtype=np.float32)
    return np.meshgrid(x, y)


X, Y = grid()


def blank():
    return np.zeros((H, W, 3), dtype=np.float32)


def expose(img, gain=1.34, gamma=0.86, lift=0.012):
    """
    统一曝光：整体提亮 + 提伽马把暗部拉出来 + 微量黑电平抬升。
    首轮渲染全片偏暗、暗部细节埋没，此函数为统一校正。
    """
    y = np.clip(img, 0, None) * gain + lift
    return np.clip(y, 0, 1.0) ** gamma


def to_rgb(lum, color=(1.0, 1.0, 1.0)):
    out = np.empty((H, W, 3), dtype=np.float32)
    for i in range(3):
        out[:, :, i] = lum * color[i]
    return out


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def fade(img, k):
    return img * float(np.clip(k, 0.0, 1.0))


def vignette(strength=0.55):
    r = np.sqrt((X / (W / H)) ** 2 + ((Y - 0.5) * 2) ** 2)
    return (1.0 - strength * np.clip(r - 0.35, 0, None) ** 1.6).astype(np.float32)


VIG = vignette()


_noise_cache = {}


def value_noise(scale, seed=0):
    """低频值噪声，用于水泥/纸张/胶片颗粒底纹"""
    key = (scale, seed)
    if key in _noise_cache:
        return _noise_cache[key]
    rng = np.random.default_rng(seed)
    small = rng.random((max(2, H // scale), max(2, W // scale))).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    n = np.asarray(img, dtype=np.float32) / 255.0
    _noise_cache[key] = n
    return n


def grain(t, amount=0.035):
    """胶片颗粒：随时间跳动"""
    rng = np.random.default_rng(int(t * 1000) % 99991)
    g = rng.standard_normal((H // 4, W // 4)).astype(np.float32)
    img = Image.fromarray(np.clip(g * 40 + 128, 0, 255).astype(np.uint8))
    img = img.resize((W, H), Image.BILINEAR)
    g2 = (np.asarray(img, dtype=np.float32) / 255.0 - 0.5) * amount
    return g2[:, :, None]


def pil_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def composite(base, layer_rgba, glow=0.0):
    """把 PIL RGBA 图层叠到 numpy 底图上，可选辉光"""
    arr = np.asarray(layer_rgba, dtype=np.float32) / 255.0
    rgb, a = arr[:, :, :3], arr[:, :, 3:4]
    out = base * (1 - a) + rgb * a
    if glow > 0:
        g = layer_rgba.filter(ImageFilter.GaussianBlur(28))
        ga = np.asarray(g, dtype=np.float32) / 255.0
        out = out + ga[:, :, :3] * ga[:, :, 3:4] * glow
    return out


# ---------------------------------------------------------------- 字幕排印

def text_card(lines, t, dur, size=58, gap=34, color=(238, 232, 222),
              y_center=0.5, align="center", track=6, fade_in=0.9, fade_out=0.9,
              small=None):
    """
    中文字幕卡。track = 字间距（排印感的关键）。
    返回 RGBA 图层与不透明度。
    """
    layer = pil_layer()
    d = ImageDraw.Draw(layer)
    f = font(size)

    a = smoothstep(0, fade_in, t) * (1 - smoothstep(dur - fade_out, dur, t))
    if a <= 0.002:
        return layer, 0.0

    heights = []
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=f)
        heights.append(bb[3] - bb[1])
    total = sum(heights) + gap * (len(lines) - 1)
    y = y_center * H - total / 2

    for ln, hh in zip(lines, heights):
        widths = [d.textbbox((0, 0), ch, font=f)[2] -
                  d.textbbox((0, 0), ch, font=f)[0] for ch in ln]
        lw = sum(widths) + track * (len(ln) - 1)
        if align == "center":
            x = (W - lw) / 2
        elif align == "left":
            x = W * 0.12
        else:
            x = W * 0.88 - lw
        for ch, cw in zip(ln, widths):
            d.text((x, y), ch, font=f, fill=color + (255,))
            x += cw + track
        y += hh + gap

    if small:
        fs = font(26)
        bb = d.textbbox((0, 0), small, font=fs)
        d.text(((W - (bb[2] - bb[0])) / 2, y + 26), small, font=fs,
               fill=(150, 145, 138, 255))

    return layer, float(a)


# ================================================================
#                          场景渲染器
# ================================================================

def sc_water_moon(t, dur, bright=1.0, moon_x=0.06, agitate=0.0):
    """水中月：全片母题。低机位，月光在洱海上碎成一片一片。"""
    y0 = 0.34                      # 地平线
    below = Y > y0
    depth = np.clip(Y - y0, 1e-3, None)
    persp = 1.0 / (depth * 2.6 + 0.035)

    sp = 1.0 + agitate * 2.0
    wave = (0.55 * np.sin(persp * 0.9 + t * 2.1 * sp)
            + 0.30 * np.sin(persp * 1.7 - t * 1.55 * sp + X * 3.1)
            + 0.18 * np.sin(persp * 3.3 + t * 3.4 * sp - X * 6.2)
            + 0.10 * np.sin(persp * 6.1 - t * 4.7 * sp + X * 11.0))
    wave += agitate * 0.35 * np.sin(persp * 9.0 + t * 8.0)

    colw = 0.05 + depth * 1.35
    col = np.exp(-((X - moon_x) ** 2) / (colw ** 2 + 1e-6))

    spec = np.clip(wave, 0, None) ** 2.6
    water = col * spec * 2.35 + col * 0.10 + 0.022
    water *= smoothstep(y0, y0 + 0.03, Y)

    sky = np.exp(-((Y - y0) ** 2) / 0.006) * 0.05 + 0.014 * (1 - Y / y0)
    lum = np.where(below, water, np.clip(sky, 0, None))

    # 月亮本体
    mx, my = moon_x, y0 - 0.16
    r = np.sqrt((X - mx) ** 2 + ((Y - my) * 1.0) ** 2)
    disk = smoothstep(0.052, 0.043, r)
    halo = np.exp(-(r ** 2) / 0.02) * 0.28
    lum = lum + np.where(below, 0, disk * 0.95 + halo)

    img = to_rgb(lum * bright, (0.80, 0.86, 1.0))
    img *= VIG[:, :, None]
    return img + grain(t)


_crack_cache = {}


def _crack_paths(seed, n_main, spread, length, origin=(0.0, 0.0), branch=True):
    """递归生成裂纹折线（金缮 / 玻璃 / 墙体共用）"""
    key = (seed, n_main, spread, length, origin, branch)
    if key in _crack_cache:
        return _crack_cache[key]
    rng = np.random.default_rng(seed)
    paths = []

    def walk(p, ang, steps, wid, depth_):
        pts = [p]
        for i in range(steps):
            ang += rng.normal(0, spread)
            step = length * (0.55 + rng.random() * 0.9)
            p = (p[0] + np.cos(ang) * step, p[1] + np.sin(ang) * step)
            pts.append(p)
            if branch and depth_ < 3 and rng.random() < 0.16:
                walk(p, ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1),
                     max(3, steps - i - 4), wid * 0.55, depth_ + 1)
        paths.append((pts, wid))

    for k in range(n_main):
        a = (k / n_main) * 2 * np.pi + rng.normal(0, 0.4)
        walk(origin, a, rng.integers(14, 26), 1.0, 0)
    _crack_cache[key] = paths
    return paths


def sc_kintsugi(t, dur):
    """金缮：瓷碗的裂缝被金一寸一寸填满。'裂缝修不掉，只能让它好看一点'"""
    base = to_rgb(0.055 + value_noise(70, 3) * 0.03, (1.0, 0.97, 0.92))

    cx, cy = W * 0.5, H * 0.54
    R = 360

    bowl = pil_layer()
    d = ImageDraw.Draw(bowl)
    d.ellipse([cx - R, cy - R * 0.86, cx + R, cy + R * 0.86],
              fill=(168, 167, 161, 255))
    d.ellipse([cx - R * 0.93, cy - R * 0.80, cx + R * 0.93, cy + R * 0.80],
              fill=(140, 143, 141, 255))
    bowl = bowl.filter(ImageFilter.GaussianBlur(1.2))
    img = composite(base, bowl)

    # 釉面反光（收窄，避免碗心过曝把金线吃掉）
    img *= (0.86 + 0.20 * np.exp(-(((X + 0.26) ** 2 + (Y - 0.34) ** 2)) / 0.022))[:, :, None]

    prog = smoothstep(0.15, 0.80, t / dur)
    paths = _crack_paths(11, 5, 0.55, 34.0, origin=(cx - 40, cy - 30))

    def clamp_bowl(px, py):
        """把裂纹约束在碗内——裂缝不该长到碗外面去"""
        ex, ey = (px - cx) / (R * 0.90), (py - cy) / (R * 0.77)
        d = np.sqrt(ex * ex + ey * ey)
        if d > 1.0:
            px, py = cx + (px - cx) / d, cy + (py - cy) / d
        return float(px), float(py)

    gold = pil_layer()
    gd = ImageDraw.Draw(gold)
    for pts, wid in paths:
        n = max(2, int(len(pts) * prog))
        seg = [clamp_bowl(px, py) for px, py in pts[:n]]
        if len(seg) > 1:
            gd.line(seg, fill=(222, 176, 80, 255), width=max(3, int(11 * wid)),
                    joint="curve")
    img = composite(img, gold, glow=0.55)

    img *= VIG[:, :, None]
    return img * 0.92 + grain(t)


def sc_wall_crack(t, dur):
    """承重墙：0.15mm → 0.28mm。结构失效不是一下子的，是累计的。"""
    n = value_noise(40, 7) * 0.5 + value_noise(9, 8) * 0.25
    base = to_rgb(0.46 + n * 0.30, (0.86, 0.86, 0.84))
    base *= (0.72 + 0.55 * np.exp(-((X - 0.5) ** 2) / 0.9))[:, :, None]

    p = t / dur
    grow = smoothstep(0.05, 0.95, p)

    layer = pil_layer()
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(5)
    x, y = W * 0.46, -20.0
    pts = [(x, y)]
    while y < H + 20:
        x += rng.normal(0, 26)
        y += rng.uniform(26, 52)
        pts.append((x, y))
    npts = max(2, int(len(pts) * grow))
    wid = 2 + 9 * grow
    d.line(pts[:npts], fill=(18, 16, 15, 255), width=int(wid), joint="curve")
    for i in range(1, npts - 1, 3):
        px, py = pts[i]
        bl = rng.uniform(30, 90) * grow
        ba = rng.uniform(-1.2, 1.2)
        d.line([(px, py), (px + np.cos(ba) * bl, py + np.sin(ba) * bl)],
               fill=(30, 27, 25, 255), width=max(1, int(wid * 0.35)))
    img = composite(base, layer)

    # 检测标注
    meas = pil_layer()
    md = ImageDraw.Draw(meas)
    val = 0.15 + 0.13 * grow
    md.text((W * 0.64, H * 0.26), "%.2f mm" % val, font=font(52),
            fill=(228, 60, 44, 240))
    md.line([(W * 0.62, H * 0.28), (W * 0.52, H * 0.34)],
            fill=(228, 60, 44, 200), width=2)
    md.text((W * 0.64, H * 0.33), "裂缝宽度 · 累计观测", font=font(24),
            fill=(200, 90, 78, 200))
    img = composite(img, meas)

    img *= VIG[:, :, None]
    return img * 0.85 + grain(t)


def sc_ring_sink(t, dur):
    """沉戒：2024年4月9日，洱海。她捞了三次。"""
    p = t / dur
    dep = smoothstep(0, 1, p)

    top = 0.20 * (1 - dep * 0.70)
    lum = (top * (1 - Y * 0.80) + 0.018)
    caus = (np.sin(X * 7 + t * 1.6) * np.sin(Y * 11 - t * 1.1)
            + np.sin(X * 13 - t * 2.2) * np.sin(Y * 7 + t * 1.4))
    lum = lum + np.clip(caus, 0, None) ** 2 * 0.12 * (1 - dep * 0.8) * (1 - Y)
    img = to_rgb(lum, (0.42, 0.66, 0.72))

    ring = pil_layer()
    rd = ImageDraw.Draw(ring)
    ry = H * (0.16 + 0.72 * dep)
    rr = 62 * (1 - 0.55 * dep)
    rx = W * 0.5 + np.sin(t * 2.3) * 26 * (1 - dep)
    squash = 0.30 + 0.42 * np.abs(np.sin(t * 1.7))
    alpha = int(255 * (1 - dep * 0.82))
    rd.ellipse([rx - rr, ry - rr * squash, rx + rr, ry + rr * squash],
               outline=(232, 230, 224, alpha), width=max(2, int(9 * (1 - dep * 0.5))))
    img = composite(img, ring, glow=0.35)

    # 气泡
    bub = pil_layer()
    bd = ImageDraw.Draw(bub)
    rng = np.random.default_rng(21)
    for i in range(26):
        bx = rng.uniform(0.2, 0.8) * W
        by = H * (1.05 - ((t * rng.uniform(0.10, 0.26) + rng.random()) % 1.0) * 1.15)
        br = rng.uniform(2, 7)
        bd.ellipse([bx - br, by - br, bx + br, by + br],
                   outline=(210, 230, 235, 90), width=1)
    img = composite(img, bub)

    img *= VIG[:, :, None]
    return img + grain(t)


def sc_viewfinder(t, dur):
    """取景框：框里的东西你看着最真，其实全是我挑出来的。"""
    bg = to_rgb(0.10 + value_noise(120, 13) * 0.16, (0.55, 0.58, 0.66))
    figure = np.exp(-(((X - 0.05) ** 2) / 0.10 + ((Y - 0.58) ** 2) / 0.16))
    bg = bg + to_rgb(figure * 0.20, (0.85, 0.80, 0.74))
    bg *= (0.5 + 0.6 * np.exp(-((Y - 0.5) ** 2) / 0.30))[:, :, None]

    ui = pil_layer()
    d = ImageDraw.Draw(ui)
    m, L = 150, 90
    c = (226, 224, 218, 210)
    for (ax, ay, dx, dy) in [(m, m, 1, 1), (W - m, m, -1, 1),
                             (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(ax, ay), (ax + dx * L, ay)], fill=c, width=3)
        d.line([(ax, ay), (ax, ay + dy * L)], fill=c, width=3)

    # 对焦框：游移后锁定
    lock = smoothstep(0.45, 0.75, t / dur)
    fx = W * 0.52 + (1 - lock) * np.sin(t * 3.1) * 130
    fy = H * 0.52 + (1 - lock) * np.cos(t * 2.3) * 80
    s = 110 - 26 * lock
    fc = (90, 220, 130, 230) if lock > 0.6 else (226, 224, 218, 150)
    d.rectangle([fx - s, fy - s * 0.7, fx + s, fy + s * 0.7], outline=fc, width=2)

    d.text((m, H - m + 22), "f/1.4    1/60    ISO 400", font=font(30),
           fill=(210, 208, 202, 190))
    d.text((W - m - 210, H - m + 22), "DALI  04/23", font=font(30),
           fill=(210, 208, 202, 190))
    if int(t * 2) % 2 == 0:
        d.ellipse([m + 6, m - 46, m + 26, m - 26], fill=(220, 60, 50, 230))
        d.text((m + 38, m - 52), "REC", font=font(28), fill=(220, 60, 50, 230))
    img = composite(bg, ui)

    # 快门叶片闭合
    sh = np.clip((t - (dur - 0.55)) / 0.30, 0, 1)
    if sh > 0:
        e = smoothstep(0, 1, sh)
        mask = ((Y < e * 0.52) | (Y > 1 - e * 0.52)).astype(np.float32)
        img *= (1 - mask)[:, :, None]

    img *= VIG[:, :, None]
    return img + grain(t, 0.05)


def sc_rain_night(t, dur):
    """台风"海棠"登陆夜：停电，一根蜡烛。"""
    lum = 0.030 + 0.05 * np.exp(-((Y - 0.2) ** 2) / 0.5)
    img = to_rgb(lum, (0.42, 0.50, 0.68))

    # 烛火
    fl = 0.72 + 0.28 * np.sin(t * 17) * np.sin(t * 6.3) + 0.12 * np.sin(t * 41)
    cxp, cyp = -0.42, 0.60
    r = np.sqrt((X - cxp) ** 2 + ((Y - cyp) * 1.15) ** 2)
    img += to_rgb(np.exp(-(r ** 2) / 0.16) * 0.55 * fl, (1.0, 0.66, 0.28))
    img += to_rgb(smoothstep(0.030, 0.012, r) * fl, (1.0, 0.85, 0.55))

    # 雨
    rain = pil_layer()
    rd = ImageDraw.Draw(rain)
    rng = np.random.default_rng(3)
    for i in range(340):
        sx = rng.random()
        sp = rng.uniform(0.9, 2.0)
        yy = ((t * sp + rng.random()) % 1.0)
        px = sx * W + yy * 90
        py = yy * (H + 220) - 110
        ln = rng.uniform(34, 96)
        al = int(rng.uniform(40, 120))
        rd.line([(px, py), (px + 16, py + ln)], fill=(190, 205, 235, al), width=1)
    img = composite(img, rain)

    img *= VIG[:, :, None]
    return img + grain(t, 0.05)


def sc_glass_break(t, dur):
    """暴力冲突：玻璃门碎了，架子上的器物哗啦倒下来。"""
    img = to_rgb(0.045 + value_noise(60, 17) * 0.05, (0.6, 0.62, 0.70))

    hit = smoothstep(0.0, 0.10, t / dur)
    paths = _crack_paths(31, 11, 0.34, 42.0, origin=(W * 0.47, H * 0.46))

    layer = pil_layer()
    d = ImageDraw.Draw(layer)
    for pts, wid in paths:
        n = max(2, int(len(pts) * hit))
        seg = [(float(a), float(b)) for a, b in pts[:n]]
        if len(seg) > 1:
            d.line(seg, fill=(232, 240, 250, 235), width=max(1, int(3 * wid)))
    img = composite(img, layer, glow=0.30)

    # 血色由中心渗出
    bleed = smoothstep(0.35, 1.0, t / dur)
    r = np.sqrt((X - 0.05) ** 2 + ((Y - 0.55)) ** 2)
    img += to_rgb(np.exp(-(r ** 2) / (0.05 + bleed * 0.35)) * 0.30 * bleed,
                  (0.75, 0.06, 0.05))

    shake = 5.0 * (1 - t / dur) ** 2
    if shake > 0.4:
        dx = int(np.sin(t * 57) * shake)
        img = np.roll(img, dx, axis=1)

    img *= VIG[:, :, None]
    return img + grain(t, 0.07)


def sc_gold_dust(t, dur):
    """她的右手抖得厉害。金粉撒了一桌子。"""
    img = to_rgb(0.035 + value_noise(80, 23) * 0.03, (0.9, 0.86, 0.80))

    rng = np.random.default_rng(77)
    N = 4200
    x0 = rng.normal(W * 0.5, 60, N)
    y0 = rng.normal(H * 0.30, 30, N)
    vx = rng.normal(0, 42, N)
    vy = rng.uniform(60, 230, N)
    ph = rng.random(N) * dur
    tt = np.clip(((t + ph) % dur), 0, None)
    px = x0 + vx * tt + np.sin(tt * 4 + ph) * 12
    py = y0 + vy * tt + 46 * tt * tt

    canvas = np.zeros((H, W), dtype=np.float32)
    ix = np.clip(px.astype(int), 0, W - 1)
    iy = np.clip(py.astype(int), 0, H - 1)
    inb = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    np.add.at(canvas, (iy[inb], ix[inb]), 1.0)
    blur = np.asarray(Image.fromarray(np.clip(canvas * 255, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(2.4)), dtype=np.float32) / 255.0
    img += to_rgb(blur * 3.4, (1.0, 0.78, 0.34))
    img += to_rgb(canvas * 1.3, (1.0, 0.92, 0.70))

    img *= VIG[:, :, None]
    return img + grain(t)


def sc_watch(t, dur):
    """这表其实一直没坏。是我八年前调错了一格，一直没改。"""
    img = to_rgb(0.045 + value_noise(90, 29) * 0.03, (0.8, 0.82, 0.88))

    cx, cy, R = W * 0.5, H * 0.5, 250
    layer = pil_layer()
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(24, 24, 26, 255),
              outline=(190, 186, 176, 255), width=6)
    for i in range(60):
        a = i * np.pi / 30 - np.pi / 2
        r1 = R * (0.86 if i % 5 == 0 else 0.92)
        wdt = 4 if i % 5 == 0 else 1
        d.line([(cx + np.cos(a) * r1, cy + np.sin(a) * r1),
                (cx + np.cos(a) * R * 0.97, cy + np.sin(a) * R * 0.97)],
               fill=(196, 192, 182, 255), width=wdt)

    p = t / dur
    corrected = smoothstep(0.55, 0.72, p)
    lag = (1 - corrected) * (4.0 / 60.0) * 2 * np.pi     # 慢四分钟
    mm = (t * 0.9) % 60
    am = mm / 60 * 2 * np.pi - np.pi / 2 - lag
    ah = (mm / 720) * 2 * np.pi - np.pi / 2 - lag / 12
    d.line([(cx, cy), (cx + np.cos(ah) * R * 0.52, cy + np.sin(ah) * R * 0.52)],
           fill=(232, 228, 218, 255), width=10)
    d.line([(cx, cy), (cx + np.cos(am) * R * 0.78, cy + np.sin(am) * R * 0.78)],
           fill=(232, 228, 218, 255), width=6)
    asec = (t * 6.0) % (2 * np.pi) - np.pi / 2
    d.line([(cx, cy), (cx + np.cos(asec) * R * 0.84, cy + np.sin(asec) * R * 0.84)],
           fill=(200, 70, 55, 255), width=2)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(200, 70, 55, 255))
    img = composite(img, layer, glow=0.10)

    img *= VIG[:, :, None]
    return img + grain(t)


def sc_streetlight(t, dur):
    """楼下那盏灯，他走那天，修好了。"""
    p = t / dur
    fixed = smoothstep(0.55, 0.70, p)
    rng = np.random.default_rng(int(t * 11))
    flick = 1.0 if rng.random() < 0.55 else 0.06
    flick = flick * (1 - fixed) + 1.0 * fixed

    img = to_rgb(0.022 + 0.02 * (1 - Y), (0.40, 0.46, 0.62))
    lx, ly = -0.30, 0.24
    r = np.sqrt((X - lx) ** 2 + ((Y - ly) * 1.2) ** 2)
    img += to_rgb(np.exp(-(r ** 2) / 0.10) * 0.55 * flick, (1.0, 0.80, 0.42))
    img += to_rgb(smoothstep(0.028, 0.010, r) * flick, (1.0, 0.95, 0.78))

    cone = np.clip(1 - np.abs(X - lx) / (0.06 + (Y - ly) * 0.6 + 1e-3), 0, 1)
    cone *= smoothstep(ly, ly + 0.05, Y) * (1 - Y * 0.5)
    img += to_rgb(cone * 0.10 * flick, (1.0, 0.84, 0.52))

    # 窗
    win = pil_layer()
    wd = ImageDraw.Draw(win)
    wd.rectangle([W * 0.66, H * 0.20, W * 0.80, H * 0.40],
                 fill=(255, 214, 150, int(70 * (1 - fixed) + 18)))
    wd.line([(W * 0.73, H * 0.20), (W * 0.73, H * 0.40)], fill=(20, 18, 16, 255), width=5)
    img = composite(img, win, glow=0.25)

    img *= VIG[:, :, None]
    return img + grain(t, 0.05)


def sc_years(t, dur):
    """八年下坠。"""
    img = to_rgb(0.028 + value_noise(100, 41) * 0.02, (0.7, 0.72, 0.78))
    p = t / dur
    years = ["2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033"]
    notes = ["离婚", "母亲去世", "瓷器厂 · 质检", "婚礼上远远看见他",
             "第三次搬家", "", "木箱摔了 · 没有打开", "辞职", "大理"]
    idx = min(len(years) - 1, int(p * len(years)))
    sub = p * len(years) - idx

    layer = pil_layer()
    d = ImageDraw.Draw(layer)
    a = int(255 * (smoothstep(0, 0.12, sub) * (1 - smoothstep(0.80, 1.0, sub))))
    f = font(150)
    bb = d.textbbox((0, 0), years[idx], font=f)
    d.text(((W - (bb[2] - bb[0])) / 2, H * 0.36), years[idx], font=f,
           fill=(226, 222, 214, a))
    if notes[idx]:
        f2 = font(42)
        bb2 = d.textbbox((0, 0), notes[idx], font=f2)
        d.text(((W - (bb2[2] - bb2[0])) / 2, H * 0.58), notes[idx], font=f2,
               fill=(168, 162, 154, a))
    img = composite(img, layer, glow=0.12)

    img *= VIG[:, :, None]
    return img + grain(t)


def sc_bowl_leak(t, dur):
    """碗粘好了。歪的。502 的痕迹亮得像疤。碗漏了。"""
    img = to_rgb(0.05 + value_noise(70, 53) * 0.03, (0.85, 0.84, 0.82))
    cx, cy, R = W * 0.5, H * 0.50, 300

    layer = pil_layer()
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - R, cy - R * 0.55, cx + R, cy + R * 0.55],
              fill=(150, 152, 150, 255), outline=(180, 182, 180, 255), width=4)
    # 502 的疤：白、硬、丑
    rng = np.random.default_rng(61)
    for k in range(4):
        pts = [(cx - R * 0.9 + k * 40, cy - R * 0.4)]
        for i in range(9):
            pts.append((pts[-1][0] + rng.normal(45, 26),
                        pts[-1][1] + rng.normal(22, 20)))
        d.line(pts, fill=(246, 246, 240, 255), width=7, joint="curve")
    img = composite(img, layer, glow=0.08)

    # 渗水
    leak = smoothstep(0.30, 1.0, t / dur)
    wr = np.sqrt(((X - 0.0) ** 2) / (0.02 + leak * 0.65) + ((Y - 0.72) ** 2) / 0.010)
    img += to_rgb(smoothstep(1.0, 0.2, wr) * 0.11 * leak, (0.55, 0.62, 0.70))

    img *= VIG[:, :, None]
    return img * 0.9 + grain(t)


def sc_black(t, dur):
    return blank()
