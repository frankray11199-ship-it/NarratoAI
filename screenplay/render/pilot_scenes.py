#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
先导片段专用程序化空镜渲染器
============================
为 8 分钟先导片段（场 12—23）新增的 18 个空镜。
全部由数学函数生成，不依赖任何外部素材。

复用 engine.py 的坐标网格、噪声、合成与曝光工具。
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import engine as E
from engine import (to_rgb, blank, smoothstep, value_noise, grain, pil_layer,
                    composite, font, sc_water_moon, sc_ring_sink, sc_viewfinder)


def _g():
    """取当前分辨率下的网格（支持运行时切分辨率）"""
    return E.X, E.Y, E.W, E.H, E.VIG


# ---------------------------------------------------------------- 场 12

def lake_dusk(t, dur):
    """黄昏的洱海。太阳高度 +6.9°，逆光，色温持续下降。"""
    X, Y, W, H, VIG = _g()
    y0 = 0.42
    below = Y > y0
    depth = np.clip(Y - y0, 1e-3, None)
    persp = 1.0 / (depth * 2.4 + 0.04)

    wave = (0.5 * np.sin(persp * 0.8 + t * 1.5)
            + 0.3 * np.sin(persp * 1.6 - t * 1.1 + X * 2.8)
            + 0.2 * np.sin(persp * 3.1 + t * 2.4 - X * 5.5))

    sun_x = -0.55
    colw = 0.07 + depth * 1.5
    col = np.exp(-((X - sun_x) ** 2) / (colw ** 2 + 1e-6))
    spec = np.clip(wave, 0, None) ** 2.2
    water = col * spec * 1.6 + 0.10 + col * 0.14

    # 天空：逆光，靠近太阳处最亮
    sky = (0.30 * np.exp(-((X - sun_x) ** 2) / 0.9)
           * np.exp(-((y0 - Y) ** 2) / 0.35) + 0.10)
    lum = np.where(below, water, sky)

    img = to_rgb(lum, (1.0, 0.72, 0.42)) * 0.9
    img += to_rgb(np.where(below, water * 0.3, sky * 0.4), (0.55, 0.62, 0.85)) * 0.4

    # 远山剪影
    ridge = y0 - 0.10 - 0.045 * np.sin(X * 2.1 + 0.6) - 0.02 * np.sin(X * 5.3)
    img *= (1 - 0.86 * ((Y < y0) & (Y > ridge)).astype(np.float32))[:, :, None]

    img *= VIG[:, :, None]
    return img + grain(t)


def _god_rays(t, dur, open_amt):
    """苍山上方云隙光柱。open_amt=0 云未开，=1 光柱贯下。"""
    X, Y, W, H, VIG = _g()
    n = value_noise(24, 61) * 0.6 + value_noise(7, 62) * 0.4
    sky = 0.16 + n * 0.20
    img = to_rgb(sky, (0.62, 0.66, 0.78))

    gap_x = -0.30
    if open_amt > 0.01:
        # 从云隙向下发散的光柱
        for k, off in enumerate([-0.10, -0.04, 0.02, 0.07, 0.13]):
            ax = gap_x + off
            spread = 0.035 + Y * 0.20
            beam = np.exp(-((X - ax - Y * 0.16) ** 2) / (spread ** 2))
            beam *= smoothstep(0.22, 0.55, Y) * (1 - smoothstep(0.80, 1.0, Y))
            flick = 0.85 + 0.15 * np.sin(t * 1.3 + k)
            img += to_rgb(beam * 0.30 * open_amt * flick, (1.0, 0.93, 0.76))
        # 光柱落到湖面
        hit = np.exp(-((X - gap_x - 0.13) ** 2) / 0.05) * \
            np.exp(-((Y - 0.88) ** 2) / 0.004)
        img += to_rgb(hit * 0.9 * open_amt, (1.0, 0.95, 0.82))

    # 山脊
    ridge = 0.60 - 0.09 * np.sin(X * 1.6 + 0.3) - 0.035 * np.sin(X * 4.2)
    img *= (1 - 0.80 * (Y > ridge).astype(np.float32))[:, :, None]
    img += to_rgb((Y > ridge).astype(np.float32) * 0.03, (0.4, 0.45, 0.6))

    img *= VIG[:, :, None]
    return img + grain(t)


