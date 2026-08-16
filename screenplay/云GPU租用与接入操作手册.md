# 云 GPU 租用与接入操作手册

> 目标：租一台带 24GB 显存的云服务器，把 Claude Code 装上去，
> 让它在有显卡、网络通畅的环境里跑完《说谎的爱人》先导片段。

---

# 第一部分 · 租云 GPU

## 1. 选平台

国内常用的几家，随便挑一家即可：

| 平台 | 特点 |
|---|---|
| **AutoDL** | 最省事，社区镜像里 ComfyUI 都装好了，适合第一次租 |
| 恒源云 | 类似 AutoDL |
| 阿里云 / 腾讯云 GPU | 正规稳定，但配置流程复杂、价格偏高 |
| RunPod / Vast.ai | 国外平台，需要外币卡 |

下面以 **AutoDL** 为例。其他平台流程大同小异。

## 2. 注册与实名

1. 打开 `autodl.com`，注册账号
2. **完成实名认证**（国内平台强制，不认证不能开机）
3. 充值。**先充 50—100 元就够跑完先导片段了**，不要一次充太多

## 3. 开一台机器

进「算力市场」，按下面这几项选：

| 选项 | 选什么 | 为什么 |
|---|---|---|
| **地区** | 哪个便宜选哪个，优先「有卡可用」的 | 热门区经常没卡 |
| **显卡** | **RTX 4090（24GB）** | 24GB 是能跑通全流程的最低线 |
| **卡数** | 1 张 | 我们的脚本是单卡流程 |
| **数据盘** | **扩到 100GB 以上** | 光模型文件就要 60GB+，默认盘不够 |
| **镜像** | 见下 | |

### 镜像怎么选

**优先找社区镜像里带 "ComfyUI" 的**（搜索框里搜 ComfyUI），这样 ComfyUI 和 PyTorch 都预装好了，省两小时。

如果找不到，选基础镜像：

```
PyTorch 2.4.0  /  Python 3.11  /  CUDA 12.1
```

然后点「立即创建」。

## 4. 计费别踩坑

- **按量计费**：用多久算多久，适合摸索阶段
- **包日/包周**：连续跑长任务时更便宜
- ⚠️ **关机 ≠ 停止计费**。要点「**关机**」才停止收 GPU 费用，数据盘仍按天收少量存储费
- 💡 AutoDL 有「**无卡模式开机**」：不占显卡、几毛钱一小时，
  **专门用来下载模型和传文件**。下载 60GB 模型时用这个模式，能省下大部分钱

**建议流程**：无卡模式开机 → 下模型/装环境 → 关机 → 换成 4090 开机 → 跑任务 → 立刻关机

## 5. 连上机器

创建完成后，控制台会给你两样东西：

- **JupyterLab 链接**（点一下就能在浏览器里打开，最简单）
- **SSH 登录命令**，形如：
  ```
  ssh -p 12345 root@region-1.autodl.com
  ```
  和一个密码

**新手直接用 JupyterLab**：打开后点左下角的「终端 / Terminal」，就得到一个命令行窗口。
下面所有命令都敲在这个窗口里。

---

# 第二部分 · 把我（Claude Code）装到这台机器上

这是让我真正用上你 GPU 的办法。装完之后，你在那台机器的终端里跟我对话，
我能直接调用它的显卡、下载模型、跑生成、看报错、改参数。

## 步骤 1 · 装 Node.js

