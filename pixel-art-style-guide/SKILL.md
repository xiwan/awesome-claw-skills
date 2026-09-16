---
name: pixel-art-style-guide
description: >
  像素游戏美术风格方法论与质量控制框架。用于：(1) 定义游戏美术风格规范（分辨率、调色板、光照方向等），
  (2) 指导 AI 生成像素美术素材时的 prompt 约束和后处理流程，
  (3) 角色/场景/UI/特效的设计规范和验收标准，
  (4) 外包美术素材的风格统一验收。
  触发词：像素美术、pixel art、游戏美术风格、美术规范、style guide、调色板、tilemap、sprite、角色动画。
---

# 像素游戏美术风格方法论

## 核心理念

**风格统一 > 单张精度**。一个风格统一的 60 分美术，比风格混乱的 90 分美术更有价值。

## 使用流程

### 1. 建立风格圣经（Style Guide）

任何项目开始前，必须先定义以下 6 项参数。用 `references/style-guide-template.md` 生成项目专属风格文档。

| 参数 | 选项 | 默认推荐 |
|------|------|----------|
| 像素密度 | 8×8 / 16×16 / 32×32 / 64×64 | **16×16**（万金油） |
| 调色板 | Pico-8(16色) / Endesga-32 / Sweetie-16 / 自定义 | **Endesga-32**（通用） |
| 轮廓线 | 有(黑色/暗色)/无 | 根据风格 |
| 光源方向 | 左上45° / 正上方 / 自定义 | **左上45°** |
| 阴影级数 | 2级 / 3级 | **2级（亮面→暗面→投影）** |
| 动画帧率 | 8 FPS / 12 FPS / 15 FPS | **12 FPS** |

### 2. 设计角色

流程：**剪影测试 → 色块填充 → 细节刻画**

- **剪影测试**：纯黑色画出角色轮廓，必须满足可识别性+独特性
- **色块填充**：3-5色填充主要区域（皮肤1-2梯度 + 服装主色1-2梯度 + 强调色1个）
- **细节刻画**：明暗关系（每色区3-4梯度）+ 关键细节（眼睛/武器/花纹）

动画帧数参考 → `references/animation-specs.md`

### 3. 设计场景与 Tilemap

流程：**基础块 → 变体(3-5个/种) → 过渡 → 装饰**

- Tile 尺寸：角色 16×16 配 Tile 16×16 或 32×32
- **变体是关键**——人眼对重复模式极敏感，3-5个变体随机排列大幅降低 Tile 感
- 视差滚动分层：远景(低饱和/模糊) → 中景 → 近景 → 前景(最鲜艳) → 叠加层(粒子/雾气)

详细规范 → `references/scene-design.md`

### 4. 设计 UI

**清晰 > 美观 > 风格统一**

- 按钮：最小 48×24px，支持 4 态（默认/悬停/按下/禁用）
- 面板：9-slice 九宫格缩放，边框 2-3px，内边距 8-12px
- 字体推荐：英文 m5x7 / Dogica，中文 Fusion Pixel（免费）/ 丁卯点阵体（付费）
- HUD：血量左上，小地图右上，技能底部中央

详细规范 → `references/ui-design.md`

### 5. 设计特效

**"少即是多"**——只在核心反馈、重要事件、环境氛围时用特效。

详细参数 → `references/vfx-specs.md`

---

## 关键技法速查

### Hue Shifting（色相偏移）

像素画最核心的调色技巧：
- **暗部**：色相向冷色（蓝/紫）偏移 + 降低饱和度
- **亮部**：色相向暖色（黄）偏移 + 提高饱和度
- 原理：模拟自然光照（阳光暖黄，阴影冷蓝）

示例：草地绿 `#5B8C3E` → 暗部 `#2E4A3A`（偏蓝绿） → 亮部 `#8BC34A`（偏黄绿）

### 自定义调色板 5 步法