def god_rays_closed(t, dur):
    return _god_rays(t, dur, 0.0)


def god_rays_open(t, dur):
    return _god_rays(t, dur, smoothstep(0.05, 0.55, t / dur))


# ---------------------------------------------------------------- 场 13

def brazier(t, dur):
    """客栈院子的炭火盆。约 1900K，自下而上。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.020 + 0.015 * (1 - Y), (0.35, 0.40, 0.55))

    fx, fy = 0.0, 0.72
    fl = 0.75 + 0.25 * np.sin(t * 13) * np.sin(t * 5.1) + 0.10 * np.sin(t * 31)
    r = np.sqrt((X - fx) ** 2 + ((Y - fy) * 1.3) ** 2)
    img += to_rgb(np.exp(-(r ** 2) / 0.13) * 0.62 * fl, (1.0, 0.48, 0.14))
    img += to_rgb(smoothstep(0.055, 0.020, r) * fl, (1.0, 0.80, 0.42))

    # 火星
    rng = np.random.default_rng(int(t * 3) % 997)
    sp = pil_layer()
    sd = ImageDraw.Draw(sp)
    for i in range(22):
        ph = (t * rng.uniform(0.3, 0.8) + rng.random()) % 1.0
        px = W * (0.5 + rng.normal(0, 0.035) + np.sin(ph * 7 + i) * 0.02)
        py = H * (fy - ph * 0.45)
        a = int(220 * (1 - ph) ** 2)
        sd.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 170, 70, a))
    img = composite(img, sp, glow=0.45)

    img *= VIG[:, :, None]
    return img + grain(t, 0.05)


def two_cups(t, dur):
    """两只梅子酒杯。火光在酒面上晃。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.035 + value_noise(50, 63) * 0.02, (0.7, 0.5, 0.32))

    lay = pil_layer()
    d = ImageDraw.Draw(lay)
    for cx in (W * 0.38, W * 0.62):
        cy, rw, rh = H * 0.56, W * 0.055, H * 0.030
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
                  outline=(200, 190, 175, 220), width=3)
        # 酒面
        sh = 0.5 + 0.5 * np.sin(t * 2.2 + cx)
        d.ellipse([cx - rw * 0.86, cy - rh * 0.80, cx + rw * 0.86, cy + rh * 0.80],
                  fill=(180, 96, 52, int(150 + 60 * sh)))
        d.polygon([(cx - rw, cy), (cx - rw * 0.72, cy + H * 0.10),
                   (cx + rw * 0.72, cy + H * 0.10), (cx + rw, cy)],
                  outline=(180, 168, 152, 150))
    img = composite(img, lay, glow=0.30)
    img *= VIG[:, :, None]
    return img + grain(t)


# ---------------------------------------------------------------- 场 14

