# 新 Skill 三层架构模板

## SKILL.md 模板

```markdown
---
name: {skill-name}
description: {一句话说清做什么 + 什么时候触发}
---

# {Skill Name}

> ⚠️ {关键约束，如模型要求}

## 目标

{一句话定位}

## 硬性约束

| 约束 | 值 |
|------|---|
| {约束1} | {值} |
| {约束2} | {值} |

## 工作流程

### 1. {步骤名}
{2-3 行描述}
> 详细参数见 [references/{file}.md](references/{file}.md)

### 2. {步骤名}
{2-3 行描述}

### 3. {步骤名}
{2-3 行描述}

## 风格 / 规范
{精简要点，5-10 行}

## 输出
{格式、交付方式}

## 参考文档
- [references/{patterns}.md](references/{patterns}.md) — {说明}
- [references/{checklist}.md](references/{checklist}.md) — {说明}
- [examples/{sample}.md](examples/{sample}.md) — {说明}
```

## 目录结构模板

```
skill-name/
├── SKILL.md                    ≤150 行
├── references/
│   ├── {patterns}.md           模式库 / 案例库
│   ├── {checklist}.md          质检清单
│   └── {detailed-guide}.md     详细指南
└── examples/
    └── {sample}.md             完整示例
```

## 自检清单

- [ ] SKILL.md ≤ 150 行？
- [ ] 所有案例/历史数据在 references/ 而非 SKILL.md？
- [ ] 约束条件用表格而非段落？
- [ ] 每个 references/ 文件在 SKILL.md 有索引链接？
- [ ] references/ 单文件 ≤ 200 行？
- [ ] 无重复内容（SKILL.md 和 references/ 之间不说同一件事）？
