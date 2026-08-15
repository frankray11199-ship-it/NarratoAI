#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《说谎的爱人》程序化配乐合成器
==============================
无采样、无素材库：全部由加法合成 / 滤波噪声 / 包络生成。

音色表：
    drone   低频持续音（婚姻的底噪）
    pluck   拨弦（古筝质感，泛音加法合成 + 指数衰减）
    water   带通噪声（洱海）
    rain    高频噪声（台风夜）
    heart   心跳（低频正弦爆发）
    shutter 快门（瞬态噪声 + 咔哒）
    shatter 碎裂（宽带噪声爆发 + 高频拖尾）
    riser   张力上行（扫频）
"""

import numpy as np
import wave

SR = 44100


def _t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)


def _lp(x, a=0.05):
    """一阶低通（IIR，向量化近似：用移动平均代替以保持速度）"""
    n = max(1, int(1 / a))
    k = np.ones(n, dtype=np.float32) / n
    return np.convolve(x, k, mode="same").astype(np.float32)


def _hp(x, a=0.05):
    return (x - _lp(x, a)).astype(np.float32)


def drone(dur, f0=55.0, amp=0.16):
    t = _t(dur)
    y = np.zeros_like(t)
    for mult, a, det in [(1.0, 1.0, 0.0), (1.0, 0.7, 0.4), (1.5, 0.34, -0.6),
                         (2.0, 0.20, 0.9), (3.0, 0.08, 1.4)]:
        y += a * np.sin(2 * np.pi * (f0 * mult + det) * t)
    lfo = 0.72 + 0.28 * np.sin(2 * np.pi * 0.055 * t)
    env = np.minimum(1.0, t / 2.5) * np.minimum(1.0, (dur - t) / 2.5)
    return (y / 2.4 * lfo * env * amp).astype(np.float32)


def pluck(dur, freq, amp=0.30, decay=2.6, bright=1.0):
    t = _t(dur)
    y = np.zeros_like(t)
    for h in range(1, 13):
        ha = (1.0 / (h ** (1.65 / bright)))
        y += ha * np.sin(2 * np.pi * freq * h * t + h * 0.7)
    env = np.exp(-t * decay)
    atk = np.minimum(1.0, t / 0.006)
    return (y / 3.0 * env * atk * amp).astype(np.float32)


def water(dur, amp=0.10):
    n = np.random.default_rng(9).standard_normal(int(SR * dur)).astype(np.float32)
    y = _lp(n, 0.02)
    t = _t(dur)
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t) * np.sin(2 * np.pi * 0.031 * t)
    env = np.minimum(1.0, t / 3.0) * np.minimum(1.0, (dur - t) / 3.0)
    return (y * mod * env * amp * 6).astype(np.float32)


def rain(dur, amp=0.13):
    n = np.random.default_rng(19).standard_normal(int(SR * dur)).astype(np.float32)
    y = _hp(n, 0.25) * 0.6 + _lp(n, 0.004) * 2.0
    t = _t(dur)
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t + 1.3)
    env = np.minimum(1.0, t / 1.5) * np.minimum(1.0, (dur - t) / 1.5)
    return (y * gust * env * amp).astype(np.float32)


def heart(dur, bpm=52, amp=0.30):
    y = np.zeros(int(SR * dur), dtype=np.float32)
    per = 60.0 / bpm
    k = 0.0
    while k < dur - 0.4:
        for off, a in [(0.0, 1.0), (0.16, 0.62)]:
            s = int((k + off) * SR)
            tt = _t(0.22)
            b = np.sin(2 * np.pi * 46 * tt) * np.exp(-tt * 22) * a
            e = min(len(y), s + len(b))
            y[s:e] += b[:e - s]
        k += per
    return (y * amp).astype(np.float32)


def shutter(amp=0.55):
    t = _t(0.10)
    n = np.random.default_rng(5).standard_normal(len(t)).astype(np.float32)
    click = _hp(n, 0.45) * np.exp(-t * 190)
    body = np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 120) * 0.4
    return ((click + body) * amp).astype(np.float32)


def shatter(dur=1.6, amp=0.45):
    t = _t(dur)
    n = np.random.default_rng(33).standard_normal(len(t)).astype(np.float32)
    burst = _hp(n, 0.35) * np.exp(-t * 7.0)
    tail = _hp(n, 0.6) * np.exp(-t * 1.6) * 0.35
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (4 + i))
               for i, f in enumerate([2300, 3100, 4700, 6100])) * 0.05
    return ((burst + tail + ring) * amp).astype(np.float32)


def riser(dur, f_from=60, f_to=900, amp=0.22):
    t = _t(dur)
    p = t / dur
    inst = f_from * (f_to / f_from) ** p
    ph = 2 * np.pi * np.cumsum(inst) / SR
    y = np.sin(ph) * 0.6
    n = np.random.default_rng(7).standard_normal(len(t)).astype(np.float32)
    y += _hp(n, 0.3) * p * 0.5
    return (y * (p ** 1.8) * amp).astype(np.float32)


def sub_drop(amp=0.5):
    t = _t(2.2)
    inst = 90 * (28 / 90) ** (t / 2.2)
    ph = 2 * np.pi * np.cumsum(inst) / SR
    return (np.sin(ph) * np.exp(-t * 1.1) * amp).astype(np.float32)


# ---------------------------------------------------------------- 混音

NOTES = {"D3": 146.83, "F3": 174.61, "G3": 196.00, "A3": 220.00,
         "C4": 261.63, "D4": 293.66, "F4": 349.23, "A4": 440.00,
         "A2": 110.00, "D2": 73.42}


class Mixer:
    def __init__(self, dur):
        self.dur = dur
        self.buf = np.zeros(int(SR * dur), dtype=np.float32)

    def add(self, sig, at):
        s = int(at * SR)
        if s < 0:
            sig = sig[-s:]
            s = 0
        e = min(len(self.buf), s + len(sig))
        if e > s:
            self.buf[s:e] += sig[:e - s]
        return self

    def out(self, path, peak=0.90):
        y = self.buf
        # 柔性限幅
        y = np.tanh(y * 1.15)
        m = np.max(np.abs(y)) + 1e-9
        y = y / m * peak
        # 简易立体声：右声道微延迟
        d = int(SR * 0.012)
        r = np.concatenate([np.zeros(d, dtype=np.float32), y[:-d]]) * 0.92 + y * 0.08
        st = np.stack([y, r], axis=1)
        pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        return path


def build_score(timeline_marks, total, path):
    """
    timeline_marks: {'water':[(at,dur)], 'rain':[...], 'shutter':[at,...], ...}
    """
    mx = Mixer(total)

    # 全片底噪 drone
    mx.add(drone(total, 55.0, 0.15), 0)
    mx.add(drone(total * 0.55, 82.4, 0.07), total * 0.42)

    for at, d in timeline_marks.get("water", []):
        mx.add(water(d, 0.10), at)
    for at, d in timeline_marks.get("rain", []):
        mx.add(rain(d, 0.14), at)
    for at, d in timeline_marks.get("heart", []):
        mx.add(heart(d, 52, 0.26), at)
    for at in timeline_marks.get("shutter", []):
        mx.add(shutter(0.5), at)
    for at in timeline_marks.get("shatter", []):
        mx.add(shatter(1.8, 0.42), at)
    for at, d in timeline_marks.get("riser", []):
        mx.add(riser(d, 55, 780, 0.20), at)
    for at in timeline_marks.get("drop", []):
        mx.add(sub_drop(0.45), at)

    # 主题动机：D 小调五声，反复出现、每次略变
    motif = ["D3", "F3", "A3", "G3", "F3", "D3"]
    for at, gap, amp, dec in timeline_marks.get("motif", []):
        for i, n in enumerate(motif):
            mx.add(pluck(3.4, NOTES[n], amp, dec, 1.0), at + i * gap)

    for at, note, amp in timeline_marks.get("note", []):
        mx.add(pluck(4.2, NOTES[note], amp, 1.7, 1.15), at)

    return mx.out(path)