def forest_light(t, dur):
    """松林。硬边光斑随风在地面移动。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.055 + value_noise(34, 64) * 0.030, (0.40, 0.46, 0.34))

    # 稀疏的椭圆光斑，随风缓慢漂移（不是噪声阈值——那会渲成迷彩）
    rng = np.random.default_rng(65)
    for i in range(9):
        bx = rng.uniform(-1.0, 1.0)
        by = rng.uniform(0.45, 1.0)
        sx = rng.uniform(0.010, 0.030)
        sy = rng.uniform(0.0016, 0.0045)
        dx = np.sin(t * rng.uniform(0.20, 0.45) + i * 1.7) * 0.035
        dy = np.cos(t * rng.uniform(0.15, 0.32) + i) * 0.012
        br = 0.30 + 0.14 * np.sin(t * rng.uniform(0.6, 1.3) + i * 2.1)
        patch = np.exp(-(((X - bx - dx) ** 2) / sx + ((Y - by - dy) ** 2) / sy))
        img += to_rgb(patch * br, (1.0, 0.94, 0.70))

    # 高处的漏光雾
    img += to_rgb(np.exp(-((Y - 0.18) ** 2) / 0.05) * 0.10, (0.95, 0.92, 0.74))

    # 树干
    lay = pil_layer()
    d = ImageDraw.Draw(lay)
    rng2 = np.random.default_rng(67)
    for i in range(6):
        x = rng2.uniform(0.03, 0.97) * W
        w = rng2.uniform(8, 26)
        d.polygon([(x - w, 0), (x + w, 0),
                   (x + w * 1.5, H), (x - w * 1.5, H)],
                  fill=(22, 19, 16, 225))
    img = composite(img, lay)

    img *= VIG[:, :, None]
    return img + grain(t)


# ---------------------------------------------------------------- 场 15

def butterfly(t, dur):
    """玻璃柜里的蝴蝶标本。一根钉子穿过胸腔。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.16 + value_noise(60, 68) * 0.05, (0.72, 0.76, 0.84))

    cx, cy = W * 0.5, H * 0.50
    lay = pil_layer()
    d = ImageDraw.Draw(lay)

    def wing(sign):
        pts = []
        for i in range(46):
            a = -1.25 + i / 45.0 * 2.5
            rr = (W * 0.135) * (0.62 + 0.38 * np.cos(a * 1.35))
            pts.append((cx + sign * abs(np.cos(a)) * rr,
                        cy + np.sin(a) * rr * 0.92))
        return pts

    for sign in (1, -1):
        d.polygon(wing(sign), fill=(58, 84, 132, 255), outline=(150, 172, 210, 255))
        for k in range(4):
            a = -0.9 + k * 0.6
            d.line([(cx, cy), (cx + sign * np.cos(a) * W * 0.10,
                               cy + np.sin(a) * H * 0.12)],
                   fill=(112, 142, 190, 190), width=2)

    d.ellipse([cx - 6, cy - H * 0.075, cx + 6, cy + H * 0.075],
              fill=(24, 22, 20, 255))
    # 钉子
    d.line([(cx, cy - H * 0.20), (cx, cy + H * 0.03)],
           fill=(232, 230, 224, 255), width=4)
    d.ellipse([cx - 9, cy - H * 0.215, cx + 9, cy - H * 0.185],
              fill=(240, 238, 232, 255))
    img = composite(img, lay, glow=0.10)

    # 玻璃反射
    img += to_rgb(np.exp(-(((X + 0.34) * 1.5 + (Y - 0.30) * 0.8) ** 2) / 0.06) * 0.16,
                  (0.85, 0.90, 1.0))
    img *= VIG[:, :, None]
    return img + grain(t)


def _fog(t, dur, amt):
    """玻璃上的呼吸雾：两团，一大一小，慢慢连成一片。"""
    X, Y, W, H, VIG = _g()
    img = butterfly(t + 3.0, dur) * 0.82

    merge = smoothstep(0.30, 0.85, amt)
    ax = -0.13 + 0.055 * merge
    bx = 0.10 - 0.055 * merge
    sa = 0.030 + 0.045 * amt
    sb = 0.020 + 0.032 * amt

    fa = np.exp(-(((X - ax) ** 2) / sa + ((Y - 0.50) ** 2) / (sa * 0.75)))
    fb = np.exp(-(((X - bx) ** 2) / sb + ((Y - 0.53) ** 2) / (sb * 0.75)))
    fog = np.clip(fa + fb, 0, 1.25) * amt

    img = img * (1 - fog[:, :, None] * 0.62) + \
        to_rgb(fog * 0.42, (0.90, 0.93, 0.98))
    img *= VIG[:, :, None]
    return img + grain(t)


def breath_fog(t, dur):
    return _fog(t, dur, smoothstep(0.0, 0.72, t / dur))


def breath_fog_fade(t, dur):
    return _fog(t, dur, 1.0 - smoothstep(0.10, 0.95, t / dur))


# ---------------------------------------------------------------- 场 16

