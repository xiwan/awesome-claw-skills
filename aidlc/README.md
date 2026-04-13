# AIDLC — AI Development Lifecycle

## 关于 AIDLC 与 awslabs/aidlc-workflows

本仓库的 [aidlc](.) 和 AWS 开源的 [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) 都叫 AIDLC，但理念和侧重点不同：

| | 本仓库 aidlc | awslabs/aidlc-workflows |
|---|---|---|
| 理念 | **版本驱动开发** — 每次开发先声明版本号和目标，全程追踪进度直到提交 | **自适应工作流** — 根据项目复杂度智能决定执行哪些阶段 |
| 侧重 | 执行与交付（HOW & SHIP） | 规划与设计（WHAT & WHY） |
| 结构 | 7 阶段线性流程，轻量单文件 | 3 Phase / ~15 Stages，多规则文件分层加载 |
| 适合 | 持续迭代、快速交付、单人 + AI agent | 大型项目从零规划、团队协作、多 stakeholder 审批 |
| 特色 | 版本日志追踪、scratch 验证、pre-commit 门禁、密钥扫描 | 需求分析、逆向工程、NFR 设计、扩展系统（security/testing） |

两者可以互补：用 awslabs 的 Inception 做项目规划，用本仓库的 aidlc 执行每个版本的开发交付。

---

## About AIDLC vs awslabs/aidlc-workflows

This repo's [aidlc](.) and AWS's open-source [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) share the AIDLC name but differ in philosophy:

| | This repo's aidlc | awslabs/aidlc-workflows |
|---|---|---|
| Philosophy | **Version-driven development** — declare version + goal before coding, track progress until commit | **Adaptive workflow** — intelligently decide which stages to execute based on complexity |
| Focus | Execution & delivery (HOW & SHIP) | Planning & design (WHAT & WHY) |
| Structure | 7-phase linear flow, single lightweight file | 3 Phases / ~15 Stages, layered rule files |
| Best for | Continuous iteration, fast delivery, solo dev + AI agent | Large-scale project planning, team collaboration, multi-stakeholder approval |
| Highlights | Version log tracking, scratch validation, pre-commit gates, secrets scanning | Requirements analysis, reverse engineering, NFR design, extension system (security/testing) |

They complement each other: use awslabs Inception for project planning, then use this repo's aidlc to execute each version's development cycle.
