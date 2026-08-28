---
name: comfyui
description: 通过 ComfyUI HTTP API 文生图，不打开 Web 界面。自动探测服务端模型，支持 Z-Image Turbo / FLUX.1 / 通用 SD 检查点，可选一键唤醒 EC2 后端。
triggers:
  - "comfyui"
  - "用 comfyui 出图"
  - "自建模型出图"
  - "flux 出图"
  - "z-image"
  - "自己的 GPU 出图"
---

# ComfyUI Skill

调用**你自己部署的** ComfyUI 出图。走 HTTP API，不加载 Web 界面。

适用场景：本地 ComfyUI、内网机器、云上 GPU 实例。跨境访问自建实例时尤其有用——ComfyUI 前端首屏要拉 60+ 个文件近 2MB，高延迟链路下要一两分钟；API 只有几 KB 的 JSON 往返。

> 想用现成的托管服务出图，用 `image-gen` skill（豆包 Seedream / Pollinations）。本 skill 是给自建后端用的。

## 快速使用

```bash
# 文生图，自动挑选服务端可用的模型
scripts/txt2img.sh "a lone red lighthouse on black volcanic rocks, overcast sky"

# 第二个位置参数是分辨率
scripts/txt2img.sh "cyberpunk street, neon rain" 1280x720

# 指定预设
scripts/txt2img.sh "portrait of an old fisherman" -m flux-dev

# 一次出 4 张（每张不同 seed）
scripts/txt2img.sh "watercolor koi pond" 768 -b 4

# 固定 seed 复现
scripts/txt2img.sh "a misty forest path" --seed 42

# 看服务端到底装了哪些模型
scripts/txt2img.sh --list-models

# 后端在 EC2 上且已停机：先唤醒再出图
scripts/txt2img.sh "a quiet harbour at dawn" --wake

# 交互模式
scripts/txt2img.sh
```

## 配置

在 `secrets/comfyui.env` 中配置：

```bash
# 必填
COMFY_HOST=http://localhost:8188

# 可选：端点需要鉴权时
COMFY_API_KEY=your-key-here
COMFY_AUTH_HEADER=X-Comfy-Key

# 可选：后端跑在 EC2 上，启用 --wake 和 instance.sh
COMFY_INSTANCE_ID=i-xxxxxxxxxxxxxxxxx
COMFY_AWS_REGION=us-west-2

# 可选：输出目录
COMFY_OUT=~/clawd/output/images
```

也可以直接用环境变量或 `--host` 覆盖。**脚本里不含任何硬编码的密钥或主机名。**

没有现成后端？见 [references/deploy-aws.md](references/deploy-aws.md)（在 AWS 上从零起一台，含机型选择、显存匹配和成本）。

## 预设

| 预设 | 别名 | 步数 | 需要的模型文件 |
|------|------|------|----------------|
| `z-image-turbo` | `turbo` | 8 | `diffusion_models/z_image_turbo_bf16.safetensors` + `text_encoders/qwen_3_4b.safetensors` + `vae/ae.safetensors` |
| `flux-schnell` | `schnell` | 4 | `checkpoints/flux1-schnell-fp8.safetensors` |
| `flux-dev` | `dev` | 20 | `checkpoints/flux1-dev-fp8.safetensors` |
| `sd-checkpoint` | `sd`, `sdxl` | 25 | 任意检查点，配合 `--ckpt` |

**不传 `-m` 时自动探测**：按上表顺序逐个检查服务端是否具备所需文件，用第一个满足的；都不满足则回落到 `checkpoints/` 里的第一个文件。

任意其他模型直接指名：

```bash
scripts/txt2img.sh "a fox in snow" --ckpt sd_xl_base_1.0.safetensors --cfg 7 -n 30
```

