# Awesome Claw Skills

为 [Clawdbot](https://github.com/clawdbot/clawdbot) Agent 打造的实用技能合集。

> 💡 **声明**：这些 skill 都是我个人觉得好用的，但不代表对所有人都适用。欢迎 fork 后根据自己的需求修改！

## ⚠️ 安全建议

**在使用任何 skill 之前，建议先用 `skill-security-audit` 扫描生成安全报告。** 这能帮你发现潜在的凭据泄露、危险命令、网络外传等风险。

## 技能列表

| 技能 | 描述 |
|------|------|
| [host-monitor](./host-monitor/) | 监控宿主机 CPU、内存、磁盘使用率，资源紧张时主动告警。适合 heartbeat 定期检查 |
| [pptx-translator](./pptx-translator/) | 翻译 PPT 文件。支持 Amazon Translate（传统机器翻译）和 Bedrock LLM（大语言模型翻译） |
| [skill-security-audit](./skill-security-audit/) | 审计 skill 的安全风险。扫描凭据泄露、危险命令、网络外传、文件越界等问题 |
| [zip-compress](./zip-compress/) | 压缩文件和目录为 ZIP 归档。支持排除 .git、node_modules 等模式 |
| [aidlc](./aidlc/) | AI Development Lifecycle — AI agent 标准化开发流程。涵盖代码阅读、设计、验证、实现、测试、文档、提交 7 个阶段 |
| [jike](./jike/) | 即刻社交网络客户端 — QR 扫码登录、刷 Feed、发帖评论搜索、Token 自动刷新 |
| [xiaoyuzhou-monitor](./xiaoyuzhou-monitor/) | 小宇宙播客数据监控 — 播放量、订阅者、评论，Token 自动刷新 |
| [skill-slimmer](./skill-slimmer/) | SKILL.md 瘦身工具 — 用四问法将臃肿的 SKILL.md 重构为三层架构（必读/按需/示例），最小化 context window 开销 |

## 关于 AIDLC 与 awslabs/aidlc-workflows

本仓库的 [aidlc](./aidlc/) 和 AWS 开源的 [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) 都叫 AIDLC，但理念和侧重点不同：

| | 本仓库 aidlc | awslabs/aidlc-workflows |
|---|---|---|
| 理念 | **版本驱动开发** — 每次开发先声明版本号和目标，全程追踪进度直到提交 | **自适应工作流** — 根据项目复杂度智能决定执行哪些阶段 |
| 侧重 | 执行与交付（HOW & SHIP） | 规划与设计（WHAT & WHY） |
| 结构 | 7 阶段线性流程，轻量单文件 | 3 Phase / ~15 Stages，多规则文件分层加载 |
| 适合 | 持续迭代、快速交付、单人 + AI agent | 大型项目从零规划、团队协作、多 stakeholder 审批 |
| 特色 | 版本日志追踪、scratch 验证、pre-commit 门禁、密钥扫描 | 需求分析、逆向工程、NFR 设计、扩展系统（security/testing） |

两者可以互补：用 awslabs 的 Inception 做项目规划，用本仓库的 aidlc 执行每个版本的开发交付。

## 安装

```bash
# 克隆仓库
git clone https://github.com/xiwan/awesome-claw-skills.git

# 复制需要的 skill 到你的 skills 目录
cp -r awesome-claw-skills/<skill-name> ~/clawd/skills/
```

## 贡献

欢迎 PR！每个 skill 应包含：
- `SKILL.md` — 使用说明和触发词
- `scripts/` — 可执行脚本（如有）
- `references/` — 文档和规则（如有）

---

# English

A collection of useful skills for [Clawdbot](https://github.com/clawdbot/clawdbot) agents.

> 💡 **Disclaimer**: These skills are what I personally find useful, but they may not suit everyone. Feel free to fork and modify them to fit your own needs!

## ⚠️ Security Recommendation

**Before using any skill, it's recommended to scan it with `skill-security-audit` to generate a security report.** This helps identify potential credential leaks, dangerous commands, data exfiltration, and other risks.

## Skills

| Skill | Description |
|-------|-------------|
| [host-monitor](./host-monitor/) | Monitor host CPU, memory, and disk usage. Alerts when resources are strained. Great for heartbeat checks |
| [pptx-translator](./pptx-translator/) | Translate PPT files. Supports Amazon Translate (traditional MT) and Bedrock LLM (context-aware translation) |
| [skill-security-audit](./skill-security-audit/) | Audit skill security risks. Scans for credential leaks, dangerous commands, data exfiltration, and file boundary violations |
| [zip-compress](./zip-compress/) | Compress files and directories into ZIP archives. Supports excluding patterns like .git, node_modules |
| [aidlc](./aidlc/) | AI Development Lifecycle — standardized dev workflow for AI agents. Covers orientation, design, scratch validation, implementation, testing, docs, and commit |
| [jike](./jike/) | Jike social network client — QR login, feed reading, posting, commenting, searching, auto token refresh |
| [xiaoyuzhou-monitor](./xiaoyuzhou-monitor/) | Xiaoyuzhou podcast monitoring — play counts, subscribers, comments, auto token refresh |
| [skill-slimmer](./skill-slimmer/) | SKILL.md slimming tool — restructure bloated SKILL.md into lean three-layer architecture (must-read / on-demand / examples) to minimize context window cost |

## About AIDLC vs awslabs/aidlc-workflows

This repo's [aidlc](./aidlc/) and AWS's open-source [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) share the AIDLC name but differ in philosophy:

| | This repo's aidlc | awslabs/aidlc-workflows |
|---|---|---|
| Philosophy | **Version-driven development** — declare version + goal before coding, track progress until commit | **Adaptive workflow** — intelligently decide which stages to execute based on complexity |
| Focus | Execution & delivery (HOW & SHIP) | Planning & design (WHAT & WHY) |
| Structure | 7-phase linear flow, single lightweight file | 3 Phases / ~15 Stages, layered rule files |
| Best for | Continuous iteration, fast delivery, solo dev + AI agent | Large-scale project planning, team collaboration, multi-stakeholder approval |
| Highlights | Version log tracking, scratch validation, pre-commit gates, secrets scanning | Requirements analysis, reverse engineering, NFR design, extension system (security/testing) |

They complement each other: use awslabs Inception for project planning, then use this repo's aidlc to execute each version's development cycle.

## Installation

```bash
# Clone the repository
git clone https://github.com/xiwan/awesome-claw-skills.git

# Copy the skill you need to your skills directory
cp -r awesome-claw-skills/<skill-name> ~/clawd/skills/
```

## Contributing

PRs welcome! Each skill should include:
- `SKILL.md` — Usage instructions and trigger words
- `scripts/` — Executable scripts (if any)
- `references/` — Documentation and rules (if any)

## License

MIT