def night_sky(t, dur):
    """天台夜空。盈凸月照亮 96%，高度 +55°。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.030 + 0.028 * (1 - Y) ** 2, (0.30, 0.38, 0.62))

    rng = np.random.default_rng(69)
    st = pil_layer()
    sd = ImageDraw.Draw(st)
    for i in range(220):
        sx, sy = rng.random() * W, rng.random() * H * 0.72
        b = rng.random() ** 2.4
        tw = 0.65 + 0.35 * np.sin(t * rng.uniform(1.2, 3.4) + i)
        a = int(215 * b * tw)
        rr = 1 if b < 0.75 else 2
        sd.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(226, 232, 246, a))
    img = composite(img, st, glow=0.16)

    mx, my = 0.42, 0.20
    r = np.sqrt((X - mx) ** 2 + (Y - my) ** 2)
    img += to_rgb(smoothstep(0.048, 0.038, r) * 0.92, (1.0, 0.98, 0.92))
    img += to_rgb(np.exp(-(r ** 2) / 0.022) * 0.24, (0.86, 0.90, 1.0))
    # 96% 而非满月：右下缺一小块
    img -= to_rgb(smoothstep(0.052, 0.044,
                             np.sqrt((X - mx - 0.012) ** 2 + (Y - my - 0.010) ** 2))
                  * 0.05, (1.0, 1.0, 1.0))

    img *= VIG[:, :, None]
    return np.clip(img, 0, None) + grain(t)


def phone_flash(t, dur):
    """桌上的手机屏幕亮了一下又暗了。画面里有个很小的、像是小孩的影子。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.025 + value_noise(45, 70) * 0.02, (0.5, 0.55, 0.7))

    p = t / dur
    on = smoothstep(0.16, 0.24, p) * (1 - smoothstep(0.44, 0.56, p))
    flip = smoothstep(0.62, 0.80, p)

    lay = pil_layer()
    d = ImageDraw.Draw(lay)
    x0, y0 = W * 0.34, H * 0.36
    x1, y1 = W * 0.66, H * 0.68
    if on > 0.01:
        d.rectangle([x0, y0, x1, y1], fill=(150, 168, 190, int(210 * on)))
        # 屏保里那个很小的影子
        cx = (x0 + x1) / 2
        d.ellipse([cx - W * 0.020, y0 + H * 0.10, cx + W * 0.020, y0 + H * 0.155],
                  fill=(70, 78, 92, int(230 * on)))
        d.polygon([(cx - W * 0.032, y1 - H * 0.055), (cx + W * 0.032, y1 - H * 0.055),
                   (cx + W * 0.020, y0 + H * 0.15), (cx - W * 0.020, y0 + H * 0.15)],
                  fill=(70, 78, 92, int(230 * on)))
    img = composite(img, lay, glow=0.42 * float(on))

    # 一只手把手机翻扣过去
    if flip > 0.01:
        img *= (1 - flip * 0.55 *
                np.exp(-(((X - 0.02) ** 2) / 0.20 + ((Y - 0.52) ** 2) / 0.10)))[:, :, None]

    img *= VIG[:, :, None]
    return img + grain(t, 0.05)


# ---------------------------------------------------------------- 场 17

def lake_noon(t, dur):
    """正午的洱海。太阳高度 72.9°，顶光，高光刺眼。"""
    X, Y, W, H, VIG = _g()
    y0 = 0.30
    below = Y > y0
    depth = np.clip(Y - y0, 1e-3, None)
    persp = 1.0 / (depth * 2.0 + 0.05)

    wave = (0.5 * np.sin(persp * 1.1 + t * 2.6)
            + 0.3 * np.sin(persp * 2.3 - t * 2.0 + X * 4.0)
            + 0.2 * np.sin(persp * 4.7 + t * 3.8 - X * 8.5))
    spec = np.clip(wave, 0, None) ** 5.0
    water = 0.30 + spec * 2.6 * np.exp(-((X - 0.0) ** 2) / 2.2)

    sky = 0.62 - 0.22 * (y0 - Y)
    lum = np.where(below, water, sky)
    img = to_rgb(lum, (0.74, 0.85, 0.97))

    ridge = y0 - 0.055 - 0.030 * np.sin(X * 1.9 + 1.1)
    img *= (1 - 0.42 * ((Y < y0) & (Y > ridge)).astype(np.float32))[:, :, None]

    img *= VIG[:, :, None]
    return img + grain(t)


