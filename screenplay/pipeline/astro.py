#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天文校验模块
============
用于验证剧本/分镜中的自然光照描述在物理上是否成立。

提供：
    太阳高度角 / 方位角、日出日落、黄金时刻
    月相（照亮比例、月龄）、月亮高度角 / 方位角、月出月落

精度：低精度算法（Meeus 简化），角度误差约 ±0.5°，
     对"有没有月亮、月亮在哪边、圆不圆"这类判定绰绰有余。

所有时间按北京时间 UTC+8 输入。
"""

import math
from datetime import datetime, timedelta

RAD = math.pi / 180.0
CN_TZ = 8.0

# 拍摄地地理坐标
PLACES = {
    "杭州": (30.27, 120.15),
    "大理": (25.60, 100.27),
    "才村码头": (25.66, 100.19),   # 洱海西岸，面向东/东南望湖
    "苍山": (25.68, 100.12),
    "成都": (30.66, 104.06),
}

# 岸线朝向：从该机位望向水面的方位角（度，正北=0，东=90）
SHORE_FACING = {
    "才村码头": 100.0,   # 面向东偏南，湖在东侧
}


def julian_day(dt_utc):
    y, m = dt_utc.year, dt_utc.month
    d = (dt_utc.day + dt_utc.hour / 24.0 + dt_utc.minute / 1440.0
         + dt_utc.second / 86400.0)
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
            + d + b - 1524.5)


def _norm(x, m=360.0):
    return x - m * math.floor(x / m)


def gmst(jd):
    """格林尼治平恒星时（度）"""
    t = (jd - 2451545.0) / 36525.0
    s = (280.46061837 + 360.98564736629 * (jd - 2451545.0)
         + 0.000387933 * t * t - t * t * t / 38710000.0)
    return _norm(s)


def _to_horizon(ra, dec, jd, lat, lon):
    """赤道坐标 -> 地平坐标。ra/dec 单位度，返回 (高度角, 方位角)，方位角正北起顺时针"""
    lst = _norm(gmst(jd) + lon)
    ha = _norm(lst - ra) * RAD
    lat_r, dec_r = lat * RAD, dec * RAD
    alt = math.asin(math.sin(lat_r) * math.sin(dec_r)
                    + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha))
    az = math.atan2(-math.sin(ha),
                    math.tan(dec_r) * math.cos(lat_r)
                    - math.sin(lat_r) * math.cos(ha))
    return alt / RAD, _norm(az / RAD)


def sun_ecliptic(jd):
    """太阳黄经（度）与到地距离修正，低精度"""
    n = jd - 2451545.0
    L = _norm(280.460 + 0.9856474 * n)
    g = _norm(357.528 + 0.9856003 * n) * RAD
    lam = L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
    return _norm(lam)


def obliquity(jd):
    t = (jd - 2451545.0) / 36525.0
    return 23.439291 - 0.0130042 * t


def sun_position(dt_cn, lat, lon):
    jd = julian_day(dt_cn - timedelta(hours=CN_TZ))
    lam = sun_ecliptic(jd) * RAD
    eps = obliquity(jd) * RAD
    ra = _norm(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)) / RAD)
    dec = math.asin(math.sin(eps) * math.sin(lam)) / RAD
    return _to_horizon(ra, dec, jd, lat, lon)


def moon_position(dt_cn, lat, lon):
    """月亮地平坐标 + 月龄 + 照亮比例（Meeus 简化主项）"""
    jd = julian_day(dt_cn - timedelta(hours=CN_TZ))
    t = (jd - 2451545.0) / 36525.0

    Lp = _norm(218.316 + 13.176396 * (jd - 2451545.0))      # 平黄经
    M = _norm(134.963 + 13.064993 * (jd - 2451545.0))       # 月平近点角
    F = _norm(93.272 + 13.229350 * (jd - 2451545.0))        # 升交点角距
    D = _norm(297.850 + 12.190749 * (jd - 2451545.0))       # 日月平距角
    Ms = _norm(357.529 + 0.98560028 * (jd - 2451545.0))     # 太阳平近点角

    Mr, Fr, Dr, Msr = M * RAD, F * RAD, D * RAD, Ms * RAD

    lam = (Lp
           + 6.289 * math.sin(Mr)
           + 1.274 * math.sin(2 * Dr - Mr)
           + 0.658 * math.sin(2 * Dr)
           + 0.214 * math.sin(2 * Mr)
           - 0.186 * math.sin(Msr)
           - 0.114 * math.sin(2 * Fr))
    beta = (5.128 * math.sin(Fr)
            + 0.281 * math.sin(Mr + Fr)
            - 0.278 * math.sin(Fr - Mr)
            - 0.173 * math.sin(2 * Dr - Fr))

    lam_r, beta_r = _norm(lam) * RAD, beta * RAD
    eps = obliquity(jd) * RAD
    ra = _norm(math.atan2(math.sin(lam_r) * math.cos(eps)
                          - math.tan(beta_r) * math.sin(eps),
                          math.cos(lam_r)) / RAD)
    dec = math.asin(math.sin(beta_r) * math.cos(eps)
                    + math.cos(beta_r) * math.sin(eps) * math.sin(lam_r)) / RAD
    alt, az = _to_horizon(ra, dec, jd, lat, lon)

    # 相位：日月黄经差
    elong = _norm(_norm(lam) - sun_ecliptic(jd))
    illum = (1 - math.cos(elong * RAD)) / 2.0
    age = elong / 360.0 * 29.530588

    return dict(alt=alt, az=az, illum=illum, age=age, elong=elong)


def phase_name(age):
    if age < 1.0 or age > 28.8:
        return "朔（不可见）"
    if age < 6.0:
        return "蛾眉月"
    if age < 9.0:
        return "上弦月"
    if age < 13.0:
        return "盈凸月"
    if age < 16.5:
        return "满月"
    if age < 20.5:
        return "亏凸月"
    if age < 23.5:
        return "下弦月"
    return "残月"


def _find_cross(dt0, lat, lon, body, target_alt, step_min=10, span_h=24):
    """在 dt0 起 span_h 小时内寻找高度角穿越 target_alt 的时刻"""
    fn = sun_position if body == "sun" else (lambda d, a, b: (moon_position(d, a, b)["alt"],
                                                              moon_position(d, a, b)["az"]))
    out = []
    prev = None
    n = int(span_h * 60 / step_min)
    for i in range(n + 1):
        d = dt0 + timedelta(minutes=i * step_min)
        alt = fn(d, lat, lon)[0]
        if prev is not None and (prev - target_alt) * (alt - target_alt) < 0:
            out.append((d, "rise" if alt > prev else "set"))
        prev = alt
    return out


def day_events(date_cn, place):
    """返回该日日出日落、月出月落（北京时间）"""
    lat, lon = PLACES[place]
    d0 = datetime(date_cn.year, date_cn.month, date_cn.day, 0, 0)
    sun = _find_cross(d0, lat, lon, "sun", -0.833)
    moon = _find_cross(d0, lat, lon, "moon", 0.125)
    return dict(
        sunrise=next((t for t, k in sun if k == "rise"), None),
        sunset=next((t for t, k in sun if k == "set"), None),
        moonrise=next((t for t, k in moon if k == "rise"), None),
        moonset=next((t for t, k in moon if k == "set"), None),
    )


def light_regime(dt_cn, place):
    """判定该时刻的光照状态"""
    lat, lon = PLACES[place]
    alt, az = sun_position(dt_cn, lat, lon)
    if alt > 50:
        r = "正午强光"
    elif alt > 15:
        r = "常规日光"
    elif alt > 6:
        r = "斜射光"
    elif alt > -0.833:
        r = "黄金时刻"
    elif alt > -6:
        r = "民用曙暮光"
    elif alt > -18:
        r = "天文曙暮光"
    else:
        r = "全黑夜"
    return dict(regime=r, sun_alt=alt, sun_az=az)


def describe(dt_cn, place):
    lat, lon = PLACES[place]
    L = light_regime(dt_cn, place)
    m = moon_position(dt_cn, lat, lon)
    return dict(when=dt_cn.strftime("%Y-%m-%d %H:%M"), place=place,
                regime=L["regime"], sun_alt=round(L["sun_alt"], 1),
                sun_az=round(L["sun_az"], 1),
                moon_alt=round(m["alt"], 1), moon_az=round(m["az"], 1),
                moon_illum=round(m["illum"] * 100, 1),
                moon_age=round(m["age"], 1), moon_phase=phase_name(m["age"]))


if __name__ == "__main__":
    import sys
    tests = [
        (datetime(2024, 4, 9, 21, 30), "才村码头", "原剧本：场18 洱海月夜"),
        (datetime(2024, 4, 23, 21, 30), "才村码头", "候选：4月23日"),
        (datetime(2024, 4, 24, 21, 30), "才村码头", "候选：4月24日"),
        (datetime(2033, 4, 6, 23, 0), "才村码头", "原剧本：场110 尾声"),
        (datetime(2033, 4, 23, 23, 0), "才村码头", "候选尾声：4月23日"),
        (datetime(2024, 4, 9, 12, 30), "才村码头", "场17 船上正午"),
        (datetime(2024, 4, 23, 12, 30), "才村码头", "场17 候选"),
        (datetime(2024, 9, 20, 21, 0), "杭州", "场49 台风夜"),
        (datetime(2024, 11, 21, 20, 40), "杭州", "场68 冲突夜"),
    ]
    for dt, pl, note in tests:
        d = describe(dt, pl)
        print("%-22s %s %-6s | 日高%6.1f° | 月高%6.1f° 方位%5.1f° 照亮%5.1f%% 月龄%4.1f %s"
              % (note, d["when"], d["place"], d["sun_alt"], d["moon_alt"],
                 d["moon_az"], d["moon_illum"], d["moon_age"], d["moon_phase"]))
