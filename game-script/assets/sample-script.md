// 示例剧本：符合 references/script-format.md 的最小可用样例
// 同时是 scripts/script_lint.py 的回归样本，应当跑出 0 ERROR / 0 WARN
// 内容取自 dialogue-craft.md 里那段"改写后"的对话，并按重复词规则做了代称替换

# 场景 s02_manor_gate: 黑死馆前 / 深夜

* BG   bg_manor_gate_night
* BGM  bgm_tension_low
* SE   se_rain_loop
* CH   雷诺 进入 右

雷诺（举枪）: 举起手来！
> 雨点砸在石阶上，溅起细碎的白。
雷诺（逼近）: 这张图，你从哪拿的？
* CH   老人 进入 左
老人（冷笑）: 不知道。
雷诺（枪口抬高）: 快说，不然我开枪了。
老人（回避）: 嘁……黑死馆。
雷诺（皱眉）: 那地方我查过。
老人（低声）: 就在那儿，座钟里。
> 风灌进门廊，铜锁轻轻磕了一下。
老人（松肩）: 喂，那玩意儿可以放下了吧？

? 选项组 (id: s02_press)
  - 「继续逼问」 -> s03a_press [set: threatened=1]
  - 「放下枪，听他说」 -> s03b_talk [set: trust=trust+1]
  - 「提起座钟里的东西」 -> s03c_clock (需要: knows_clock==1) [set: showed_clue=1]

# 场景 s03a_press: 黑死馆前 / 深夜

* BG   bg_manor_gate_night
* BGM  bgm_tension_high
* FX   画面轻微抖动 0.3s

雷诺（枪管顶上前额）: 别动。
老人（喘息）: ……你要的东西，得换。
> 老人的手指在口袋边缘蜷了一下。
雷诺（咬牙）: 换什么。
老人（试探）: 你手里那半张。
雷诺（后退半步）: 那是我父亲留下的。
* SE   se_thunder
老人（眼神一亮）: 看来上头真记着埋点。
> 雷神在云层深处滚过，照亮了半张脸。

=> s04_gate_open
