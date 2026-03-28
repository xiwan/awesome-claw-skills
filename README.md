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