def water_moon_break(t, dur):
    """镜头留在水面上的月亮。波纹一过，散了。"""
    ag = smoothstep(0.35, 0.85, t / dur) * 0.9
    return sc_water_moon(t, dur, bright=1.0 - 0.25 * ag, agitate=ag)


# ---------------------------------------------------------------- 场 19

def lamp_off(t, dur):
    """一只手伸向台灯。关灯。"""
    X, Y, W, H, VIG = _g()
    p = t / dur
    on = 1.0 - smoothstep(0.58, 0.66, p)

    img = to_rgb(0.020 + 0.010 * (1 - Y), (0.4, 0.44, 0.58))
    lx, ly = 0.22, 0.40
    r = np.sqrt((X - lx) ** 2 + ((Y - ly) * 1.1) ** 2)
    img += to_rgb(np.exp(-(r ** 2) / 0.14) * 0.60 * on, (1.0, 0.74, 0.36))
    img += to_rgb(smoothstep(0.045, 0.018, r) * on, (1.0, 0.92, 0.68))

    # 伸过来的手（剪影）
    reach = smoothstep(0.10, 0.60, p)
    hx = -0.55 + reach * 0.62
    hand = np.exp(-(((X - hx) ** 2) / 0.020 + ((Y - 0.52) ** 2) / 0.010))
    img *= (1 - np.clip(hand, 0, 1) * 0.90)[:, :, None]

    img *= VIG[:, :, None]
    return img + grain(t, 0.05)


def phone_ringing(t, dur):
    """黑屏。手机亮起来，来电显示'周砚'。响了很久，暗下去。"""
    X, Y, W, H, VIG = _g()
    img = blank()
    p = t / dur
    on = smoothstep(0.10, 0.20, p) * (1 - smoothstep(0.72, 0.94, p))
    if on <= 0.01:
        return img + grain(t, 0.02)

    pulse = 0.72 + 0.28 * (np.sin(t * 6.0) > 0)
    lay = pil_layer()
    d = ImageDraw.Draw(lay)
    x0, y0 = W * 0.40, H * 0.34
    x1, y1 = W * 0.60, H * 0.66
    a = int(200 * on * pulse)
    d.rectangle([x0, y0, x1, y1], fill=(118, 138, 162, a))
    f = font(max(12, int(H * 0.045)))
    txt = "周砚"
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((W - (bb[2] - bb[0])) / 2, H * 0.46), txt, font=f,
           fill=(240, 244, 250, int(235 * on * pulse)))
    img = composite(img, lay, glow=0.50 * float(on))
    return img + grain(t, 0.02)


# ---------------------------------------------------------------- 场 20

