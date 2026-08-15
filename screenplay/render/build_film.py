#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《说谎的爱人》· 概念预告片 合成器
==================================
把 engine.py 的场景渲染器与 score.py 的合成配乐编排成一支完整成片。

用法:
    python3 build_film.py [--preview]   # --preview 出 640x360 快速样片
"""

import os
import sys
import subprocess
import numpy as np
import imageio_ffmpeg

import engine as E
from engine import (sc_water_moon, sc_kintsugi, sc_wall_crack, sc_ring_sink,
                    sc_viewfinder, sc_rain_night, sc_glass_break, sc_gold_dust,
                    sc_watch, sc_streetlight, sc_years, sc_bowl_leak, sc_black,
                    text_card, composite, blank, font, pil_layer)
import score as S
from PIL import ImageDraw

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ================================================================
# 时间线：(渲染器, 时长, [(文本起点, 文本时长, 文本行, 选项)])
# ================================================================
TL = [
    (sc_black, 3.0, []),

    (lambda t, d: sc_water_moon(t, d, bright=E.smoothstep(0, 5, t)), 13.0, [
        (3.2, 4.0, ["她 把 手 伸 进 水 里"], dict(size=54, track=2)),
        (8.4, 3.6, ["捞 了 三 次"], dict(size=54, track=2)),
    ]),

    (sc_kintsugi, 15.0, [
        (4.6, 3.8, ["有些裂缝是修不好的"], dict(size=56, y_center=0.87)),
        (9.0, 4.2, ["只能让它看起来好看一点"], dict(size=52, y_center=0.87)),
    ]),

    (sc_wall_crack, 13.0, [
        (3.6, 3.6, ["拆了它，不会当场塌"], dict(size=54)),
        (7.8, 4.2, ["塌 是 三 年 以 后 的 事"], dict(size=58, track=4,
                                                 color=(232, 96, 78))),
    ]),

    (sc_ring_sink, 11.0, [
        (1.0, 3.4, ["2024 年 4 月 9 日"], dict(size=42, track=3,
                                              color=(196, 206, 214),
                                              small="洱海")),
        (6.4, 3.6, ["她 把 戒 指 弄 丢 了"], dict(size=50, track=2)),
    ]),

    (sc_viewfinder, 11.5, [
        (2.6, 3.8, ["框里的东西你看着最真"], dict(size=52)),
        (7.0, 3.8, ["真东西都在框外面"], dict(size=52)),
    ]),

    (sc_rain_night, 13.0, [
        (4.0, 4.6, ["你 还 想 回 来 吗"], dict(size=62, track=6)),
    ]),

    (sc_glass_break, 9.0, [
        (3.4, 4.4, ["你说谎的时候", "会摸左边耳朵"], dict(size=54)),
    ]),

    (sc_black, 4.0, [
        (0.4, 3.2, ["我 第 一 年 就 知 道"], dict(size=58, track=5)),
    ]),

    (sc_gold_dust, 9.5, [
        (2.8, 4.2, ["她的右手", "再也拿不稳描金笔"], dict(size=52)),
    ]),

    (sc_watch, 10.0, [
        (3.6, 4.4, ["我 一 直 以 为 来 得 及"], dict(size=56, track=4,
                                                y_center=0.88)),
    ]),

    (sc_streetlight, 9.5, [
        (3.0, 5.0, ["他走那天", "那盏坏了八个月的灯", "修好了"], dict(size=46)),
    ]),

    (sc_years, 16.0, []),

    (sc_bowl_leak, 11.5, [
        (2.6, 3.6, ["她 终 于 用 了 502"], dict(size=52, track=3, y_center=0.16)),
        (7.2, 3.6, ["碗 漏 了"], dict(size=58, track=8, y_center=0.16)),
    ]),

    (lambda t, d: sc_water_moon(t, d, bright=0.85, agitate=0.15), 16.0, [
        (2.0, 3.2, ["2033 年 4 月 6 日"], dict(size=40, track=3,
                                              color=(190, 200, 210),
                                              small="才村码头 · 同一个位置")),
        (7.0, 3.4, ["她 回 头 了"], dict(size=58, track=6)),
        (11.2, 4.0, ["身 后 什 么 都 没 有"], dict(size=58, track=6)),
    ]),

    (sc_black, 10.0, []),      # 片名（单独绘制）
    (sc_black, 3.5, []),
]

TITLE_SEG = len(TL) - 2


def seg_bounds():
    marks, t = [], 0.0
    for fn, d, texts in TL:
        marks.append((t, d))
        t += d
    return marks, t


BOUNDS, TOTAL = seg_bounds()


def title_frame(t, dur):
    """片名卡：《说谎的爱人》"""
    img = blank()
    layer = pil_layer()
    d = ImageDraw.Draw(layer)

    a = E.smoothstep(1.0, 3.4, t) * (1 - E.smoothstep(dur - 2.2, dur, t))
    f = font(112)
    title = "说谎的爱人"
    track = 26
    widths = [d.textbbox((0, 0), c, font=f)[2] - d.textbbox((0, 0), c, font=f)[0]
              for c in title]
    lw = sum(widths) + track * (len(title) - 1)
    x = (E.W - lw) / 2
    for c, cw in zip(title, widths):
        d.text((x, E.H * 0.40), c, font=f, fill=(240, 236, 228, int(255 * a)))
        x += cw + track

    f2 = font(30)
    sub = "T H E   L Y I N G   L O V E R"
    bb = d.textbbox((0, 0), sub, font=f2)
    a2 = E.smoothstep(3.6, 5.2, t) * (1 - E.smoothstep(dur - 2.2, dur, t))
    d.text(((E.W - (bb[2] - bb[0])) / 2, E.H * 0.56), sub, font=f2,
           fill=(168, 162, 152, int(255 * a2)))

    f3 = font(24)
    cr = "程序化影像生成 · 全部画面与配乐由数学函数合成"
    bb3 = d.textbbox((0, 0), cr, font=f3)
    a3 = E.smoothstep(6.0, 7.4, t) * (1 - E.smoothstep(dur - 2.0, dur, t))
    d.text(((E.W - (bb3[2] - bb3[0])) / 2, E.H * 0.86), cr, font=f3,
           fill=(112, 108, 102, int(255 * a3)))

    return composite(img, layer, glow=0.22)


def build_marks():
    """按时间线派生配乐事件"""
    m = {"water": [], "rain": [], "heart": [], "shutter": [], "shatter": [],
         "riser": [], "drop": [], "motif": [], "note": []}
    b = BOUNDS
    m["water"] += [(b[1][0], b[1][1]), (b[4][0], b[4][1]),
                   (b[14][0], b[14][1] + 2)]
    m["rain"] += [(b[6][0], b[6][1])]
    m["heart"] += [(b[6][0] + 5, 9.0), (b[7][0], 8.0)]
    m["shutter"] += [b[1][0] + 3.0, b[5][0] + 9.4, b[15][0] + 8.4]
    m["shatter"] += [b[7][0] + 0.25]
    m["riser"] += [(b[6][0] + 7.5, 5.4), (b[13][0] + 6.5, 4.6)]
    m["drop"] += [b[7][0] + 0.2, b[8][0] + 0.3]
    m["motif"] += [(b[2][0] + 1.2, 1.55, 0.26, 1.5),
                   (b[10][0] + 1.0, 1.75, 0.22, 1.3),
                   (b[14][0] + 1.5, 2.10, 0.24, 1.1)]
    m["note"] += [(b[3][0] + 7.6, "D2", 0.34),
                  (b[9][0] + 2.4, "F3", 0.22),
                  (b[11][0] + 2.6, "C4", 0.20),
                  (b[12][0] + 1.0, "A2", 0.26),
                  (b[15][0] + 1.4, "D3", 0.30),
                  (b[15][0] + 4.4, "A3", 0.22),
                  (b[15][0] + 7.2, "D4", 0.18)]
    return m


def render(preview=False):
    ow, oh = (640, 360) if preview else (E.W, E.H)
    fps = 12 if preview else E.FPS
    out_mp4 = os.path.join(OUT_DIR, "..", "说谎的爱人-概念预告片.mp4")
    out_mp4 = os.path.abspath(out_mp4)
    if preview:
        out_mp4 = os.path.join(OUT_DIR, "preview.mp4")
    wav = os.path.join(OUT_DIR, "score.wav")

    print("[1/3] 合成配乐 ...", flush=True)
    S.build_score(build_marks(), TOTAL, wav)
    print("      时长 %.1fs -> %s" % (TOTAL, wav), flush=True)

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (E.W, E.H), "-r", str(fps), "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p",
           "-vf", "scale=%d:%d" % (ow, oh),
           "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    total_frames = int(TOTAL * fps)
    print("[2/3] 渲染 %d 帧 @ %dfps ..." % (total_frames, fps), flush=True)

    done = 0
    for si, (fn, dur, texts) in enumerate(TL):
        nf = int(dur * fps)
        for i in range(nf):
            t = i / fps
            if si == TITLE_SEG:
                img = title_frame(t, dur)
            else:
                img = fn(t, dur)

            for (ts, td, lines, opts) in texts:
                if ts <= t < ts + td:
                    layer, a = text_card(lines, t - ts, td, **opts)
                    if a > 0.002:
                        arr = np.asarray(layer, dtype=np.float32) / 255.0
                        rgb, al = arr[:, :, :3], arr[:, :, 3:4] * a
                        img = img * (1 - al * 0.55) + rgb * al

            # 统一曝光校正（片名卡与纯黑场不参与，避免黑底被抬灰）
            if si != TITLE_SEG and fn is not sc_black:
                img = E.expose(img)

            # 段落首尾淡入淡出
            k = min(E.smoothstep(0, 0.55, t), 1 - E.smoothstep(dur - 0.55, dur, t))
            img = img * k

            frame = (np.clip(img, 0, 1) * 255).astype(np.uint8)
            proc.stdin.write(frame.tobytes())
            done += 1
            if done % 240 == 0:
                print("      %d/%d (%.0f%%)" % (done, total_frames,
                                                100 * done / total_frames), flush=True)

    proc.stdin.close()
    proc.wait()
    print("[3/3] 完成 -> %s" % out_mp4, flush=True)
    return out_mp4


if __name__ == "__main__":
    render(preview="--preview" in sys.argv)
