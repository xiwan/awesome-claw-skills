# ComfyUI HTTP API 参考

`scripts/txt2img.py` 封装的就是下面这三步。需要自己集成、或想加新工作流时看这里。

约定：

```bash
export COMFY_HOST=http://localhost:8188
export COMFY_KEY=...            # 若端点无鉴权则省略所有 -H 参数
AUTH=(-H "X-Comfy-Key: $COMFY_KEY")
```

---

## 第 1 步 提交工作流 → 拿 prompt_id

`POST /prompt`，body 为 `{"prompt": {图}}`。

图是一个字典：key 是节点 ID（任意字符串），`class_type` 是节点类型，`inputs`
里引用其它节点的输出写成 `["节点ID", 输出槽位下标]`。

```bash
curl -sS -X POST "$COMFY_HOST/prompt" "${AUTH[@]}" \
  -H "Content-Type: application/json" -d '{
  "prompt": {
    "ckpt": {"class_type": "CheckpointLoaderSimple",
             "inputs": {"ckpt_name": "flux1-schnell-fp8.safetensors"}},
    "pos":  {"class_type": "CLIPTextEncode",
             "inputs": {"text": "a lighthouse at dusk, stormy sea", "clip": ["ckpt", 1]}},
    "neg":  {"class_type": "CLIPTextEncode",
             "inputs": {"text": "", "clip": ["ckpt", 1]}},
    "lat":  {"class_type": "EmptyLatentImage",
             "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "ks":   {"class_type": "KSampler",
             "inputs": {"seed": 42, "steps": 4, "cfg": 1.0,
                        "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                        "model": ["ckpt", 0], "positive": ["pos", 0],
                        "negative": ["neg", 0], "latent_image": ["lat", 0]}},
    "dec":  {"class_type": "VAEDecode",
             "inputs": {"samples": ["ks", 0], "vae": ["ckpt", 2]}},
    "save": {"class_type": "SaveImage",
             "inputs": {"filename_prefix": "demo", "images": ["dec", 0]}}
  }
}'
```

响应：

```json
{
    "prompt_id": "556f2fa2-45b8-491d-9498-0f3e67341b2f",
    "number": 4,
    "node_errors": {}
}
```

`node_errors` 非空即图写错了，内容会指明哪个节点的哪个参数有问题，**此时不会入队**。

---

## 第 2 步 轮询直到完成

`GET /history/{prompt_id}`。**未完成时返回 `{}`**，完成后才有内容。

```bash
PID=556f2fa2-45b8-491d-9498-0f3e67341b2f
while :; do
  R=$(curl -sS "$COMFY_HOST/history/$PID" "${AUTH[@]}")
  [ "$R" != "{}" ] && break
  sleep 2
done
echo "$R" | python3 -m json.tool
```

关注三个字段：

```
status.status_str        success | error
status.completed         true
outputs["save"].images[0]  {filename, subfolder, type}
```

`outputs` 的 key 是 **SaveImage 节点的 ID**（上例中是 `"save"`）。
失败时原因在 `status.messages` 里。

也可以用 WebSocket `/ws?clientId=<uuid>` 接收实时进度，但轮询对脚本更简单可靠。

---

## 第 3 步 取图

`GET /view`，参数来自上一步的 `images[0]`。

```bash
# 服务端转码为 webp —— 强烈推荐
curl -sS -o out.webp "${AUTH[@]}" \
  "$COMFY_HOST/view?filename=demo_00001_.png&subfolder=&type=output&preview=webp;90"

# 原始 PNG
curl -sS -o out.png "${AUTH[@]}" \
  "$COMFY_HOST/view?filename=demo_00001_.png&subfolder=&type=output"
```

`preview` 格式为 `webp;质量` 或 `jpeg;质量`，**只认这两种**，其他值一律回落为 webp。

同一张 1024² 图实测：

| 请求 | 体积 |
|------|------|
| 原始 PNG | 1,234,646 B |
| `preview=webp;90` | 115,876 B |
| `preview=webp;80` | 58,494 B |
| `preview=jpeg;85` | 115,916 B |

远程访问时务必用 webp——差一个数量级。

---

## 其他有用端点

```bash
# 全部节点的参数定义、类型、默认值、可选值（约 1.7MB）
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/object_info" > nodes.json

# 单个节点
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/object_info/KSampler" | python3 -m json.tool

# 已安装模型
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/models/checkpoints"
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/models/diffusion_models"
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/models/text_encoders"
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/models/vae"
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/models/loras"

# GPU / 显存 / 版本
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/system_stats"

# 队列，以及清空队列
curl -sS "${AUTH[@]}" "$COMFY_HOST/api/queue"
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"clear": true}' "$COMFY_HOST/api/queue"

# 中断当前任务
curl -sS -X POST "${AUTH[@]}" "$COMFY_HOST/api/interrupt"
```

`/api/xxx` 与 `/xxx` 两种前缀都可用，`/prompt` 和 `/api/prompt` 等价。

---

## 三类模型的接线差异

**All-in-one 检查点**（FLUX.1 fp8、SD1.5、SDXL）——一个文件同时提供三个输出：

```
CheckpointLoaderSimple  →  [0]=MODEL  [1]=CLIP  [2]=VAE
```

**分离式**（Z-Image Turbo、FLUX.2、多数新模型）——三个加载器各管一块：

```
UNETLoader   →  [0]=MODEL      inputs: unet_name, weight_dtype
CLIPLoader   →  [0]=CLIP       inputs: clip_name, type, device
VAELoader    →  [0]=VAE        inputs: vae_name
```

**FLUX.1 dev 需要 guidance embedding**，在正向条件后插一个节点并改 KSampler 的接线：

```json
"guide": {"class_type": "FluxGuidance",
          "inputs": {"guidance": 3.5, "conditioning": ["pos", 0]}}
```

然后 `"ks".inputs.positive` 指向 `["guide", 0]`。schnell 不需要。

### 各预设的关键采样参数

| 预设 | latent 节点 | sampler | scheduler | cfg | steps |
|------|-------------|---------|-----------|-----|-------|
| Z-Image Turbo | `EmptySD3LatentImage` | `res_multistep` | `simple` | 1.0 | 8 |
| FLUX.1 schnell | `EmptyLatentImage` | `euler` | `simple` | 1.0 | 4 |
| FLUX.1 dev | `EmptyLatentImage` | `euler` | `simple` | 1.0 | 20 |
| SD / SDXL | `EmptyLatentImage` | `euler` | `normal` | 7.0 | 25 |

Z-Image Turbo 还要在 UNET 后串一个 `ModelSamplingAuraFlow`（`shift: 3.0`），
且 `CLIPLoader.type` 必须是 `lumina2`。

蒸馏模型（turbo / schnell）**cfg 必须为 1.0**，调高会出废图。

---

## 加新工作流最省事的办法

在 ComfyUI Web UI 里把工作流搭好调通，然后 **Workflow → Export (API)**。
导出的 JSON 就是 `/prompt` 的 `prompt` 字段内容，可直接 POST。

把它填进 `scripts/txt2img.py` 的 `PRESETS` 与 `build_graph()`，就多了一个预设。
