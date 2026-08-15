#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI 批量提交器 · FLUX.1-dev (+ PuLID / LoRA)
================================================
读取 characters.py 导出的 jsonl，逐条构建 ComfyUI API 图并提交到本地 ComfyUI。

前置（在你本机，非本容器）：
  1. ComfyUI 已启动:  python main.py --listen 127.0.0.1 --port 8188
  2. 模型就位:
       models/unet/flux1-dev.safetensors
       models/clip/t5xxl_fp16.safetensors
       models/clip/clip_l.safetensors
       models/vae/ae.safetensors
  3. 【L2 一致性，可选】安装 ComfyUI_PuLID_Flux_ll 节点包，并放置:
       models/pulid/pulid_flux_v0.9.1.safetensors
     参考图必须是本管线 L1 生成的原创虚拟人脸，不要用真人照片。
  4. 【L3 一致性，可选】角色 LoRA 放在 models/loras/

用法:
  python3 characters.py --jsonl prompts.jsonl
  python3 comfy_submit.py prompts.jsonl --out ./render_out
  python3 comfy_submit.py prompts.jsonl --dry-run > graph.json   # 只看图，不提交
  python3 comfy_submit.py prompts.jsonl --pulid ref_ljy.png --filter 林见月
  python3 comfy_submit.py prompts.jsonl --lora ljy_v1.safetensors --filter 林见月
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

DEFAULTS = dict(
    unet="flux1-dev.safetensors",
    clip_t5="t5xxl_fp16.safetensors",
    clip_l="clip_l.safetensors",
    vae="ae.safetensors",
    pulid_model="pulid_flux_v0.9.1.safetensors",
    steps=28,
    guidance=3.5,
    sampler="euler",
    scheduler="simple",
    denoise=1.0,
)


def build_graph(item, cfg, pulid_ref=None, lora=None, prefix="lyinglover"):
    """构建 ComfyUI API 格式图。节点 id 用字符串，符合 /prompt 接口约定。"""
    g = {}

    g["1"] = {"class_type": "UNETLoader",
              "inputs": {"unet_name": cfg["unet"], "weight_dtype": "default"}}
    g["2"] = {"class_type": "DualCLIPLoader",
              "inputs": {"clip_name1": cfg["clip_t5"], "clip_name2": cfg["clip_l"],
                         "type": "flux"}}
    g["3"] = {"class_type": "VAELoader", "inputs": {"vae_name": cfg["vae"]}}

    model_ref = ["1", 0]
    clip_ref = ["2", 0]

    # ---- L3: 角色 LoRA
    if lora:
        g["4"] = {"class_type": "LoraLoader",
                  "inputs": {"model": model_ref, "clip": clip_ref,
                             "lora_name": lora,
                             "strength_model": 0.85, "strength_clip": 0.85}}
        model_ref, clip_ref = ["4", 0], ["4", 1]

    # ---- L2: PuLID 人脸身份锁定
    if pulid_ref:
        g["5"] = {"class_type": "PulidFluxModelLoader",
                  "inputs": {"pulid_file": cfg["pulid_model"]}}
        g["6"] = {"class_type": "PulidFluxEvaClipLoader", "inputs": {}}
        g["7"] = {"class_type": "PulidFluxInsightFaceLoader",
                  "inputs": {"provider": "CUDA"}}
        g["8"] = {"class_type": "LoadImage", "inputs": {"image": pulid_ref}}
        g["9"] = {"class_type": "ApplyPulidFlux",
                  "inputs": {"model": model_ref, "pulid_flux": ["5", 0],
                             "eva_clip": ["6", 0], "face_analysis": ["7", 0],
                             "image": ["8", 0],
                             "weight": 0.80, "start_at": 0.0, "end_at": 1.0}}
        model_ref = ["9", 0]

    g["10"] = {"class_type": "CLIPTextEncode",
               "inputs": {"clip": clip_ref, "text": item["prompt"]}}
    g["11"] = {"class_type": "FluxGuidance",
               "inputs": {"conditioning": ["10", 0], "guidance": cfg["guidance"]}}
    # FLUX 无独立负面通道，留空 conditioning 作占位
    g["12"] = {"class_type": "CLIPTextEncode",
               "inputs": {"clip": clip_ref, "text": item.get("negative", "")}}

    g["13"] = {"class_type": "EmptyLatentImage",
               "inputs": {"width": item.get("width", 1024),
                          "height": item.get("height", 1024), "batch_size": 1}}
    g["14"] = {"class_type": "KSampler",
               "inputs": {"model": model_ref,
                          "positive": ["11", 0], "negative": ["12", 0],
                          "latent_image": ["13", 0],
                          "seed": item.get("seed", 0),
                          "steps": cfg["steps"], "cfg": 1.0,
                          "sampler_name": cfg["sampler"],
                          "scheduler": cfg["scheduler"],
                          "denoise": cfg["denoise"]}}
    g["15"] = {"class_type": "VAEDecode",
               "inputs": {"samples": ["14", 0], "vae": ["3", 0]}}

    tag = "%s_%s_%s" % (prefix, item.get("character", "x"),
                        item.get("scene", item.get("idx", "0")))
    g["16"] = {"class_type": "SaveImage",
               "inputs": {"images": ["15", 0], "filename_prefix": tag}}
    return g


