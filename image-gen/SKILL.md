---
name: image-gen
description: AI 图片生成。支持豆包 Seedream（火山方舟）和 Pollinations（免费备选）。文生图、图生图、组图生成。
triggers:
  - "生成图片"
  - "出图"
  - "画一张"
  - "generate image"
  - "配图"
---

# Image Gen Skill

多源 AI 图片生成，支持豆包 Seedream（主力）和 Pollinations（免费备选）。

## 快速使用

```bash
# 文生图（默认 Seedream 5.0）
scripts/generate.sh "一只可爱的机器人在挥手"

# 指定尺寸
scripts/generate.sh "科技风格封面" --size 2K

# 指定模型
scripts/generate.sh "风景照" --model 5.0
scripts/generate.sh "风景照" --model 4.5

# 图生图（参考图 + prompt）
scripts/generate.sh "把她放在游乐园" --image https://example.com/photo.jpg

# 组图生成
scripts/generate.sh "女孩在公园的一天，早中晚" --sequential --max-images 3

# 免费备选（Pollinations，无需 key，较慢）
scripts/generate.sh "cute robot" --source pollinations

# 指定输出路径
scripts/generate.sh "测试" --output /tmp/myimage.jpg
```

## 模型列表

| 模型 | 别名 | 说明 |
|------|------|------|
| doubao-seedream-5-0-260128 | 5.0 | **默认**，最新最强，照片级质感 |
| doubao-seedream-4-5-251128 | 4.5 | 性价比高，卡通/插画风格好 |
| doubao-seedream-4-0-250828 | 4.0 | 稳定 |
| doubao-seedream-3-0-t2i-250415 | 3.0 | 基础版 |
| Pollinations (sana) | - | 免费，无需 key，较慢 |

## 尺寸选项

- `1K` — ~1024x1024
- `2K` — ~2048x2048（默认）
- `4K` — ~4096x4096
- 或精确像素：`1920x1080`、`1080x1920` 等
- 注意：Seedream 最小总像素 3,686,400（约 1920x1920）

## 配置

在 `secrets/volcengine.env` 中配置 API Key：
```bash
ARK_API_KEY=your-api-key-here
```

获取方式：注册[火山方舟](https://www.volcengine.com/product/ark)，创建 Seedream 模型的 API Key。

## 输出

- 默认保存到 `~/clawd/output/images/`
- 文件名格式：`YYYYMMDD_HHMMSS_prompt摘要.jpg`

## 计费参考

- Seedream 5.0: ~¥0.06/张
- Seedream 4.5: ~¥0.04/张
- Pollinations: 免费
