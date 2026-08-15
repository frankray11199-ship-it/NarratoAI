#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《说谎的爱人》数字人角色库 + 批量提示词生成器
==============================================
角色形象均为原创设定，不以任何真实个人照片为基准。

用法:
    python3 characters.py --list                 列出角色
    python3 characters.py --sheet 林见月          出该角色的一致性训练集提示词(40条)
    python3 characters.py --shots                出全片关键镜头提示词
    python3 characters.py --jsonl out.jsonl      导出为批量生成任务
"""

import argparse
import json
import itertools

# ---------------------------------------------------------------- 统一规格

LOOK = ("shot on ARRI Alexa, 40mm anamorphic lens, T2.0, shallow depth of field, "
        "natural available light, motivated practical sources only, "
        "muted desaturated palette, teal-leaning shadows, warm skin falloff, "
        "Kodak Vision3 500T film emulation, visible fine grain, "
        "photorealistic skin texture with visible pores and fine vellus hair, "
        "no beauty retouching, no skin smoothing, no makeup gloss, "
        "cinematic color grading")

NEG = ("cgi, 3d render, plastic skin, airbrushed, beauty filter, smooth skin, "
       "doll-like, oversaturated, hdr, instagram filter, glamour lighting, "
       "symmetrical perfect face, anime, illustration, painting, "
       "extra fingers, deformed hands, watermark, text, logo, "
       "duplicate face, multiple people, celebrity likeness")

# ---------------------------------------------------------------- 角色库

CHARACTERS = {
    "林见月": dict(
        key="ljy", trigger="ljy_woman", age=34, role="陶瓷修复师 · 女主",
        base=("a 34-year-old East Asian woman, Chinese, southern Chinese features, "
              "long oval face with a narrow jaw, slightly asymmetric, "
              "inner double eyelids that read almost monolid in low light, "
              "straight sparse eyebrows with a low arch, "
              "narrow high nose bridge with a slightly rounded tip, "
              "thin upper lip and fuller lower lip, natural pale lip color, "
              "a single small dark mole on the left jawline below the ear, "
              "faint nasolabial lines, tired under-eyes with mild pigmentation, "
              "shoulder-length dark brown hair, slightly wavy, usually pinned up "
              "with loose strands at the temples, "
              "bare face, no makeup, slightly dry skin, "
              "quiet closed expression, eyes that do not fully engage the camera"),
        stages={
            "2024春": "hair pinned up, grey-blue linen apron, no jewellery except a plain wedding band, flat affect, hollow gaze",
            "2024大理": "hair down, faint high-altitude sun flush on the cheeks, the first laugh lines appear",
            "2024秋": "very light makeup but a visible lip colour, a new brightness in the eyes",
            "2024冬": "right hand bandaged, ashen complexion, undyed roots showing",
            "2025春": "sunken eye sockets, drained lip colour, protruding collarbones",
            "2033": "a 43-year-old version, several grey hairs at the temples, coarse sun-damaged skin with age spots, heavy under-eye bags, a completely slack expression — not peace, emptiness",
        }),
    "周砚": dict(
        key="zy", trigger="zy_man", age=38, role="结构工程师 · 男主",
        base=("a 38-year-old East Asian man, Chinese, square forehead, "
              "deep-set eyes with pronounced double eyelids, "
              "heavy straight eyebrows, a high straight nose, "
              "hard defined jawline with slight jowl beginning, "
              "deep vertical line between the brows from years of squinting, "
              "short black hair with visible grey at both temples, "
              "clean-shaven with faint blue-grey stubble shadow, "
              "thin rimless glasses, small ear lobes, "
              "restrained expression, mouth held in a flat neutral line, "
              "shoulders slightly raised from shallow breathing"),
        stages={
            "第一幕": "white shirt with a faint brown tea stain inside the collar, a mechanical watch",
            "第二幕": "puffy under-eyes, creased shirt, an inhaler in his pocket",
            "场68": "cyanotic lips, corded neck veins, an asthma attack",
            "场91": "bare wrist, no watch — the empty wrist is the point of the scene",
        }),
    "陈亦": dict(
        key="cy", trigger="cy_man", age=31, role="摄影师 · 情人",
        base=("a 31-year-old East Asian man, Chinese, lean face, high cheekbones, "
              "slightly downturned outer eye corners giving a soft melancholic look, "
              "single eyelid on the left, faint double on the right, asymmetric, "
              "medium-length wavy black hair pushed back, often falling loose, "
              "unshaven, patchy stubble along the jaw, "
              "a small scar through the right eyebrow, "
              "slim build, prominent collarbones, "
              "an easy relaxed half-smile that never reaches the eyes"),
        note="陈亦的每一个镜头都必须有遮挡物（取景框/门框/车窗/相机/手臂）。"
             "全片他没有一个完全敞开的正面单人镜头。",
        stages={"全片": "always partially occluded by a frame, a doorway, a car window, a camera body, or his own forearm"}),
    "何雨": dict(
        key="hy", trigger="hy_woman", age=30, role="小学教师 · 陈亦妻子",
        base=("a 30-year-old East Asian woman, Chinese, round soft face, "
              "warm double-eyelid eyes, low flat nose bridge, full cheeks, "
              "chin-length straight black hair tucked behind one ear, "
              "minimal makeup, slightly chapped lips, "
              "a plain wool coat, a canvas tote bag, "
              "composed and calm, completely without aggression, "
              "the steadiness of someone who has already cried this out at home"),
        stages={"场78": "standing in a doorway, backlit, holding a small child's hand"}),
    "王素芬": dict(
        key="wsf", trigger="wsf_woman", age=62, role="见月母亲",
        base=("a 62-year-old East Asian woman, Chinese, deeply lined face, "
              "short permed grey hair, hooded eyes with clouded corneas, "
              "thin frame in a hospital cardigan, "
              "a vacant searching expression, mouth slightly open, "
              "hands with prominent veins resting on a blanket"),
        stages={"全片": "seated by a window in a care facility"}),
    "张小满": dict(
        key="xm", trigger="xm_woman", age=22, role="缮堂助理",
        base=("a 22-year-old East Asian woman, Chinese, round youthful face, "
              "bright double-eyelid eyes, small nose, slight baby fat, "
              "black hair in a high messy bun, a few acne marks on the chin, "
              "oversized sweatshirt and canvas apron, "
              "open readable expressions — she is the only face in this film "
              "that shows exactly what she feels"),
        stages={"全片": "in the restoration studio"}),
}

# ---------------------------------------------------------------- 一致性训练集

ANGLES = ["front facing, eye level",
          "three-quarter left, eye level",
          "three-quarter right, eye level",
          "full profile left",
          "slight low angle looking up",
          "slight high angle looking down",
          "back of head turning toward camera",
          "extreme close-up on the eyes"]

LIGHTS = ["soft north window light from camera left",
          "single warm practical lamp, hard shadow side",
          "overcast outdoor daylight, flat and even",
          "night, streetlight from behind, rim light only",
          "candlelight from below, flickering"]

EXPRS = ["neutral, unreadable", "holding back tears", "a small tired smile",
         "listening, eyes lowered", "flat exhausted stare"]


def sheet(name, n=40):
    """生成角色一致性训练集提示词（用于 LoRA 训练素材）"""
    c = CHARACTERS[name]
    combos = list(itertools.product(ANGLES, LIGHTS, EXPRS))
    out = []
    step = max(1, len(combos) // n)
    for i, (a, l, e) in enumerate(combos[::step][:n]):
        out.append(dict(
            character=name, kind="trainset", idx=i + 1,
            prompt=f"{LOOK}, {c['base']}, {a}, {l}, {e}, plain neutral background",
            negative=NEG, width=1024, height=1024, seed=10000 + i))
    return out


# ---------------------------------------------------------------- 关键镜头

SHOTS = [
    (1, "场2", "林见月",
     "interior night, cramped old apartment, she sits at a dining table under a single warm desk lamp, painting gold along a crack in a porcelain bowl with a fine brush, an old cat at her feet, rain on the window behind, camera at table height, over-shoulder", "2024春"),
    (2, "场6", "周砚",
     "industrial interior day, unfinished concrete floor, he stands in a hard hat looking up at a structural wall, cold north light from an open facade, low angle, dust in the air", "第一幕"),
    (3, "场12", "林见月",
     "exterior golden hour, a wooden pier on a vast highland lake, strong wind, her hair blown completely across her face, distant mountains under breaking clouds, a shaft of light hitting the water, wide shot, backlit", "2024大理"),
    (4, "场14", "陈亦",
     "exterior day, a mountain trail, he raises a camera to his eye, his face half hidden behind the camera body, dappled light through pines", "全片"),
    (5, "场17", "林见月",
     "exterior harsh midday, on a small wooden boat, she leans over the gunwale reaching into the water, her expression caught between laughing and crying, harsh specular glitter on the lake surface, handheld", "2024大理"),
    (6, "场21", "林见月",
     "interior day, a small silver workshop, she holds a plain band ring up to the window light examining it, her own bare ring finger visible, shallow focus on the ring", "2024大理"),
    (7, "场24", "王素芬",
     "interior day, a care facility room, an old woman by the window looks at her daughter without recognition, flat overcast light, static frame", "全片"),
    (8, "场45", "周砚",
     "interior night, bedroom, near-total darkness, he sits on the edge of the bed holding her sleeping hand, only a streetlight through the curtain, extreme close-up on his thumb turning the ring on her finger", "第二幕"),
    (9, "场49", "林见月",
     "interior night during a typhoon, power out, a single candle on a dining table, wind and rain lashing the window, she sits facing her husband across the table, wide two-shot, candle as only source", "2024秋"),
    (10, "场68", "周砚",
     "exterior night, narrow old canal street, wet cobblestones, shattered glass door, ceramic shards and blood on the ground, he kneels gasping for breath, handheld, streetlamp only", "场68"),
    (11, "场69", "林见月",
     "interior night, hospital emergency corridor, harsh green fluorescent overhead, she sits alone staring at her bandaged right hand, extreme close-up on the trembling index finger", "2024冬"),
    (12, "场78", "何雨",
     "interior day, ceramic restoration studio, a calm woman in a wool coat holding a 4-year-old girl's hand standing in the doorway backlit, deep focus, static frame", "场78"),
    (13, "场88", "张小满",
     "interior day, restoration studio, a young woman handing over a resignation letter, red-rimmed eyes, afternoon window light", "全片"),
    (14, "场89", "周砚",
     "interior night, dining table, he signs a document slowly with a heavy hand, single overhead pendant lamp, close on the pen and his knuckles", "第二幕"),
    (15, "场91", "周砚",
     "interior morning, an emptied apartment entry, a suitcase by the door, a set of keys and a mechanical watch placed side by side on the shoe cabinet, his bare wrist visible leaving frame, macro on the watch", "场91"),
    (16, "场104", "林见月",
     "exterior morning, a lakeside pier, a 43-year-old woman behind a tiny souvenir stall of cheap glued bowls, weathered coat, cold flat light, wide shot", "2033"),
    (17, "场106", "林见月",
     "interior night, a bare rented room, a 43-year-old woman sitting at a small table trying to hold a gold-dust brush, her right hand visibly trembling, single bulb overhead", "2033"),
    (18, "场110", "林见月",
     "exterior night, the same wooden pier nine years later, a 43-year-old woman crouching at the edge, her hand in the black water, the full moon shattered into fragments across the ripples, wide shot, moonlight only", "2033"),
]


def shots():
    out = []
    for idx, scene, name, shot, stage in SHOTS:
        c = CHARACTERS[name]
        st = c["stages"].get(stage, "")
        out.append(dict(
            character=name, kind="shot", scene=scene, idx=idx,
            prompt=f"{LOOK}, {c['base']}, {st}, {shot}",
            negative=NEG, width=1920, height=816, seed=20000 + idx,
            lora=c["trigger"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sheet")
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--jsonl")
    a = ap.parse_args()

    items = []
    if a.list:
        for n, c in CHARACTERS.items():
            print("%-8s %-4s %-22s trigger=%s" % (n, c["age"], c["role"], c["trigger"]))
        return
    if a.sheet:
        items = sheet(a.sheet)
    if a.shots:
        items += shots()
    if not items:
        items = shots()
        for n in CHARACTERS:
            items += sheet(n)

    if a.jsonl:
        with open(a.jsonl, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        print("wrote %d prompts -> %s" % (len(items), a.jsonl))
    else:
        for it in items:
            print("--- [%s] %s" % (it["character"], it.get("scene", it.get("idx"))))
            print(it["prompt"][:400])
            print()


if __name__ == "__main__":
    main()