1. 确定情绪基调（紧张=偏红橙 / 平静=偏蓝绿 / 诡异=偏紫暗绿）
2. 选 3-4 主色
3. 每主色用 Hue Shifting 生成 4-5 梯度
4. 添加 1-2 强调色（互补色或三角色）
5. 实际场景测试

### 抗锯齿（AA）

- 线条转折处加中间色像素
- 曲线凸面加亮色 AA，凹面加暗色 AA
- **16×16 以下角色不用 AA**（太小会模糊）

### 抖动（Dithering）

- ✅ 大面积渐变（天空/水面）、阴影过渡、复古风
- ❌ 小角色 sprite（会显脏）、动画帧中（会闪烁）

### 亚像素动画

通过改变相邻像素颜色模拟<1像素移动。适用：呼吸、水面微波、火焰摇曳。

---

## AI 辅助美术的后处理流程

AI 生成的像素画（如 Stable Diffusion + Pixel Art LoRA）**不能直接使用**，必须经过：

1. **降分辨率**：缩放到目标像素密度（最近邻插值，禁用双线性/双三次）
2. **调色板锁定**：所有颜色替换为项目调色板（Aseprite 一键替换）
3. **清理脏像素**：移除不在调色板内的颜色
4. **线条统一**：修正不一致的线条粗细
5. **光源校正**：确保光照方向与项目设定一致
6. **动画兼容性检查**：确认能拆分为合理的动画帧

### AI Prompt 约束模板

给 AI 生成像素美术时，prompt 应包含：

```
pixel art, [像素密度如 16x16], [调色板名如 endesga-32 palette],
[光源方向如 top-left lighting], [轮廓线如 dark outline / no outline],
[风格参考如 celeste-style / stardew-valley-style],
clean pixels, no anti-aliasing, transparent background
```

**负面 prompt**：
```
blurry, smooth gradients, high resolution, photorealistic,
anti-aliased edges, mixed pixel sizes, dirty pixels
```

---

## 验收 Checklist

### 角色 Sprite

- [ ] 剪影测试通过（纯黑可识别）
- [ ] 所有颜色在项目调色板内
- [ ] 所有动画帧脚底对齐
- [ ] Idle/Walk/Attack/Hurt/Death 动画完成
- [ ] 有预备动作和跟随动作
- [ ] 缩小到游戏实际尺寸仍清晰
- [ ] 与现有角色比例一致
- [ ] 导出格式正确（Sprite Sheet + JSON）

### 场景 Tileset

- [ ] 基础 Tile 完成（地面/墙壁/天花板）
- [ ] 每种基础 Tile 有 3-5 变体
- [ ] 过渡 Tile 完成
- [ ] 装饰 Tile 完成
- [ ] Tile 之间无缝隙
- [ ] 测试关卡铺设效果

### 风格一致性

- [ ] 灰度检查：转灰度后明暗关系清晰
- [ ] 缩略图检查：缩小25%后色调统一
- [ ] 并排对比：与 Style Guide 参考图一致
- [ ] 调色板验证：无越界颜色

---

## 参考文件索引

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `references/the-last-night-style.md` | The Last Night 2.5D filmic pixel art 风格实现指南 | 提到 The Last Night 风格/2.5D cinematic pixel/Low-fi hi-fi 时 |
| `references/style-guide-template.md` | 风格圣经文档模板 | 新项目启动时 |
| `references/animation-specs.md` | 动画帧数/帧率/重量感设计 | 设计角色动画时 |
| `references/scene-design.md` | 场景色彩规划/视差/光影/Auto-tiling | 设计场景时 |
| `references/ui-design.md` | UI组件规范/字体/HUD布局 | 设计UI时 |
| `references/vfx-specs.md` | 特效动画/粒子参数/后处理 | 设计特效时 |
| `references/palette-reference.md` | 调色板速查/场景配色方案 | 选色时 |
| `references/outsource-guide.md` | 外包Brief模板/验收清单/素材平台 | 外包美术时 |
| `references/tools-and-resources.md` | 工具推荐/免费素材/学习资源 | 选工具/找素材时 |
