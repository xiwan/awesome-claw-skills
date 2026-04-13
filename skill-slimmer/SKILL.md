---
name: skill-slimmer
description: Analyze and restructure bloated SKILL.md files into a lean three-layer architecture (必读/按需/示例). Use when (1) a SKILL.md exceeds 150 lines or feels cluttered, (2) designing a new skill and wanting the right structure from the start, (3) auditing all skills for context efficiency. Triggers on：skill 瘦身、skill 太长、精简 skill、slim skill、optimize skill structure.
---

# Skill Slimmer

Restructure SKILL.md files to minimize context window cost while preserving all information.

## Core Principle

**SKILL.md is read every time the skill triggers.** Every line costs tokens. The question for each paragraph: "Does the agent need this on every call, or only sometimes?"

## Three-Layer Architecture

```
SKILL.md (≤150 lines)          ← 必读层：每次调用都读
references/*.md                 ← 按需层：需要时才读  
examples/*.md                   ← 示例层：学习或调试时才读
```

### Layer 1: 必读层 (SKILL.md)
- 目标与定位（一句话）
- 硬性约束（表格形式，一目了然）
- 流程骨架（每步 2-3 行，细节指向 references/）
- 风格要点（精简版）
- 参考文档索引（指向 references/ 和 examples/）

### Layer 2: 按需层 (references/)
- 模式库 / 案例库
- 质检清单
- 历史教训与复盘
- 详细参数与配置
- API 文档 / Schema

### Layer 3: 示例层 (examples/)
- 完整示例文件
- 模板
- 风格参考样本

## 分类四问法

对 SKILL.md 中每个段落问四个问题：

| 问题 | 是 | 否 |
|------|---|---|
| 每次调用都需要？ | 留 SKILL.md | 拆出去 |
| 忘了会出事？（硬性约束） | 留 SKILL.md | 拆出去 |
| 是规则还是案例？ | 规则留 | 案例拆到 references/ |
| 是流程还是知识？ | 流程留 | 知识拆到 references/ |

**四问全"留" → 必须在 SKILL.md。其余 → 拆。**

## 工作流程

### 场景 A：瘦身现有 skill

1. **备份** 原始 SKILL.md → `SKILL-pre-slim-{YYYY-MM-DD}.md`（同目录，不删，瘦身完确认无误后用户自行清理）
2. **读取** SKILL.md 全文，统计行数和 token 估算
3. **分类** 每个段落/章节，用四问法标注"留/拆/删"
4. **生成拆分方案** 列出：
   - 哪些段落移到 references/（附建议文件名）
   - 哪些段落移到 examples/
   - 哪些段落可以删除（重复/过时）
   - 哪些段落需要压缩（案例过多、解释冗长）
5. **确认方案** 展示给用户，等批准
6. **执行拆分** 重写 SKILL.md + 创建 references/ 和 examples/ 文件
7. **验证** 检查交叉引用完整、无信息丢失、行数达标
8. **保留备份** 提醒用户备份文件已保留，确认效果满意后可自行删除

### 场景 B：设计新 skill

1. 提供三层架构模板（见 references/template.md）
2. 用户写完后检查是否超 150 行
3. 超标则按四问法建议拆分

## 瘦身标准

| 指标 | 健康 | 警告 | 必须瘦身 |
|------|------|------|---------|
| SKILL.md 行数 | ≤150 | 150-300 | >300 |
| references 单文件 | ≤200 行 | 200-400 | >400 |
| 案例/历史数据在 SKILL.md | 0 | 1-2 处 | >2 处 |
| 重复内容 | 0 | — | 任何 |

## 压缩技巧

- **表格替代段落**：约束条件用表格，一行一条
- **指向替代内联**：详细内容写 references/，SKILL.md 只留一行链接
- **祈使句替代解释**：`Hook ≤ 400 字` 比解释为什么要 400 字更省 token
- **删除"为什么"**：SKILL.md 留"做什么"，"为什么"放 references/ 的教训文档里

## 参考文档

- [references/template.md](references/template.md) — 新 skill 三层架构模板
