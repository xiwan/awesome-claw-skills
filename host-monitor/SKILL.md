---
name: host-monitor
description: 监控宿主机的 CPU、内存、磁盘使用情况。在资源紧张时主动告警。用于：(1) 检查系统资源状态 (2) 设置资源告警阈值 (3) 在 heartbeat 中定期监控。触发词：系统资源、CPU、内存、磁盘、硬盘、监控、告警。
---

# Host Monitor 🖥️

监控宿主机资源使用情况，资源紧张时主动通知。

## 快速检查

```bash
scripts/check_resources.sh
```

输出示例：
```
=== Host Resources ===
CPU:    15% used (8 cores)
Memory: 62% used (4.9G / 7.9G)
Disk:   17% used (4.6G / 29G)
Status: ✅ All OK
```

## 告警阈值

| 资源 | 警告 | 危险 |
|------|------|------|
| CPU | 80% | 95% |
| 内存 | 85% | 95% |
| 磁盘 | 80% | 90% |

## Heartbeat 集成

在 `HEARTBEAT.md` 中添加：

```markdown
## 系统资源监控（每小时）
运行 `skills/host-monitor/scripts/check_resources.sh`
如果输出包含 ⚠️ 或 🔴，立即通知鲁伊科斯塔
```

## 手动检查命令

如果脚本不可用，可直接运行：

```bash
# CPU 使用率
top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8"%"}'

# 内存使用
free -h | awk '/Mem:/ {printf "%.0f%% (%s / %s)\n", $3/$2*100, $3, $2}'

# 磁盘使用
df -h / | awk 'NR==2 {print $5 " (" $3 " / " $2 ")"}'
```

## 告警时通知格式

```
⚠️ 资源告警

[资源类型]: [当前值] (阈值: [阈值])
建议: [具体建议]
```

示例：
```
⚠️ 资源告警

磁盘: 85% used (阈值: 80%)
建议: 清理日志或临时文件，或考虑扩容
```
