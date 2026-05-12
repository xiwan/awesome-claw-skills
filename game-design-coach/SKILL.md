---
name: game-design-coach
description: '游戏设计教练 — 引导用户从一句话想法逐步完善为高质量的 OpenGame prompt。当用户说"设计游戏"、"游戏点子"、"帮我想个游戏"、"game design"、"完善prompt"等类似指令时使用。'
---

# Game Design Coach — OpenGame Prompt 引导器

将用户模糊的一句话游戏想法，通过结构化提问逐步引导为一个高质量、可直接喂给 OpenGame 的完整 prompt。

## 设计理念

OpenGame 的生成质量高度依赖 prompt 质量。一个好的 prompt 需要覆盖 6 个维度：
1. **核心玩法机制**（不是"做个好玩的游戏"，而是具体的交互规则）
2. **游戏类型/物理模型**（决定 OpenGame 选择哪个 template module）
3. **视觉风格**（像素风、霓虹、手绘、写实 16-bit 等）
4. **角色与敌人设计**（能力、AI 行为、Boss 机制）
5. **关卡/内容结构**（几关、难度曲线、场景变化）
6. **UI 与反馈**（血条、分数、特效、音效氛围）

## 引导流程

**总体原则**：
- 每个问题都给选项，用户只需"选"不需要"想"
- 用户说"不知道"/"你来定"/"都行" → 采用推荐默认值，继续推进
- 不要连续问超过 3 个问题 — 如果用户明显没想法，用默认值快速推进到 Step 5 组装 prompt
- 最终在 Step 6 让用户看完整 prompt 再调整，比逐个问题纠结高效得多

收到用户的初始想法后，按以下步骤引导：

### Step 1: 分类确认

根据用户描述判断游戏物理模型，向用户确认：

| Module | 判断依据 | 典型游戏 |
|--------|----------|----------|
| platformer | 角色会掉落、有重力 | Mario, 街霸, Terraria |
| top_down | 自由移动、俯视角 | Zelda, 吸血鬼幸存者 |
| grid_logic | 网格移动、回合制 | 推箱子, 火焰纹章, 消消乐 |
| tower_defense | 固定路径、波次敌人 | 保卫萝卜, Bloons TD |
| ui_heavy | 主要是 UI 交互 | 卡牌游戏, 视觉小说 |

**输出**：「你的游戏听起来是一个 [类型]，对吗？」

### Step 2: 核心机制深挖（最关键）

**引导原则：每个问题必须提供 2-3 个具体选项 + 一个推荐默认值。用户只需说"选 A"或"都行你定"。**

如果用户说"不确定"/"你来定"/"都行"，直接采用推荐默认值并继续，不要反复追问。

针对已确认的类型，提出 2-3 个选择题：

**platformer 类**：

Q1: 战斗方式？
- A) 近战连击（拳脚组合，像街霸）← 推荐，手感好
- B) 远程射击（枪/魔法弹，像魂斗罗）
- C) 混合（近战+远程切换）

Q2: 要不要大招/必杀技？
- A) 要！冲刺斩 ← 推荐，简单帅气
- B) 要！全屏 AOE 清场
- C) 不要，保持简单

Q3: Boss 战？
- A) 有，最后一关一个 Boss，多阶段变身 ← 推荐
- B) 每关都有小 Boss
- C) 没有 Boss，纯闯关

**top_down 类**：

Q1: 游戏节奏？
- A) 生存模式 — 敌人一波波来，活越久分越高（像吸血鬼幸存者）← 推荐
- B) 探索模式 — 一个个房间推进（像塞尔达地牢）

Q2: 武器？
- A) 近战刀剑 ← 推荐，配合俯视角手感好
- B) 远程弓箭/枪
- C) 多武器可切换

Q3: 成长系统？
- A) 有，升级选技能（Roguelike 风）← 推荐
- B) 没有，纯操作

**tower_defense 类**：

Q1: 塔的风格？给我一个主题就行，我来设计 3 种塔。
- 示例：猫咪、中世纪、科幻、植物、美食……
- 默认：我帮你设计 3 种经典塔（单体输出/AOE 范围/减速控制）

Q2: 几波敌人？
- A) 5 波（短局，适合休闲）← 推荐
- B) 10 波（中等长度）
- C) 无尽模式

**grid_logic 类**：

Q1: 核心玩法？
- A) 推箱子/滑块类（策略思考）← 推荐
- B) 三消/匹配类（爽快连锁）
- C) 回合战棋类（走格子打仗）

Q2: 关卡数量？
- A) 5 关，逐渐变难 ← 推荐
- B) 10+ 关
- C) 随机生成

**ui_heavy 类**：

