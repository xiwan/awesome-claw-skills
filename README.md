# Awesome Claw Skills

为 [Clawdbot](https://github.com/clawdbot/clawdbot) Agent 打造的实用技能合集。

## ⚠️ 安全建议

**在使用任何 skill 之前，建议先用 `skill-security-audit` 扫描生成安全报告。** 这能帮你发现潜在的凭据泄露、危险命令、网络外传等风险。

## 技能列表

| 技能 | 描述 |
|------|------|
| [skill-security-audit](./skill-security-audit/) | 审计 skill 的安全风险。扫描凭据泄露、危险命令、网络外传、文件越界等问题 |
| [zip-compress](./zip-compress/) | 压缩文件和目录为 ZIP 归档。支持排除 .git、node_modules 等模式 |

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

## ⚠️ Security Recommendation

**Before using any skill, it's recommended to scan it with `skill-security-audit` to generate a security report.** This helps identify potential credential leaks, dangerous commands, data exfiltration, and other risks.

## Skills

| Skill | Description |
|-------|-------------|
| [skill-security-audit](./skill-security-audit/) | Audit skill security risks. Scans for credential leaks, dangerous commands, data exfiltration, and file boundary violations |
| [zip-compress](./zip-compress/) | Compress files and directories into ZIP archives. Supports excluding patterns like .git, node_modules |

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