def submit(graph, host):
    data = json.dumps({"prompt": graph}).encode("utf-8")
    req = urllib.request.Request("%s/prompt" % host, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def queue_len(host):
    try:
        with urllib.request.urlopen("%s/queue" % host, timeout=10) as r:
            q = json.loads(r.read().decode("utf-8"))
        return len(q.get("queue_running", [])) + len(q.get("queue_pending", []))
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--host", default="http://127.0.0.1:8188")
    ap.add_argument("--pulid", help="PuLID 参考图文件名（须已放入 ComfyUI input/）")
    ap.add_argument("--lora", help="角色 LoRA 文件名")
    ap.add_argument("--filter", help="只提交某角色，如 林见月")
    ap.add_argument("--kind", choices=["shot", "trainset"], help="只提交某类")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-queue", type=int, default=8, help="队列水位上限")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = dict(DEFAULTS)
    items = []
    with open(a.jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            it = json.loads(line)
            if a.filter and it.get("character") != a.filter:
                continue
            if a.kind and it.get("kind") != a.kind:
                continue
            items.append(it)
    if a.limit:
        items = items[:a.limit]

    if not items:
        print("没有匹配的条目", file=sys.stderr)
        return 1

    if a.dry_run:
        print(json.dumps(build_graph(items[0], cfg, a.pulid, a.lora),
                         ensure_ascii=False, indent=2))
        print("\n// 共 %d 条待提交（--dry-run 仅输出第一条的图）" % len(items),
              file=sys.stderr)
        return 0

    if queue_len(a.host) < 0:
        print("连不上 ComfyUI: %s\n请先启动: python main.py --listen 127.0.0.1 --port 8188"
              % a.host, file=sys.stderr)
        return 2

    ok = 0
    for i, it in enumerate(items, 1):
        while True:
            q = queue_len(a.host)
            if 0 <= q < a.max_queue:
                break
            time.sleep(3)
        g = build_graph(it, cfg, a.pulid, a.lora)
        try:
            r = submit(g, a.host)
            ok += 1
            print("[%d/%d] %s %s -> %s" % (i, len(items), it.get("character"),
                                           it.get("scene", it.get("idx")),
                                           r.get("prompt_id", "?")))
        except urllib.error.HTTPError as e:
            print("[%d/%d] 失败: %s\n%s" % (i, len(items), e,
                                           e.read().decode("utf-8")[:400]),
                  file=sys.stderr)
    print("已提交 %d/%d" % (ok, len(items)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
