# 《说谎的爱人》数字人管线 · 本机运行指南

> 本目录的脚本在**你自己的机器**上运行（需 GPU、需正常出网）。
> 远程容器内跑不了：所有生图接口与模型仓库被出网策略拦截，且无 GPU。

---

## 合规前置（唯一必须守住的一条）

管线中 PuLID / InstantID 一类工具的**参考图，必须是本管线 L1 阶段生成的原创虚拟人脸**，
不得投入现实中可识别的真人照片。

例外仅限三种，且需自行留存凭证：
- 演员签署了含「AI 训练 / 数字化形象 / 影视使用」条款的肖像授权书
- 你本人的面孔
- 已购商用授权、且授权范围明确包含 AI 训练的虚拟人资产

同理适用于 TTS 语音克隆的参考音频。

---

## 一、环境

```bash
# ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI && cd ComfyUI
pip install -r requirements.txt

# 模型（HuggingFace: black-forest-labs/FLUX.1-dev）
models/unet/flux1-dev.safetensors
models/clip/t5xxl_fp16.safetensors
models/clip/clip_l.safetensors
models/vae/ae.safetensors

# 可选：PuLID 人脸一致性
cd custom_nodes && git clone https://github.com/lldacing/ComfyUI_PuLID_Flux_ll
# models/pulid/pulid_flux_v0.9.1.safetensors

python main.py --listen 127.0.0.1 --port 8188
```

显存：FLUX.1-dev fp8 约 12GB，fp16 约 24GB。4090 可跑 fp8 + PuLID。

---

## 二、三步出图

### L1 · 先立角色（不锁脸，只挑脸）

```bash
python3 characters.py --sheet 林见月 --jsonl ljy_train.jsonl
python3 comfy_submit.py ljy_train.jsonl --out ./out_ljy
```

产出 40 张同角色不同角度/光位/表情。**人工挑出 8 张最一致、最符合设定的**，
这 8 张就是该角色的"原创面孔基准"，后续所有一致性手段都以它们为参考。

### L2 · 锁脸（够拍分镜）

```bash
# 把 L1 挑出的最佳一张放进 ComfyUI/input/ref_ljy.png
python3 characters.py --shots --jsonl shots.jsonl
python3 comfy_submit.py shots.jsonl --filter 林见月 --pulid ref_ljy.png
```

一致性约 88%。

### L3 · 训 LoRA（正片级，一致性约 96%）

```bash
# 用 L2 产出 35—50 张干净素材，分桶 512/768/1024
# kohya_ss FLUX LoRA:
#   network_dim 32 / alpha 16 / lr 1e-4 / batch 2 / epochs 12 / ~1800 steps
#   触发词: ljy_woman
python3 comfy_submit.py shots.jsonl --filter 林见月 --lora ljy_v1.safetensors
```

六个角色各训一个，即得到本片完整的"数字演员班底"。

---

## 三、静帧 → 视频

```bash
# 图生视频（开源本地）
Wan2.2-I2V-A14B      # 5s/镜, 720p, 4090 约 6—9 min
HunyuanVideo-I2V     # 备选

# 口型（有台词的镜头）
LatentSync 1.5       # 需先有配音音轨
EchoMimicV2          # 备选

# 补帧 + 提分辨率
RIFE 4.17            # 24 → 48fps
Real-ESRGAN / SUPIR  # 720p → 1080p
```

## 四、配音 + 成片（用本仓库 NarratoAI）

NarratoAI 不生成画面，它负责后段：素材入库 → 文案 → TTS → 自动对轴 → 字幕 → 配乐 → 导出。

```bash
cd ../..          # 回到 NarratoAI 根目录
uv sync && uv run webui.py
```

在 WebUI 中配置 LLM Base URL 与 TTS 引擎（IndexTTS-2 / 豆包 / 腾讯云），
把上一步产出的视频片段入库，把 `说谎的爱人-剧本.md` 作为文案来源。

---

## 五、文件说明

| 文件 | 作用 |
|---|---|
| `characters.py` | 六个角色的原创形象设定 + 258 条提示词生成器 |
| `comfy_submit.py` | ComfyUI API 图构建与批量提交，支持 PuLID / LoRA / 队列水位控制 |
| `../render/engine.py` | 程序化空镜渲染器（12 个意象场景，无需任何素材） |
| `../render/score.py` | 程序化配乐合成器 |
| `../render/build_film.py` | 时间线编排 + ffmpeg 合成 |

`render/` 里那套是**离线兜底方案**：在拿不到任何素材的环境下，
它仍能产出可用的意象空镜与转场（水中月、金缮裂纹、承重墙、沉戒……）。
正片里这类抽象镜头本来也需要，程序化生成比实拍更可控，可直接并入剪辑。

---

## 六、工作量估算（4090 单卡）

| 项 | 数量 | 合计 |
|---|---|---|
| 角色 LoRA 训练 | 6 | 9 h |
| 关键帧生成 | 600 镜 × 6 选 1 | 25 h |
| 图生视频 | 600 镜 × 5s | 70 h |
| 口型对齐 | 240 镜 | 12 h |
| 补帧提分辨率 | 50 min | 14 h |
| 配音 | 900 句 | 6 h |

GPU 侧约 136 h（连续约 6 天），人工剪辑调色混音约 100 h。

**建议先做 8 分钟先导片段（场 12—23 大理段落）验证效果，再决定是否投全片。**
