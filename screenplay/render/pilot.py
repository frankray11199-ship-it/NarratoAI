#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《说谎的爱人》8 分钟先导片段 · 动态分镜（Animatic）
====================================================
按 pipeline/pilot_shots.py 的镜头表，逐镜组装成一条精确到帧的时间轴。

    proc 镜头 → 用 pilot_scenes.py 真实渲染出画面
    dh   镜头 → 用镜头卡占位，卡上带全部拍摄信息与台词

用途：在投入 GPU 生成数字人之前，先验证剪辑节奏、段落长度与情绪曲线。
待数字人镜头产出后，按镜号逐条替换即可，时间轴不动。

用法:
    python3 pilot.py            1280x720 / 24fps
    python3 pilot.py --fast     640x360  / 12fps（快速校对）
"""

import os
import sys
import subprocess
import numpy as np
import imageio_ffmpeg
from PIL import ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "pipeline"))

import engine as E                                    # noqa: E402
import score as S                                     # noqa: E402
import pilot_shots as PS                              # noqa: E402


def shot_card(shot, t, dur):
    """数字人镜头的占位卡：黑底 + 全部拍摄信息 + 进度条"""
    W, H = E.W, E.H
    img = E.blank()
    img += E.to_rgb(np.full((H, W), 0.045, dtype=np.float32), (0.52, 0.56, 0.66))

    lay = E.pil_layer()
    d = ImageDraw.Draw(lay)
    s = lambda k: max(9, int(H * k))                  # noqa: E731

    a = int(255 * min(E.smoothstep(0, 0.25, t),
                      1 - E.smoothstep(dur - 0.2, dur, t)))
    if a < 4:
        return img

    m = W * 0.075
    # 顶栏：镜号 / 场次 / 景别 / 运镜 / 时长
    d.text((m, H * 0.10), shot["id"], font=E.font(s(0.062)),
           fill=(232, 228, 220, a))
    head = "场 %d　·　%s　·　%s　·　%.1fs" % (shot["scene"], shot["size"],
                                            shot["move"], shot["dur"])
    d.text((m, H * 0.185), head, font=E.font(s(0.034)), fill=(150, 156, 168, a))

    # 待生成标记
    tag = "数字人镜头 · 待生成"
    d.text((W - m - s(0.030) * len(tag) * 0.62, H * 0.105), tag,
           font=E.font(s(0.030)), fill=(206, 138, 62, a))
    if shot["char"]:
        d.text((W - m - s(0.030) * (len(shot["char"]) + 6) * 0.62, H * 0.165),
               "%s / %s" % (shot["char"],
                            PS.CHARACTERS[shot["char"]]["trigger"]),
               font=E.font(s(0.028)), fill=(120, 126, 138, a))

    d.line([(m, H * 0.245), (W - m, H * 0.245)], fill=(70, 74, 84, a), width=2)

    # 画面内容
    y = H * 0.305
    f = E.font(s(0.046))
    for ln in _wrap(shot["desc"].replace("**", ""), 24):
        d.text((m, y), ln, font=f, fill=(224, 220, 212, a))
        y += H * 0.070

    # 台词
    if shot["dialogue"]:
        y += H * 0.030
        d.line([(m, y), (m + W * 0.05, y)], fill=(206, 138, 62, a), width=3)
        y += H * 0.030
        fd = E.font(s(0.050))
        for ln in _wrap(shot["dialogue"], 20):
            d.text((m + W * 0.02, y), ln, font=fd, fill=(240, 224, 196, a))
            y += H * 0.072

    # 备注
    if shot["note"]:
        y += H * 0.020
        fn = E.font(s(0.028))
        for ln in _wrap("※ " + shot["note"], 40):
            d.text((m, y), ln, font=fn, fill=(126, 132, 144, a))
            y += H * 0.042

    # 底部进度条
    p = t / dur
    by = H * 0.925
    d.line([(m, by), (W - m, by)], fill=(52, 56, 64, a), width=3)
    d.line([(m, by), (m + (W - 2 * m) * p, by)], fill=(206, 138, 62, a), width=3)

    return E.composite(img, lay)


def _wrap(text, n):
    out, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= n and ch in "，。；、！？　 ":
            out.append(cur.strip())
            cur = ""
        elif len(cur) >= n + 8:
            out.append(cur)
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out[:6]


def scene_slate(scene, t, dur):
    """场次板：每场开头 0.8 秒"""
    W, H = E.W, E.H
    img = E.blank()
    lay = E.pil_layer()
    d = ImageDraw.Draw(lay)
    a = int(255 * (1 - E.smoothstep(dur * 0.6, dur, t)))
    f = E.font(max(14, int(H * 0.10)))
    txt = "场 %d" % scene
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((W - (bb[2] - bb[0])) / 2, H * 0.42), txt, font=f,
           fill=(226, 222, 214, a))
    f2 = E.font(max(9, int(H * 0.026)))
    sub = PS.LIGHT[scene].split("｜")[0]
    bb2 = d.textbbox((0, 0), sub, font=f2)
    d.text(((W - (bb2[2] - bb2[0])) / 2, H * 0.58), sub, font=f2,
           fill=(132, 138, 150, a))
    return E.composite(img, lay)


def build_marks(timeline):
    """按镜头表派生配乐事件"""
    m = {"water": [], "rain": [], "heart": [], "shutter": [], "shatter": [],
         "riser": [], "drop": [], "motif": [], "note": []}
    by_scene = {}
    for st, sh in timeline:
        by_scene.setdefault(sh["scene"], []).append((st, sh))

    def s0(sc):
        return by_scene[sc][0][0]

    # 水声：所有洱海场次
    for sc in (12, 17, 18):
        seg = by_scene[sc]
        m["water"].append((seg[0][0], sum(x[1]["dur"] for x in seg)))

    # 快门：场 12 拍照、场 17 陈亦按下、场 23 定格
    for st, sh in timeline:
        if sh["id"] in ("12-10", "17-09", "23-04"):
            m["shutter"].append(st + (1.0 if sh["id"] == "23-04" else 2.2))

    # 主题动机
    m["motif"] += [(s0(12) + 2.0, 2.20, 0.20, 1.2),
                   (s0(18) + 1.5, 2.60, 0.24, 1.0),
                   (s0(23) + 1.0, 2.00, 0.22, 1.3)]
    # 单音
    m["note"] += [(s0(13) + 1.5, "F3", 0.20), (s0(14) + 2.0, "A3", 0.16),
                  (s0(15) + 1.0, "D3", 0.22), (s0(15) + 30.0, "C4", 0.20),
                  (s0(16) + 12.0, "D2", 0.26), (s0(17) + 20.0, "D2", 0.30),
                  (s0(19) + 2.0, "F3", 0.24), (s0(20) + 20.0, "A2", 0.26),
                  (s0(21) + 18.0, "C4", 0.22), (s0(22) + 12.0, "D3", 0.24)]
    # 心跳：场 15 两寸 / 场 19 门内
    m["heart"] += [(s0(15) + 26.0, 18.0), (s0(19), 22.0)]
    # 张力上行：场 17 丢戒指前
    m["riser"] += [(s0(17) + 10.0, 6.0)]
    m["drop"] += [s0(17) + 16.5, s0(20) + 26.0]
    return m


def render(fast=False):
    if fast:
        E.set_resolution(640, 360)
        fps = 12
        out = os.path.join(HERE, "pilot_fast.mp4")
    else:
        E.set_resolution(1280, 720)
        fps = 24
        out = os.path.abspath(os.path.join(HERE, "..",
                                           "说谎的爱人-先导片段-动态分镜.mp4"))
    import pilot_scenes as PSC                        # 必须在设分辨率之后导入

    SLATE = 0.8
    timeline, t = [], 0.0
    last_scene = None
    for sh in PS.SHOTS:
        if sh["scene"] != last_scene:
            timeline.append((t, dict(sh, id="__slate__", dur=SLATE,
                                     kind="slate", scene=sh["scene"])))
            t += SLATE
            last_scene = sh["scene"]
        timeline.append((t, sh))
        t += sh["dur"]
    total = t

    wav = os.path.join(HERE, "pilot_score.wav")
    print("[1/3] 合成配乐 ...", flush=True)
    S.build_score(build_marks(timeline), total, wav)
    print("      %.1fs -> %s" % (total, wav), flush=True)

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (E.W, E.H), "-r", str(fps), "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "22",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    nframes = int(total * fps)
    print("[2/3] 渲染 %d 帧 @ %dfps  (%dx%d) ..." % (nframes, fps, E.W, E.H),
          flush=True)

    done = 0
    for st, sh in timeline:
        n = int(sh["dur"] * fps)
        for i in range(n):
            lt = i / fps
            if sh["kind"] == "slate":
                img = scene_slate(sh["scene"], lt, sh["dur"])
            elif sh["kind"] == "proc":
                fn = PSC.REGISTRY.get(sh["proc"])
                img = E.expose(fn(lt, sh["dur"])) if fn else E.blank()
            else:
                img = shot_card(sh, lt, sh["dur"])

            k = min(E.smoothstep(0, 0.18, lt),
                    1 - E.smoothstep(sh["dur"] - 0.18, sh["dur"], lt))
            proc.stdin.write((np.clip(img * k, 0, 1) * 255)
                             .astype(np.uint8).tobytes())
            done += 1
            if done % 480 == 0:
                print("      %d/%d (%.0f%%)" % (done, nframes,
                                                100 * done / nframes), flush=True)

    proc.stdin.close()
    proc.wait()
    print("[3/3] 完成 -> %s" % out, flush=True)
    return out


if __name__ == "__main__":
    render(fast="--fast" in sys.argv)