def morning_light(t, dur):
    """低角度晨光从东窗斜射入室。太阳高度 +6°。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.10 + value_noise(55, 71) * 0.04, (0.72, 0.70, 0.68))

    for k, off in enumerate([-0.30, -0.06, 0.20]):
        band = np.exp(-(((X - off) - (Y - 0.5) * 0.85) ** 2) / 0.010)
        img += to_rgb(band * 0.34 * (0.9 + 0.1 * np.sin(t * 0.5 + k)),
                      (1.0, 0.86, 0.62))

    dust = value_noise(6, 72)
    img += to_rgb(smoothstep(0.72, 0.92, np.roll(dust, int(t * 12) % max(1, W), axis=1))
                  * 0.10, (1.0, 0.94, 0.82))

    img *= VIG[:, :, None]
    return img + grain(t)


# ---------------------------------------------------------------- 场 21

def ring_sunlight(t, dur):
    """银戒举在直射天光下。和真的没有区别。只是轻。"""
    X, Y, W, H, VIG = _g()
    img = to_rgb(0.14 + value_noise(48, 73) * 0.05, (0.76, 0.74, 0.70))
    shaft = np.exp(-(((X - 0.10) - (Y - 0.5) * 0.30) ** 2) / 0.022)
    img += to_rgb(shaft * 0.30, (1.0, 0.95, 0.84))

    p = t / dur
    lift = smoothstep(0.05, 0.45, p)
    cx = W * (0.5 + 0.02 * np.sin(t * 1.1))
    cy = H * (0.72 - 0.24 * lift)
    rr = W * 0.075

    lay = pil_layer()
    d = ImageDraw.Draw(lay)
    d.ellipse([cx - rr, cy - rr * 0.30, cx + rr, cy + rr * 0.30],
              outline=(228, 226, 220, 255), width=max(3, int(W * 0.010)))
    img = composite(img, lay, glow=0.30)

    # 镀层高光：比铂金更漫、边缘更钝
    hl = np.exp(-(((X - 0.06) ** 2) / 0.006 +
                  ((Y - (0.72 - 0.24 * lift)) ** 2) / 0.0012))
    img += to_rgb(hl * 0.55 * lift, (1.0, 0.99, 0.94))

    img *= VIG[:, :, None]
    return img + grain(t)


# ---------------------------------------------------------------- 场 23

def shutter_freeze(t, dur):
    """快门声。定格。画面凝成一张照片，边缘出现相纸白边。"""
    X, Y, W, H, VIG = _g()
    p = t / dur
    img = to_rgb(0.30 + value_noise(40, 74) * 0.10, (0.70, 0.72, 0.78))
    fig = np.exp(-(((X - 0.0) ** 2) / 0.055 + ((Y - 0.56) ** 2) / 0.13))
    img += to_rgb(fig * 0.30, (0.88, 0.83, 0.76))

    # 快门闭合
    sh = smoothstep(0.06, 0.16, p)
    img *= (1 - ((Y < sh * 0.5) | (Y > 1 - sh * 0.5)).astype(np.float32))[:, :, None]
    reopen = smoothstep(0.18, 0.30, p)
    if reopen > 0:
        img = img * (1 - reopen) + to_rgb(
            (0.30 + value_noise(40, 74) * 0.10 + fig * 0.30) * reopen,
            (0.74, 0.74, 0.76))

    # 凝成照片：去饱和 + 相纸白边
    froze = smoothstep(0.34, 0.60, p)
    g = img.mean(axis=2, keepdims=True)
    img = img * (1 - froze * 0.75) + np.repeat(g, 3, axis=2) * (froze * 0.75)

    if froze > 0.01:
        m = 0.055 * froze
        border = ((X / (W / H) < -1 + m * 2) | (X / (W / H) > 1 - m * 2) |
                  (Y < m) | (Y > 1 - m)).astype(np.float32)
        img = img * (1 - border[:, :, None]) + \
            to_rgb(border * 0.90 * froze, (1.0, 1.0, 0.99))

    img *= VIG[:, :, None]
    return img + grain(t, 0.045)


# ---------------------------------------------------------------- 注册表

REGISTRY = {
    "lake_dusk": lake_dusk,
    "god_rays_closed": god_rays_closed,
    "god_rays_open": god_rays_open,
    "brazier": brazier,
    "two_cups": two_cups,
    "forest_light": forest_light,
    "viewfinder": sc_viewfinder,
    "butterfly": butterfly,
    "breath_fog": breath_fog,
    "breath_fog_fade": breath_fog_fade,
    "night_sky": night_sky,
    "phone_flash": phone_flash,
    "lake_noon": lake_noon,
    "ring_sink": sc_ring_sink,
    "water_moon": lambda t, d: sc_water_moon(t, d, bright=1.0, moon_x=0.10),
    "water_moon_break": water_moon_break,
    "lamp_off": lamp_off,
    "phone_ringing": phone_ringing,
    "morning_light": morning_light,
    "ring_sunlight": ring_sunlight,
    "shutter_freeze": shutter_freeze,
}
