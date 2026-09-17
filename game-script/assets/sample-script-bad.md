// 反例剧本：故意把 10 条规则全踩一遍，用来验证 script_lint.py 能报出问题
// 跑法：python3 ../scripts/script_lint.py sample-script-bad.md --theme 友情 正义 --strict

# 场景 s01_bad: 黑死馆前

// ↑ 缺时间 → MISSING_DIRECTIVE
// ↓ 全场景没有 * BG → MISSING_DIRECTIVE

雷诺: 这张地图是我前几天在城外一个名叫黑死馆的别墅的座钟里偶然发现的，当时我正在调查父亲的死因。
雷诺: 那张地图上标着三个埋藏点，分别在东边的港口、西边的旧塔和北边的雪山，一共要走十二天。
雷诺: 你拿这张地图想干什么，难道你也知道我父亲的遗物就藏在地图标记的那个地方吗？
老人: 我终于明白了，友情才是最强大的力量。
雷诺: 地图是我的，地图上的宝藏也是我的，你别想拿走这张地图。

? 选项组 (id: s01_flat)
  - 「我知道了」 -> s02_bad
  - 「我明白了」 -> s02_bad
  - 「继续逼问他」 -> s02_press [set: threatened=1]
  - 「继续逼问她」 -> s02_press2 [set: pressed=1]
  - 「随便」
