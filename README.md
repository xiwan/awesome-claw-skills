# Awesome Claw Skills

A collection of useful skills for [Clawdbot](https://github.com/clawdbot/clawdbot) agents.

## Skills

| Skill | Description |
|-------|-------------|
| [skill-security-audit](./skill-security-audit/) | 审计 skill 的安全风险。扫描凭据泄露、危险命令、网络外传、文件越界等问题 |

## Installation

```bash
# Using ClawdHub CLI
clawdhub install <skill-name>

# Or manually copy to your skills directory
cp -r <skill-folder> ~/clawd/skills/
```

## Contributing

PRs welcome! Each skill should include:
- `SKILL.md` — Usage instructions and trigger words
- `scripts/` — Executable scripts (if any)
- `references/` — Documentation and rules (if any)

## License

MIT
