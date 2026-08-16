#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《说谎的爱人》8 分钟先导片段 · 镜头表（唯一真源）
==================================================
覆盖场 12—23（大理段落），共 95 个镜头，总时长 480 秒。

本文件是**唯一真源**：
    分镜文档  ← python3 pilot_shots.py --md
    生图提示词 ← python3 pilot_shots.py --jsonl
    动态分镜  ← render/pilot.py 直接 import

镜头类型：
    proc  程序化空镜——本机可直接渲染出真实画面
    dh    数字人镜头——需 FLUX+LoRA 出帧、Wan2.2 转视频

光照数据全部经 pipeline/astro.py 实算，见每场的 LIGHT 注记。
"""

import argparse
import json
import sys

try:
    from characters import CHARACTERS, LOOK, NEG
except ImportError:                                  # 供 render/pilot.py 跨目录导入
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from characters import CHARACTERS, LOOK, NEG


# 每场的实算光照条件（astro.py 输出）
LIGHT = {
    12: "2024-04-20 19:10 才村码头｜太阳高度 +6.9° 斜射光，日落 19:50。"
        "苍山在西，人物逆光；光柱落东侧湖面。色温约 3200K 并持续下降。",
    13: "2024-04-20 21:00 半亩客栈院子｜全黑夜。唯一光源为院中炭火盆（约 1900K），"
        "自下而上打光，人脸下半亮、眼窝深。",
    14: "2024-04-22 10:30 苍山徒步道｜太阳高度 +52°，晴。松林透光形成硬边光斑，"
        "斑块随风移动。",
    15: "2024-04-22 15:20 蝴蝶泉｜太阳高度 +48°。室内展柜为漫射天光 + 柜内冷光管（4000K），"
        "玻璃形成双重反射——这是本场的核心光学母题。",
    16: "2024-04-22 22:30 客栈天台｜全黑夜，月龄 13.4 天盈凸月，照亮 96%，高度 +55°。"
        "月光足以形成清晰轮廓光，无需补光。",
    17: "2024-04-23 12:30 洱海船上｜太阳高度 +72.9° 正午强光，顶光。"
        "水面高光极强，戒指入水后立即不可见。",
    18: "2024-04-23 21:30 才村码头｜满月，照亮 99.8%，高度 +26.9°，方位 120.6°。"
        "月出 19:20。码头面向东偏南约 100°——月光带正落在人物面前，倒影成立。",
    19: "2024-04-25 23:40 半亩客栈 5 号房｜室内，一盏床头台灯（2700K），"
        "关灯后仅余窗外月光（月龄 15.4，照亮 99%）。",
    20: "2024-04-26 07:20 5 号房｜日出 06:50，太阳高度 +6°。"
        "低角度晨光从东窗斜射入室，光带打在床与地面上。",
    21: "2024-04-27 14:00 大理古城银器店｜太阳高度 +66°。"
        "店内为漫射光，柜台上方一束直射天光——银戒举到光下时反光锐利，与铂金难辨。",
    22: "2024-04-29 23:00 5 号房｜室内无灯，仅窗外月光（月龄 19.4，照亮 88%，高度 +18°）。",
    23: "2024-04-30 11:00 大理机场｜候机厅顶部漫射天光 + 大面积落地窗侧光。",
}


def S(sid, scene, dur, size, move, kind, desc, dialogue="", proc=None,
      prompt="", motion="", char=None, note=""):
    return dict(id=sid, scene=scene, dur=dur, size=size, move=move, kind=kind,
                desc=desc, dialogue=dialogue, proc=proc, prompt=prompt,
                motion=motion, char=char, note=note)


# ================================================================
#  场 12 · 才村码头 · 初见（62s）
# ================================================================
SHOTS = [
    S("12-01", 12, 8.0, "大远景", "固定", "proc",
      "洱海全景。风起。远山在逆光里只剩轮廓。",
      proc="lake_dusk",
      note="开场镜头。声音先入：风、水、极远处的船机声。"),
    S("12-02", 12, 6.0, "全景", "缓推", "dh",
      "见月站在木栈道尽头，风把她头发全部吹到一侧。她背对镜头。",
      char="林见月",
      prompt="standing alone at the end of a wooden pier on a vast highland lake, "
             "seen from behind, strong wind blowing all her hair to one side, "
             "distant mountains in silhouette, golden hour backlight",
      motion="slow dolly in, hair and coat moving continuously in the wind, "
             "water rippling, no cuts"),
    S("12-03", 12, 5.0, "中近景", "固定", "dh",
      "她举起手机对着苍山，举了很久，放下。",
      char="林见月",
      prompt="raising a phone to photograph distant mountains, holding it up "
             "for a long moment, then lowering it, backlit rim light on her cheek",
      motion="she raises the phone, holds, then lowers it; subtle disappointment"),
    S("12-04", 12, 5.0, "中景", "固定", "dh",
      "画面右后方，一个男人在架三脚架。**他始终被三脚架的支腿切割**。",
      char="陈亦",
      prompt="a man setting up a camera tripod on the pier, his body partially "
             "cut by the tripod legs in the foreground, out of focus",
      motion="he extends the tripod legs, adjusts the head, never fully revealed",
      note="陈亦规则第一次执行：他从此不再有无遮挡的镜头。"),
    S("12-05", 12, 4.0, "近景", "固定", "dh",
      "见月回头。", "（回头）什么？", char="林见月",
      prompt="turning her head sharply toward camera, wind in her hair, "
             "questioning expression, golden backlight",
      motion="head turn, hair follows with a beat of delay"),
    S("12-06", 12, 8.0, "中近景", "固定", "dh",
      "陈亦眼睛没离开取景器。",
      "苍山，现在这个云，四十分钟以后会开一条缝，光从那儿下来。你要拍的是那个。",
      char="陈亦",
      prompt="a man speaking while still looking through his camera viewfinder, "
             "face half hidden behind the camera body, calm and certain",
      motion="he speaks without looking up, one hand adjusting focus ring"),
    S("12-07", 12, 6.0, "远景", "缓摇", "proc",
      "苍山。云层压得很低，一线未开。",
      proc="god_rays_closed"),
    S("12-08", 12, 3.0, "特写", "固定", "dh",
      "见月侧脸。她看了他一眼——第一次认真地看。", char="林见月",
      prompt="extreme close-up of her profile, eyes shifting sideways to look at "
             "someone off-frame, a flicker of curiosity",
      motion="only the eyes move"),
    S("12-09", 12, 9.0, "远景", "固定", "proc",
      "四十分钟后。云真的开了。光柱落在湖面上。",
      proc="god_rays_open",
      note="全片唯一一次陈亦说了完全的真话，且这句话可被天文验证：日落 19:50。"),
    S("12-10", 12, 4.0, "中景", "固定", "dh",
      "见月按下快门。", char="林见月",
      prompt="pressing the shutter on her phone, face lit by the sudden light "
             "shaft on the water, mouth slightly open",
      motion="she presses, then keeps looking"),
    S("12-11", 12, 4.0, "全景", "固定", "dh",
      "她转身想说什么。那个人已经在收三脚架。", char="林见月",
      prompt="she turns to speak, but the man behind her is already folding his "
             "tripod, back turned, leaving",
      motion="she turns; he is already walking away"),

    # ============================================================
    #  场 13 · 半亩客栈院子 · 夜（30s）
    # ============================================================
    S("13-01", 13, 6.0, "全景", "固定", "proc",
      "客栈院子。一盆炭火。四周极暗。",
      proc="brazier"),
    S("13-02", 13, 5.0, "中景", "固定", "dh",
      "见月办入住，抬头。", char="林见月",
      prompt="checking in at a guesthouse counter at night, looking up, "
             "warm firelight from below on her face",
      motion="she signs, then looks up"),
    S("13-03", 13, 5.0, "中近景", "固定", "dh",
      "陈亦坐在火边看相机回放，脸被相机屏幕照亮。**火盆的支架横切过他的身体。**",
      "住 3 号？我住 5 号。", char="陈亦",
      prompt="seated by a brazier reviewing images on a camera screen, his face "
             "lit from below by the screen, a brazier stand crossing his torso",
      motion="he scrolls through images, then looks up"),
    S("13-04", 13, 4.0, "近景", "固定", "dh",
      "见月。", "……你算得挺准。", char="林见月",
      prompt="a small guarded almost-smile, firelight from below",
      motion="a beat, then the corner of her mouth moves"),
    S("13-05", 13, 6.0, "中景", "固定", "dh",
      "老板娘端来两杯梅子酒。",
      "老板娘：两位一起的？／两人（同时）：不是。",
      char="林见月",
      prompt="a guesthouse owner setting down two cups of plum wine between "
             "two guests seated apart by the fire",
      motion="cups set down, both guests answer at once, then both laugh"),
    S("13-06", 13, 4.0, "特写", "固定", "proc",
      "两只酒杯。火光在酒面上晃。",
      proc="two_cups"),

    # ============================================================
    #  场 14 · 苍山徒步道 · 日（42s）
    # ============================================================
    S("14-01", 14, 5.0, "远景", "固定", "proc",
      "松林。硬边光斑随风在地面移动。",
      proc="forest_light"),
    S("14-02", 14, 5.0, "中景", "跟移", "dh",
      "两人同行。陈亦举着相机拍她，她躲。", char="林见月",
      prompt="two people walking a mountain trail, one raising a camera at the "
             "other who turns away, dappled hard light through pines",
      motion="walking, she turns her face away from the lens"),
    S("14-03", 14, 3.0, "近景", "固定", "dh",
      "", "别拍我。", char="林见月",
      prompt="turning her face away from a camera, mild irritation, dappled light",
      motion="face turns away"),
    S("14-04", 14, 3.0, "近景", "固定", "dh",
      "**陈亦的脸被相机机身遮住一半。**", "为什么。", char="陈亦",
      prompt="half his face hidden behind a camera body, one visible eye",
      motion="he lowers the camera slightly, revealing one eye"),
    S("14-05", 14, 3.0, "近景", "固定", "dh",
      "", "不好看。", char="林见月",
      prompt="a flat self-deprecating expression, eyes lowered",
      motion="she looks down"),
    S("14-06", 14, 11.0, "中近景", "缓推", "dh",
      "陈亦放下相机。这是他全片说得最像真话的一段谎。",
      "取景框是骗人的。框里的东西你看着最真，其实全是我挑出来的。真东西都在框外面。",
      char="陈亦",
      prompt="lowering the camera to speak, his forearm still crossing the lower "
             "frame, sunlight through pines moving across his face",
      motion="he lowers the camera and speaks, light patches drifting over him",
      note="伏笔 5 埋设点。回收于场 78（何雨：框外面站着的是我）与场 105。"),
    S("14-07", 14, 7.0, "主观", "手持", "proc",
      "见月的视角切进取景框：世界被裁掉了四边。",
      proc="viewfinder"),
    S("14-08", 14, 5.0, "特写", "固定", "dh",
      "见月看着他。第一次认真地看。", char="林见月",
      prompt="looking directly at someone for the first time with real attention, "
             "the guardedness briefly gone",
      motion="a long look, one slow blink"),

    # ============================================================
    #  场 15 · 蝴蝶泉 · 日（58s）
    # ============================================================
    S("15-01", 15, 7.0, "特写", "缓推", "proc",
      "玻璃柜里的蝴蝶标本。翅膀展得极完美。一根钉子穿过胸腔。",
      proc="butterfly",
      note="伏笔 16 埋设点。"),
    S("15-02", 15, 3.0, "近景", "固定", "dh",
      "", "好看。", char="林见月",
      prompt="looking into a museum display case, cool fluorescent light on her "
             "face, glass reflections overlaying her features",
      motion="she leans slightly closer to the glass"),
    S("15-03", 15, 7.0, "中近景", "固定", "dh",
      "**陈亦的脸出现在玻璃反射里——他本人在框外。**",
      "钉住了才好看。飞着的时候，你根本看不清它长什么样。",
      char="陈亦",
      prompt="his face appearing only as a reflection in the display glass, his "
             "actual body outside the frame",
      motion="the reflection speaks; the real man is never shown in this shot",
      note="全片对'框外'规则最直接的一次视觉执行。"),
    S("15-04", 15, 5.0, "特写", "固定", "dh",
      "见月伸手贴在玻璃上。婚戒磕在玻璃上，'嗒'的一声。",
      char="林见月",
      prompt="a hand pressed flat against display glass, a plain platinum wedding "
             "band clicking against the surface, macro",
      motion="palm meets glass, the ring taps once — audible",
      note="道具核对：此时为**真戒**，铂金，反光锐。"),
    S("15-05", 15, 4.0, "中景", "固定", "dh",
      "两人都听见了。都没提。", char="林见月",
      prompt="two people beside a display case, both having heard something "
             "neither will mention, a held silence",
      motion="neither moves; a two-second stillness"),
    S("15-06", 15, 9.0, "中近景", "固定", "dh",
      "陈亦走到她身后，没有碰她。他抬手指着玻璃里的一只蓝蝶。"
      "**手臂从她肩侧越过去，隔着两寸。**",
      "这只，翅膀是破的。", char="陈亦",
      prompt="a man reaching past a woman's shoulder to point at something in a "
             "display case, his forearm two inches from her, not touching",
      motion="the arm comes in slowly and stops; the gap is the subject of the shot",
      note="全片最远的两寸。这一场的张力全部押在这个距离上。"),
    S("15-07", 15, 4.0, "特写", "固定", "dh",
      "", "……在哪儿。", char="林见月",
      prompt="close on her face, not turning around, breath held",
      motion="she does not turn; her jaw tightens"),
    S("15-08", 15, 4.0, "特写", "固定", "dh",
      "", "左边。你得靠近看。", char="陈亦",
      prompt="his mouth close to the edge of frame, speaking low",
      motion="only lips move"),
    S("15-09", 15, 8.0, "特写", "固定", "proc",
      "见月往前倾。**她的后背碰到了他的胸口。**"
      "玻璃上出现两道呼吸的雾，一大一小，慢慢连成一片。",
      proc="breath_fog",
      note="不拍人，拍玻璃。这是全片处理亲密最核心的一次替换。"),
    S("15-10", 15, 4.0, "中景", "固定", "dh",
      "见月直起身，退开半步。", "我没看见破的。／（笑）那可能是我看错了。",
      char="林见月",
      prompt="straightening up and stepping back half a pace, composing herself",
      motion="she straightens, steps back; he lets her",
      note="他们谁都知道没看错。"),
    S("15-11", 15, 3.0, "特写", "固定", "proc",
      "玻璃上那片雾慢慢散掉。钉住的蝴蝶还在。",
      proc="breath_fog_fade"),

    # ============================================================
    #  场 16 · 客栈天台 · 夜（40s）
    # ============================================================
    S("16-01", 16, 5.0, "远景", "固定", "proc",
      "天台。盈凸月照亮 96%，星空可见。",
      proc="night_sky"),
    S("16-02", 16, 5.0, "中景", "固定", "dh",
      "两人隔着一张小桌喝酒。月光形成清晰轮廓光。", char="林见月",
      prompt="two people drinking at a small rooftop table under a bright "
             "gibbous moon, strong rim light, no fill",
      motion="she turns her cup slowly on the table"),
    S("16-03", 16, 4.0, "近景", "固定", "dh",
      "", "你一个人出来拍？", char="林见月",
      prompt="asking a casual question, moonlight rim on her cheek",
      motion="she asks without looking at him"),
    S("16-04", 16, 6.0, "近景", "固定", "dh",
      "**停顿约半秒**——这半秒就是全片的答案。",
      "（停顿）嗯，我一个人。", char="陈亦",
      prompt="a half-second hesitation before answering, his face half in shadow, "
             "a railing post crossing the frame in front of him",
      motion="a micro-pause before the mouth moves — the pause must be visible",
      note="伏笔 12 第一谎。0.5 秒的迟疑是全片最重要的表演指令。"),
    S("16-05", 16, 4.0, "近景", "固定", "dh",
      "", "家里不管你？／（笑）我没什么家。", char="陈亦",
      prompt="an easy relaxed lie delivered with a half-smile",
      motion="he smiles; the smile does not reach the eyes"),
    S("16-06", 16, 7.0, "特写", "固定", "proc",
      "**桌上的手机屏幕亮了一下又暗了。画面里有个很小的、像是小孩的影子。**"
      "一只手把手机翻扣过去。",
      proc="phone_flash",
      note="伏笔 12 的视觉物证。此镜必须真的拍出来，否则场 78 无法回收。"),
    S("16-07", 16, 5.0, "近景", "固定", "dh",
      "", "你呢。／我结婚八年了。", char="林见月",
      prompt="stating a fact flatly, looking at her own hands",
      motion="she says it to her hands, not to him"),
    S("16-08", 16, 4.0, "近景", "固定", "dh",
      "他没有问下去。**这是他最聪明的一次沉默。**", "（很轻）嗯。",
      char="陈亦",
      prompt="receiving information and choosing not to pursue it, a single nod",
      motion="one small nod, then he looks away at the sky"),

    # ============================================================
    #  场 17 · 洱海船上 · 正午（55s）
    # ============================================================
    S("17-01", 17, 6.0, "大远景", "固定", "proc",
      "正午的洱海。太阳高度 72.9°，顶光。水面高光刺眼。",
      proc="lake_noon"),
    S("17-02", 17, 5.0, "中景", "手持", "dh",
      "小木船。日头很烈。见月眯着眼。", char="林见月",
      prompt="on a small wooden boat in harsh overhead noon sun, squinting, "
             "top light carving hard shadows under the brow and nose",
      motion="the boat rocks; she squints against the glare"),
    S("17-03", 17, 5.0, "特写", "固定", "dh",
      "她把手伸进水里划。手腕上的水花。", char="林见月",
      prompt="a hand trailing in bright lake water from the side of a boat, "
             "harsh specular glitter, macro on the wrist",
      motion="the hand cuts through water, spray catching the sun",
      note="道具核对：入水前**婚戒仍在**。此镜必须清楚拍到戒指。"),
    S("17-04", 17, 3.0, "近景", "固定", "dh",
      "", "小心。／（笑）这么点浪。", char="陈亦",
      prompt="a warning spoken from behind a camera he is holding",
      motion="he speaks, camera still at chest height"),
    S("17-05", 17, 6.0, "特写", "固定", "proc",
      "**戒指脱手，沉入水中。**光斑一层层掠过它，越来越暗。",
      proc="ring_sink",
      note="伏笔 4 埋设点。此后至场 21 她无名指为空。"),
    S("17-06", 17, 4.0, "特写", "固定", "dh",
      "见月把手抽出来。**无名指是空的。**她愣住。", char="林见月",
      prompt="pulling a wet hand out of the water, macro on the bare ring finger, "
             "the moment of realisation",
      motion="the hand comes up; the fingers spread; everything stops",
      note="道具核对：从本镜起，直到场 21，左手无名指必须为空。"),
    S("17-07", 17, 6.0, "中景", "手持", "dh",
      "她猛地趴到船舷上去看。水面上只有一圈一圈的光。", char="林见月",
      prompt="lunging to the gunwale to look down into the water, the surface "
             "showing only rings of light",
      motion="a sudden lunge, the boat tips, water slaps the hull"),
    S("17-08", 17, 8.0, "近景", "手持", "dh",
      "她伸手去捞。**捞了三次。**", "船家：捞不上来的。／（笑，但眼睛是红的）我知道。",
      char="林见月",
      prompt="reaching into the water again and again, three times, "
             "laughing while her eyes redden",
      motion="three distinct attempts, each shallower than the last",
      note="这个动作在场 110（九年后）原样复现——但那次水里什么都没有。"),
    S("17-09", 17, 6.0, "中景", "固定", "dh",
      "**陈亦举起相机，拍下了这一刻。快门声。**", char="陈亦",
      prompt="raising a camera to photograph a woman's private moment of loss, "
             "his face behind the body of the camera",
      motion="he raises, frames, and presses — no hesitation",
      note="这张照片八个月后成为场 49 周砚手里的物证。"),

    # ============================================================
    #  场 18 · 洱海边 · 满月夜（48s）
    # ============================================================
    S("18-01", 18, 10.0, "大远景", "固定", "proc",
      "满月。照亮 99.8%，高度角 26.9°，方位 120.6°。"
      "月光带正落在人物面前的湖面上，碎成一片一片。",
      proc="water_moon",
      note="天文实算成立。换任何日期均无此天象——拍摄窗口不可移动。"),
    S("18-02", 18, 5.0, "全景", "固定", "dh",
      "两人并肩坐在水边。月光是唯一光源。", char="林见月",
      prompt="two people sitting side by side at the water's edge under a full "
             "moon, moonlight the only source, the moon path on the water "
             "directly in front of them",
      motion="almost still; only water moves"),
    S("18-03", 18, 4.0, "近景", "固定", "dh",
      "", "你名字里有个月。", char="陈亦",
      prompt="speaking quietly in moonlight, half his face in shadow",
      motion="he speaks without turning"),
    S("18-04", 18, 7.0, "近景", "固定", "dh",
      "", "我妈说，生我那天晚上月亮特别好。", char="林见月",
      prompt="recounting something her mother told her, moonlight rim on her face",
      motion="a small smile that fades",
      note="经天文核实为真：1990-02-04 夜杭州，照亮 69.8%，高度角 69.1°。"),
    S("18-05", 18, 4.0, "近景", "固定", "dh",
      "", "见月。看见月亮。", char="陈亦",
      prompt="saying her name slowly, testing it",
      motion="lips shape the two syllables"),
    S("18-06", 18, 7.0, "特写", "固定", "dh",
      "她看着水面。",
      "我妈没告诉我，水里这个是捞不起来的。", char="林见月",
      prompt="looking down at the moon's reflection on the water, "
             "the reflection visible in her eyes",
      motion="her eyes track the broken reflection"),
    S("18-07", 18, 5.0, "特写", "固定", "dh",
      "**陈亦握住了她的手。她没有抽走。**空无名指。", char="林见月",
      prompt="a man's hand closing over a woman's hand, macro, "
             "her ring finger visibly bare",
      motion="his hand arrives; hers does not withdraw",
      note="道具核对：无名指为空——这是他知道她丢了戒指的那一刻。"),
    S("18-08", 18, 6.0, "特写", "固定", "proc",
      "镜头留在水面上的月亮。**波纹一过，散了。**",
      proc="water_moon_break"),

    # ============================================================
    #  场 19 · 5 号房 · 夜（38s）
    # ============================================================
    S("19-01", 19, 5.0, "中景", "固定", "dh",
      "门在身后关上。见月背贴着门站着，胸口起伏。", char="林见月",
      prompt="standing with her back pressed against a closed hotel room door, "
             "chest rising and falling, one warm bedside lamp",
      motion="breathing, visibly; she does not move otherwise"),
    S("19-02", 19, 4.0, "中景", "固定", "dh",
      "陈亦走过来，停在半步之外。", "你可以走。", char="陈亦",
      prompt="stopping half a step away, a doorframe edge crossing the frame",
      motion="he stops; the gap holds"),
    S("19-03", 19, 5.0, "近景", "固定", "dh",
      "", "（很久）我知道。", char="林见月",
      prompt="a long pause before answering, eyes down then up",
      motion="a long beat, then she raises her eyes"),
    S("19-04", 19, 6.0, "近景", "固定", "dh",
      "**他吻了她。**不重。像是在确认一件事，不是在索取。",
      char="林见月",
      prompt="a restrained kiss, more a confirmation than a demand, "
             "warm lamplight from one side",
      motion="the kiss is brief and still; no hands move at first",
      note="表演指令：此吻不得表现为索取。全片的情欲都建立在'确认'而非'占有'上。"),
    S("19-05", 19, 6.0, "特写", "固定", "dh",
      "她的右手抬起来，抓住他的衬衫下摆——**攥得很紧，指节发白。**",
      char="林见月",
      prompt="macro on a hand gripping the hem of a shirt, knuckles white, "
             "like holding onto something that is falling",
      motion="the fingers close and tighten; the knuckles blanch",
      note="这只手在七个月后（场 68）会被瓷片割断肌腱。"),
    S("19-06", 19, 5.0, "近景", "固定", "dh",
      "两人隔着五厘米喘气。", "还走吗。／（气音）……你别说话。",
      char="林见月",
      prompt="two faces five centimetres apart, both breathing hard, not kissing",
      motion="breath only"),
    S("19-07", 19, 7.0, "中景", "固定", "dh",
      "她把脸埋进他的颈窝。",
      "（很轻，几乎听不见）我今天想当一次别人。", char="林见月",
      prompt="burying her face in the crook of his neck, her expression hidden",
      motion="she moves in; her face disappears from view as she speaks",
      note="全片她唯一一次说出自己要什么。与场 33、场 89 构成动机三段链。"),

    # ============================================================
    #  场 19B · 关灯（8s，纯程序化）
    # ============================================================
    S("19B-01", 19, 4.0, "特写", "固定", "proc",
      "一只手伸向台灯。**关灯。**",
      proc="lamp_off"),
    S("19B-02", 19, 4.0, "黑场", "—", "proc",
      "黑屏。手机在黑暗里亮起来，来电显示'周砚'。响了很久，暗下去。",
      proc="phone_ringing",
      note="全片的转折点用一块黑屏和一个来电完成。此处不拍任何身体。"),

    # ============================================================
    #  场 20 · 5 号房 · 晨（38s）
    # ============================================================
    S("20-01", 20, 5.0, "中景", "固定", "proc",
      "低角度晨光从东窗斜射入室，光带打在床和地面上。太阳高度 +6°。",
      proc="morning_light"),
    S("20-02", 20, 5.0, "特写", "固定", "dh",
      "见月醒来，第一件事是摸自己的左手无名指——**空的。**",
      char="林见月",
      prompt="waking and immediately touching her own bare left ring finger, "
             "low golden morning light raking across the bed",
      motion="the hand finds the empty finger and stops"),
    S("20-03", 20, 8.0, "中景", "固定", "dh",
      "她坐起来，回拨电话。",
      "喂？昨晚睡着了……嗯，挺好的。苍山上信号不好。", char="林见月",
      prompt="sitting up in bed making a phone call, her voice flat and "
             "controlled, morning light behind her",
      motion="she sits, dials, speaks — her body language completely calm"),
    S("20-04", 20, 6.0, "特写", "固定", "dh",
      "**她摸了一下左耳。**", "我明天去双廊，后天回。", char="林见月",
      prompt="macro on her hand touching her left ear while speaking on the phone",
      motion="the hand rises to the ear mid-sentence",
      note="伏笔 23。观众已在场 2 见过这个动作——此处是第二次，开始有意义。"),
    S("20-05", 20, 8.0, "近景", "固定", "dh",
      "陈亦从背后看着她。", "你说谎的时候，会摸左边耳朵。", char="陈亦",
      prompt="watching her from behind in bed, his face partially behind her "
             "shoulder, speaking a quiet observation",
      motion="he speaks; she freezes mid-motion"),
    S("20-06", 20, 6.0, "近景", "固定", "dh",
      "见月的手僵在半空。", "……你怎么知道。／我拍了你一个星期。",
      char="林见月",
      prompt="her hand frozen in mid-air, the blood draining from her expression",
      motion="total stillness — the hand must not come down"),

    # ============================================================
    #  场 21 · 银器店 · 日（32s）
    # ============================================================
    S("21-01", 21, 5.0, "中景", "固定", "dh",
      "见月站在柜台前，指着一枚素圈银戒。", char="林见月",
      prompt="standing at a silver shop counter pointing at a plain band ring, "
             "diffuse interior light with one shaft of direct daylight on the counter",
      motion="she points; the shopkeeper reaches for it"),
    S("21-02", 21, 6.0, "近景", "固定", "dh",
      "", "这个，能做成看起来像铂金的吗？／能镀白金，一模一样，外行看不出。",
      char="林见月",
      prompt="asking a question she has clearly rehearsed, avoiding eye contact",
      motion="she asks without looking at the shopkeeper"),
    S("21-03", 21, 7.0, "近景", "固定", "dh",
      "", "（顿了顿）多沉？／轻不少。银比铂金轻多了，戴上就知道。／没事。",
      char="林见月",
      prompt="a pause before asking about weight, then dismissing the answer",
      motion="a visible hesitation, then a small shake of the head",
      note="她问了重量，也听见了答案，然后选择忽略。八个月后周砚正是靠重量识破的。"),
    S("21-04", 21, 8.0, "特写", "固定", "proc",
      "她戴上。举起手，在那束直射天光下看。**它和真的没有区别。只是轻。**",
      proc="ring_sunlight",
      note="道具核对：从本镜起至全片终，均为**镀白金银戒**——"
           "反光更漫、边缘更钝。场 109 它会氧化发黑，且摘不下来。"),
    S("21-05", 21, 6.0, "特写", "固定", "dh",
      "她放下手。**手垂下去的时候，比戴真戒指时快了一点。**", char="林见月",
      prompt="lowering the hand after examining the ring, macro",
      motion="the hand drops slightly faster than it should — it weighs less",
      note="表演指令：这一点点的'快'，是全片唯一一次让观众用眼睛看见重量差。"),

    # ============================================================
    #  场 22 · 5 号房 · 最后一夜（22s）
    # ============================================================
    S("22-01", 22, 5.0, "中景", "固定", "dh",
      "最后一夜。窗外月光，室内无灯。", "回去以后呢。", char="陈亦",
      prompt="a dark room lit only by moonlight through a window, "
             "a man asking a question from the shadows",
      motion="minimal movement; the room is nearly still"),
    S("22-02", 22, 5.0, "近景", "固定", "dh",
      "", "回去以后就没有以后了。", char="林见月",
      prompt="a flat definitive statement, moonlight on one side of her face",
      motion="she says it cleanly, without hesitation"),
    S("22-03", 22, 6.0, "近景", "固定", "dh",
      "", "（笑）你说这句的时候，没摸耳朵。", char="陈亦",
      prompt="a quiet amused observation delivered as a verdict",
      motion="a short laugh, then stillness"),
    S("22-04", 22, 6.0, "特写", "固定", "dh",
      "见月怔住。", "所以你自己也知道，这句是假的。", char="林见月",
      prompt="the moment of being caught by her own tell, eyes widening slightly",
      motion="a flinch that does not become an expression",
      note="伏笔 23 的第三次使用。她在场 56 会用同一个方法识破陈亦。"),

    # ============================================================
    #  场 23 · 大理机场 · 日（25s）
    # ============================================================
    S("23-01", 23, 6.0, "全景", "固定", "dh",
      "安检口。两人隔着五米站着，谁也没有走近。", char="林见月",
      prompt="two people standing five metres apart at an airport security "
             "checkpoint, neither approaching, diffuse skylight and window light",
      motion="crowds move around them; the two do not"),
    S("23-02", 23, 5.0, "中景", "固定", "dh",
      "**陈亦举起相机，对着她。**", char="陈亦",
      prompt="raising a camera toward someone across a departure hall, "
             "his face going behind the body of the camera",
      motion="the camera comes up and covers his face completely",
      note="他最后一次出现在这个段落里，脸被相机完全遮住——规则闭环。"),
    S("23-03", 23, 6.0, "近景", "固定", "dh",
      "**她没有躲。**", char="林见月",
      prompt="not turning away from a lens for the first time, "
             "looking directly into it",
      motion="she holds the look; she does not move",
      note="对位场 14-03：那时她躲，现在她不躲了。"),
    S("23-04", 23, 8.0, "特写", "固定", "proc",
      "**快门声。定格。**画面凝成一张照片，边缘出现相纸的白边。",
      proc="shutter_freeze",
      note="先导片段结束镜头。这张照片就是场 49 周砚放在桌上的那一张。"),
]


# ================================================================

def total():
    return sum(s["dur"] for s in SHOTS)


def scene_dur(scene):
    return sum(s["dur"] for s in SHOTS if s["scene"] == scene)


def timecode(sec):
    return "%02d:%02d:%02d" % (int(sec) // 60, int(sec) % 60,
                               int(round((sec - int(sec)) * 24)))


def with_timecodes():
    t = 0.0
    out = []
    for s in SHOTS:
        s = dict(s)
        s["tc_in"] = timecode(t)
        s["start"] = t
        t += s["dur"]
        s["tc_out"] = timecode(t)
        out.append(s)
    return out


def export_prompts():
    """导出数字人镜头的生图 + 图生视频提示词"""
    out = []
    for s in with_timecodes():
        if s["kind"] != "dh":
            continue
        c = CHARACTERS[s["char"]]
        stage = "2024大理" if s["char"] == "林见月" else "全片"
        st = c["stages"].get(stage, "")
        out.append(dict(
            shot=s["id"], scene=s["scene"], character=s["char"],
            tc_in=s["tc_in"], duration=s["dur"],
            lora=c["trigger"],
            prompt="%s, %s, %s, %s" % (LOOK, c["base"], st, s["prompt"]),
            negative=NEG,
            motion=s["motion"],
            width=1920, height=816,
            seed=30000 + int(s["id"].replace("-", "").replace("B", "9"))))
    return out


def to_markdown():
    L = []
    A = L.append
    A("# 《说谎的爱人》· 8 分钟先导片段 · 分镜表\n")
    A("**覆盖**：场 12—23（大理段落）　**镜头数**：%d　**总时长**：%.1f 秒（%s）\n"
      % (len(SHOTS), total(), timecode(total())))
    A("> 本表由 `pipeline/pilot_shots.py` 生成，是分镜的唯一真源。")
    A("> 修改镜头请改该文件，勿直接编辑本文档。\n")
    A("**镜头类型**：`proc` 程序化空镜（本机可直接渲染）　"
      "`dh` 数字人镜头（需 FLUX+LoRA 出帧 → Wan2.2 转视频）\n")
    n_proc = sum(1 for s in SHOTS if s["kind"] == "proc")
    A("统计：程序化空镜 **%d** 镜 / %.0f 秒　·　数字人镜头 **%d** 镜 / %.0f 秒\n"
      % (n_proc, sum(s["dur"] for s in SHOTS if s["kind"] == "proc"),
         len(SHOTS) - n_proc, sum(s["dur"] for s in SHOTS if s["kind"] == "dh")))
    A("\n---\n")

    cur = None
    for s in with_timecodes():
        if s["scene"] != cur:
            cur = s["scene"]
            A("\n## 场 %d　（本场 %.0f 秒）\n" % (cur, scene_dur(cur)))
            A("> **光照实算**：%s\n" % LIGHT[cur])
            A("\n| 镜号 | 入点 | 时长 | 景别 | 运镜 | 类型 | 内容 |")
            A("|---|---|---|---|---|---|---|")
        d = s["desc"].replace("\n", " ")
        if s["dialogue"]:
            d += "<br>**台词**：" + s["dialogue"]
        if s["note"]:
            d += "<br>*※ " + s["note"] + "*"
        A("| `%s` | %s | %.1fs | %s | %s | `%s` | %s |"
          % (s["id"], s["tc_in"], s["dur"], s["size"], s["move"], s["kind"], d))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true", help="输出分镜表 markdown")
    ap.add_argument("--jsonl", help="导出数字人镜头提示词")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    if a.md:
        print(to_markdown())
    elif a.jsonl:
        items = export_prompts()
        with open(a.jsonl, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        print("导出 %d 个数字人镜头 -> %s" % (len(items), a.jsonl))
    else:
        n_proc = sum(1 for s in SHOTS if s["kind"] == "proc")
        print("镜头总数 %d　总时长 %.1fs (%s)" % (len(SHOTS), total(), timecode(total())))
        print("  程序化空镜 %d 镜 / %.0fs" % (n_proc, sum(s["dur"] for s in SHOTS if s["kind"] == "proc")))
        print("  数字人镜头 %d 镜 / %.0fs" % (len(SHOTS) - n_proc, sum(s["dur"] for s in SHOTS if s["kind"] == "dh")))
        for sc in sorted(set(s["scene"] for s in SHOTS)):
            print("    场 %-3d %5.1fs  %d 镜" % (sc, scene_dur(sc),
                                                sum(1 for s in SHOTS if s["scene"] == sc)))


if __name__ == "__main__":
    main()
