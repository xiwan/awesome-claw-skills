---
name: skill-security-audit
description: 审计 skill 的安全风险。扫描凭据泄露、危险命令、网络外传、文件越界等问题。用于：(1) 安装新 skill 前的安全检查 (2) 定期审计现有 skills (3) 发布 skill 前的自检。触发词：skill 安全、审计、security audit、检查 skill。
---

# Skill Security Audit

审计 skills 目录中的安全风险，生成报告。

## 🚀 快速使用

### 安全安装（推荐）

```bash
# 替代 clawdhub install，自动审计
bash skills/skill-security-audit/scripts/safe-install.sh weather

# 安装指定版本
bash skills/skill-security-audit/scripts/safe-install.sh my-skill --version 1.2.3

# 有警告也强制安装
bash skills/skill-security-audit/scripts/safe-install.sh risky-skill --force
```

### 安全发布

```bash
# 替代 clawdhub publish，发布前审计
bash skills/skill-security-audit/scripts/safe-publish.sh ./my-skill --slug my-skill --version 1.0.0

# CRITICAL 问题会阻止发布，无法绕过
```

### 手动审计

```bash
# 审计单个 skill
bash skills/skill-security-audit/scripts/audit.sh skills/target-skill

# 审计所有 skills
bash skills/skill-security-audit/scripts/audit.sh skills/

# 包含文档文件（更严格）
bash skills/skill-security-audit/scripts/audit.sh skills/ --include-docs

# 输出 JSON（给程序用）
bash skills/skill-security-audit/scripts/audit.sh skills/ --json
```

## 🛡️ 检测项目

| 类别 | 严重程度 | 检测内容 |
|------|----------|----------|
| 凭据泄露 | 🔴 CRITICAL | OpenAI/Anthropic/AWS/GitHub 等 API key |
| 危险命令 | 🟠 HIGH | `rm -rf`、`sudo`、`eval()`、`curl \| bash` |
| 敏感目录 | 🟠 HIGH | `~/.ssh`、`~/.aws`、`/etc/passwd` |
| 网络请求 | 🟡 MEDIUM | HTTP 到非白名单域名 |
| 权限问题 | 🟡 MEDIUM | `chmod 777` |
| 依赖风险 | 🟢 LOW | 未锁定版本的依赖 |

## 📋 安装/发布行为

### safe-install.sh

| 问题级别 | 默认行为 | 可覆盖 |
|----------|----------|--------|
| CRITICAL | ❌ 阻止安装 | `--allow-critical`（危险！） |
| HIGH/MEDIUM | ⚠️ 询问确认 | `--force` |
| LOW | ✅ 允许 | - |

### safe-publish.sh

| 问题级别 | 默认行为 | 可覆盖 |
|----------|----------|--------|
| CRITICAL | ❌ 阻止发布 | **不可覆盖** |
| HIGH | ⚠️ 询问确认 | `--force` |
| MEDIUM | ⚠️ 询问确认 | `--force` |
| LOW | ✅ 允许 | - |

## 🔇 忽略误报

### 行内忽略

```bash
# security-audit: ignore-next-line
EXAMPLE_KEY="sk-test-not-real-key-for-documentation"
```

### 文件忽略

创建 `.security-audit-ignore`：
```
scripts/test_*.sh
references/examples/*
assets/*
```

## 📁 文件结构

```
skill-security-audit/
├── SKILL.md
├── scripts/
│   ├── audit.sh          # 核心审计脚本
│   ├── safe-install.sh   # 安全安装 wrapper
│   └── safe-publish.sh   # 安全发布 wrapper
└── references/
    └── detection-rules.md  # 检测规则详情
```

## ⚙️ 设置别名（可选）

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias skill-install='bash ~/clawd/skills/skill-security-audit/scripts/safe-install.sh'
alias skill-publish='bash ~/clawd/skills/skill-security-audit/scripts/safe-publish.sh'
alias skill-audit='bash ~/clawd/skills/skill-security-audit/scripts/audit.sh'

# 使用
skill-install weather
skill-publish ./my-skill --slug my-skill
skill-audit skills/
```