Q1: 核心玩法？
- A) 卡牌对战（出牌打怪）← 推荐
- B) 答题/知识问答
- C) 视觉小说（选择分支剧情）

Q2: 有没有数值对抗（HP、攻击力）？
- A) 有，打败对手获胜 ← 推荐
- B) 没有，纯叙事/纯答题

### Step 3: 视觉与氛围

提供选项而非开放问题：

「视觉风格选一个（或告诉我你喜欢的）：」
- A) 90 年代街机像素风（硬核、怀旧）← 动作游戏推荐
- B) 可爱手绘 Kawaii（粉彩、圆润）← 休闲游戏推荐
- C) 霓虹赛博朋克（暗底+荧光色）
- D) 哥特暗黑奇幻（阴暗、大气）
- E) 极简几何（干净、现代）
- F) 其他（你描述，我来翻译成美术方向）

「场景设定？」
- 给个关键词就行：太空 / 中世纪 / 都市 / 森林 / 海底 / 地狱 / 校园……
- 如果没想法，我根据你的游戏主题推荐

### Step 4: 内容规模

快速确认（有默认值，用户可以直接跳过）：

- 关卡数？默认 **3 关**（开头简单 → 中间加难度 → 最终 Boss）
- 如果用户没有强烈意见，直接用默认值继续

**"都行"快速通道**：如果用户在 Step 2-4 中多次说"你来定"，可以跳过剩余问题，直接用推荐默认值组装 prompt，然后在 Step 6 让用户审核调整。

### Step 5: 组装 Prompt

将收集到的信息组装为 OpenGame 格式的 prompt，遵循以下模板：

```
Build a [类型] game [主题/IP].
[核心玩法描述 — 2-3 句话说清楚玩家做什么].
[角色能力 — 列出具体的攻击/技能].
[敌人设计 — 类型和行为].
[关卡结构 — 几关、场景描述].
[视觉风格 — 一句话锚定美术方向].
[UI/反馈 — 血条、分数、特效等].
```

### Step 6: 确认与优化

将组装好的 prompt 展示给用户，询问：
- 「这个 prompt 是否符合你的想法？有什么要调整的？」
- 如果用户满意，提供最终 prompt 并建议调用 `opengame` skill 生成

## 好 Prompt vs 坏 Prompt 对比

**❌ 坏 prompt**：
> 做一个好玩的射击游戏

**✅ 好 prompt**：
> Build a side-scrolling action platformer starring a space marine fighting through 3 levels: an Alien Hive, a Crashed Spaceship, and a Volcanic Planet. The player has a blaster (ranged), a plasma sword (melee combo), and a screen-clearing Orbital Strike ultimate. Enemies include patrol drones, charging aliens, and a final boss with 3 phases (shield → rage → self-destruct). Art style: gritty 16-bit sci-fi pixel art with neon highlights. Show health bar, ammo count, and boss HP. Screen shake on explosions.

## 关键原则

1. **具体胜过抽象** — "damage=30, HP=100" 比 "适当的伤害" 好
2. **机制胜过主题** — 先确定玩法规则，再包装故事
3. **约束胜过自由** — 明确的限制（3 关、2 种武器）比"丰富的内容"产出更好
4. **英文 prompt 优先** — OpenGame 的 template 和 GDD 系统都是英文的，英文 prompt 生成质量更高
5. **单一 HTML 可选** — 如果是简单游戏，可以加 "Single HTML file, Canvas rendering" 来简化输出

## 与 opengame skill 的衔接

当 prompt 完善后，引导用户：
1. 确认最终 prompt
2. 建议使用 `opengame` skill 生成游戏
3. 生成后可用 `s3-deploy` skill 部署到 CDN

## 示例对话

**用户**：我想做一个猫咪塔防游戏

**Coach 引导**：
1. 确认类型 → tower_defense ✓
2. 深挖机制 → 3 种猫塔（远程狙击猫、AOE 胖橘、减速布偶猫）、敌人是老鼠/吸尘器/黄瓜
3. 视觉 → 手绘 Kawaii 风格、粉彩色调
4. 规模 → 5 波敌人、最后一波 Boss 是巨型扫地机器人
5. 组装 prompt →

```
Build a hilarious tower defense game where cute cats defend a Golden Tuna Can from household pests. Towers: Sniper Siamese (long range, single target), Fat Orange Cat (throws buns for AOE splash), and Ragdoll Cat (slows enemies in area). Enemies: mice (fast, low HP), cucumbers (medium, cats get scared debuff), vacuum cleaners (tanky, boss-type). 5 waves with increasing difficulty, final wave boss is a Giant Roomba with shield phases. Art style: hand-drawn pastel Kawaii with bouncy animations. Show: wave counter, gold/tuna currency, cat mood indicators.
```