Claude Code 需要 Node.js 18 以上。在终端里敲：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
node -v          # 显示 v20.x 就对了
```

> 如果网络慢，AutoDL 可以先开学术加速：`source /etc/network_turbo`

## 步骤 2 · 装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

## 步骤 3 · 登录

```bash
claude
```

第一次运行会让你登录。它会打印一个链接——
**复制到你自己电脑的浏览器里打开**，登录你的 Claude 账号，
把页面给出的验证码粘回终端。

> 服务器上没有浏览器，所以必须用这种「链接 + 验证码」的方式。

## 步骤 4 · 把项目拉下来

```bash
cd /root/autodl-tmp                      # 数据盘目录，空间大
git clone https://github.com/frankray11199-ship-it/NarratoAI.git
cd NarratoAI
git checkout claude/lying-lover-film-script-ztzz8w
```

现在剧本、镜头表、提示词生成器、ComfyUI 提交器全都在这台机器上了。

## 步骤 5 · 开始干活

```bash
claude
```

然后直接跟它说：

> 读一下 screenplay/说谎的爱人-先导片段-生产手册.md，
> 按里面的步骤，在这台机器上把先导片段的 68 个数字人镜头做出来。
> 先装 ComfyUI 和 FLUX 模型，装好告诉我。

**它会接着我在这里做完的一切往下干**——因为所有上下文都写在仓库的文档里了。

---

# 第三部分 · 模型下载（可以让它代劳，也可以自己来）

## 需要下载的东西和大小

| 模型 | 大小 | 用途 |
|---|---|---|
| `flux1-dev.safetensors` | 约 24GB | 出图主模型 |
| `t5xxl_fp16.safetensors` | 约 10GB | 文本编码 |
| `clip_l.safetensors` | 约 250MB | 文本编码 |
| `ae.safetensors` | 约 340MB | 解码 |
| `pulid_flux_v0.9.1.safetensors` | 约 1.1GB | 锁脸（可选） |
| Wan2.2-I2V-A14B | 约 30—60GB | 图生视频 |

**合计约 70—100GB**，所以数据盘一定要开够 100GB 以上。

## 两个坑

**坑一：FLUX.1-dev 需要在 HuggingFace 上先同意协议。**
去 `huggingface.co/black-forest-labs/FLUX.1-dev` 页面点同意，
然后在账号设置里生成一个 Access Token，下载时要用。

**坑二：国内直连 HuggingFace 很慢或连不上。**
两个办法：
- AutoDL 开学术加速：`source /etc/network_turbo`
- 或用国内镜像站：把下载地址里的 `huggingface.co` 换成 `hf-mirror.com`

## 下载命令示例

```bash
pip install -U "huggingface_hub[cli]"
export HF_ENDPOINT=https://hf-mirror.com          # 走国内镜像
cd /root/autodl-tmp/ComfyUI/models

huggingface-cli download black-forest-labs/FLUX.1-dev \
    flux1-dev.safetensors --local-dir ./unet --token 你的Token
huggingface-cli download comfyanonymous/flux_text_encoders \
    t5xxl_fp16.safetensors clip_l.safetensors --local-dir ./clip
huggingface-cli download black-forest-labs/FLUX.1-dev \
    ae.safetensors --local-dir ./vae --token 你的Token
```

**下载这一步务必用「无卡模式」开机**，能省不少钱。

---

# 第四部分 · 花多少钱

先导片段 GPU 侧约 17.5 小时。按 4090 的常见价位估算：

| 项 | 时长 | 说明 |
|---|---|---|
| 无卡模式下模型 | 2—3 小时 | 极便宜，几毛钱一小时 |
| 4090 跑生成 | 17.5 小时 | 主要成本 |
| 数据盘存储 | 按天 | 少量 |

**总体量级在几十到一百多元**。具体价格以平台当时的实际报价为准——
GPU 租赁价格波动大，我给不了准确数字。

比买一张 4090（一万多）便宜太多。**先导片段验证通过了再考虑买卡。**

---

# 第五部分 · 如果你不想装 Claude Code

也可以你自己动手，我在这边远程指导：

1. 你在 AutoDL 上按上面的步骤开机、装 ComfyUI、下模型
2. 把这个仓库拉下来
3. 按 `说谎的爱人-先导片段-生产手册.md` 一步步执行
4. **卡住了就把报错信息复制过来发给我**，我告诉你怎么改

这条路慢一些，但完全可行。缺点是每一步都要你手动转达，
而装了 Claude Code 的话它自己就能看报错、自己改。

---

# 常见问题

**Q：机器关机后东西还在吗？**
A：数据盘（`/root/autodl-tmp`）的东西会保留，系统盘可能被重置。
**所有模型和产出都放数据盘**。

**Q：能不能让当前这个对话直接连我的 GPU？**
A：不能。当前会话跑在一个出网被锁死的容器里，SSH 不出去。
正确做法就是上面说的——把 Claude Code 装到 GPU 机器上。

**Q：租的机器会不会被别人看到我的东西？**
A：实例是独占的。但云平台的机器终究不是你自己的，
**敏感素材（尤其是任何真人照片）不要往上传**。

**Q：4090 抢不到怎么办？**
A：换地区、换时段，或者退一步用 **A5000（24GB）/ 3090（24GB）**，
显存一样够，速度慢 30% 左右，不影响能不能跑通。