## 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `<prompt>` | 必填 | 位置参数 1，不给则进入交互 |
| `<size>` | `1024` | 位置参数 2，`1024` 或 `1280x720` |
| `-m, --model` | 自动 | 预设名或别名 |
| `--ckpt` | — | 直接指定检查点文件名 |
| `-b, --batch` | `1` | 生成张数 |
| `-n, --steps` | 按预设 | 采样步数 |
| `--cfg` | 按预设 | CFG scale |
| `--seed` | `0`（随机） | 固定 seed |
| `--negative` | 空 | 负面提示词（FLUX 会忽略） |
| `-d, --dir` | `~/clawd/output/images` | 输出目录 |
| `--png` | 关 | 下载无损 PNG（约 10 倍大且慢） |
| `-q, --quality` | `90` | webp 质量 |
| `--host` | — | 覆盖 `COMFY_HOST` |
| `--timeout` | `900` | 每张图等待上限（秒） |
| `--wake` | 关 | 先启动 EC2 后端并轮询到就绪 |
| `--list-models` | — | 列出服务端模型后退出 |
| `--no-open` | 关 | 完成后不在 Finder 中定位 |

分辨率分隔符 `x` `*` `×` `,` 空格都认，范围 256–4096，**自动对齐到 16 的倍数**（扩散模型要求）。

## 输出

默认 `~/clawd/output/images/`，文件名便于检索：

```
20260828-095030_z-image-turbo_1280x720_a-lone-red-lighthouse.webp
└─ 时间戳 ──┘ └── 预设 ──┘ └─分辨率─┘ └──── 提示词摘要 ────┘
```

**默认下 webp 而非 PNG**，因为服务端转码后体积差一个数量级——跨境链路上直接决定体验：

| 格式 | 实测体积 | 实测下载 |
|------|----------|----------|
| `webp;90`（默认） | 116 KB | 3.3s |
| 原始 PNG（`--png`） | 1,235 KB | 33.7s |

PNG 原图始终留在服务端 `ComfyUI/output/`，且**内嵌完整工作流元数据**——把 PNG 拖回 ComfyUI 画布可还原当时全部参数。要无损原图再做后期时才用 `--png`。

## 实例管理

GPU 实例按小时计费，闲置务必停机。

```bash
scripts/instance.sh status
scripts/instance.sh start
scripts/instance.sh stop
```

停机保留磁盘和模型，但**根卷仍然计费**。

## 性能预期

单卡 24GB（L4 / A10G 一档）实测：

| 预设 | 分辨率 | 热态耗时 |
|------|--------|----------|
| `z-image-turbo` | 768² | 6–8s |
| `z-image-turbo` | 1024² | ~12s |
| `flux-schnell` | 1024² | ~9s |
| `flux-dev` | 1024² | ~70s |

**冷启动**：每个模型首次使用要从磁盘加载 12–17GB 权重，额外 30–60 秒。之后连续用同一模型都是热态；频繁切换模型会反复触发冷加载。

**文字渲染**：要求图中出现准确文字时用 `z-image-turbo`。`flux-dev` 在 fp8 量化下常把文字画成乱码或镜像。

## 排查

| 现象 | 原因与处理 |
|------|-----------|
| `cannot reach ...` | 后端未运行。设了 `COMFY_INSTANCE_ID` 就用 `--wake`，否则检查 `COMFY_HOST` |
| `HTTP 302/401/403 — authentication rejected` | 密钥缺失或不对。注意反代常用 302 重定向到登录页而非 401 |
| `preset X needs Y but the server does not have it` | 用 `--list-models` 看实际有什么，再用 `--ckpt` 指名 |
| `server rejected the workflow` | 模型文件名变了，或节点参数不被该 ComfyUI 版本接受 |
| 出图很慢 | 先确认是否冷加载。热态应符合上表 |

## 扩展到其他工作流

想加图生图、LoRA、放大等，改 `scripts/txt2img.py` 的 `PRESETS` 和 `build_graph()`。
最省事的做法：在 ComfyUI Web UI 里搭好工作流，用 **Workflow → Export (API)** 导出，
得到的 JSON 就是可直接 POST 的格式。

原始 HTTP API 三步流程（提交 / 轮询 / 取图）见 [references/api.md](references/api.md)。

## 安全

- 脚本**不包含**任何密钥、主机名、账号 ID。全部由环境变量或 `secrets/comfyui.env` 注入。
- `COMFY_API_KEY` 等同于该 ComfyUI 的完整 API 权限。ComfyUI 可通过 ComfyUI-Manager 安装任意 custom node，**即等价于该机器上的任意代码执行**。别把密钥提交进 git。
- ComfyUI 自身没有认证机制。**不要把它直接暴露在公网**，前面要放反向代理或身份层（见 `references/deploy-aws.md`）。
