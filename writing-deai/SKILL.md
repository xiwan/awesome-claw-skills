---
name: writing-deai
description: AI写作痕迹深度自检工具。基于 claudisms.ai 禁词表，扫描文稿中的 AI 味词汇、结构和语气问题。用于：(1) 播客口播稿自检 (2) 知乎/小红书文案去AI感 (3) 任何正式输出前的最后一道防线。支持中英文检测。触发词：去AI味、claudisms、写作自检、AI痕迹、deai、文风检查。
---

# Writing De-AI 写作去AI味自检

## 用途

写完任何正式输出（口播稿、知乎文案、小红书笔记、文章）后，跑一遍这个检查。

## 快速使用

### 自动扫描（脚本）

```bash
python3 skills/writing-deai/scripts/scan_claudisms.py <file.md>
# 或管道输入
echo "This is worth noting that..." | python3 skills/writing-deai/scripts/scan_claudisms.py -
# JSON 输出
python3 skills/writing-deai/scripts/scan_claudisms.py <file.md> --json
```

### 人工检查流程（脚本扫不到的）

脚本能抓词汇和固定结构，但以下需要人眼判断：

1. **Cool people rule** — 内容是在"宣布自己重要"还是"用内容证明"？
2. **虚构观察** — 有没有"most people"类的无源断言？
3. **戏剧化程度匹配** — 动词的力度是否匹配实际影响？
4. **结构单调** — 是否连续4+短句？是否每段都是相同节奏？
5. **负面平行** — 文中有没有 "不是X，而是Y" 的结构？（中文版同样致命）
6. **加冕最高级** — 有没有"最重要的是"/"最关键的一点"式的单峰宣告？

## 自检清单（写完后过一遍）

- [ ] 跑 `scan_claudisms.py`，处理所有 ⚠️
- [ ] Ctrl+F 搜 `—`（em dash），全部改成 ` - `
- [ ] 检查开头：是不是宏大叙事开场？直接砍掉第一段试试
- [ ] 检查结尾：是不是在重述论点？如果去掉最后一句文章完整度不变，就去掉
- [ ] 全文搜"值得"/"不可否认"/"众所周知"等中文套话
- [ ] 检查是否有 "不是A，而是B" 的结构 — 最显眼的AI指纹

## 详细禁词表

完整列表见 `references/claudisms-banlist.md`（按需加载）。

## 注意事项

- 不是所有命中都必须改 — 有些词在特定语境下合理
- 脚本是辅助，最终判断靠人
- 中文AI味词汇还在持续积累中，发现新的随时加
- 播客口播稿额外注意：不要均匀撒口语填充词，集中在高认知负荷处才自然
