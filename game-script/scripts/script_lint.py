#!/usr/bin/env python3
"""游戏剧本机械体检 / lint。零第三方依赖。

解析 references/script-format.md 定义的轻量剧本格式，检查 10 条最常被违反的规则：

  E1 THEME_IN_DIALOGUE  主题词被角色直接说出口（需 --theme）
  E2 CHOICE_NO_EFFECT   选项既没有跳转也没有 flag 写入
  E3 FLAT_CHOICE        同组选项后果完全相同（E）或文本差异过小（W）
  E4 MISSING_DIRECTIVE  场景缺 BG 或场景头缺时间
  W1 LINE_TOO_LONG      单条台词超过字数上限
  W2 INFO_DENSITY       一句台词塞了多个关键信息
  W3 NO_ACTION          连续多条台词之间没有任何动作/表情/旁白/指示
  W4 MONOLOGUE          同一角色连续说太多条
  W5 REPEAT_WORD        同一场景内某个词反复出现
  W6 EXPOSITION         场景开头连续出现长台词（前置准备写成说明文）

用法：
    python3 script_lint.py my_script.md
    python3 script_lint.py my_script.md --max-line 30 --theme 友情 正义 --strict

--strict：存在 E 级问题时退出码 1（可挂 CI）。
"""

import argparse
import collections
import os
import re
import sys

CJK = re.compile(r"[\u4e00-\u9fff]")
# 场景头：# 场景 id: 标题 / 时间
RE_SCENE = re.compile(r"^#\s*(?:场景\s*)?([\w\-]+)\s*[:：]?\s*(.*)$")
RE_DIRECTIVE = re.compile(r"^\*\s*([A-Za-z]+)\s*(.*)$")
RE_NARRATION = re.compile(r"^>\s*(.+)$")
RE_CHOICE_GROUP = re.compile(r"^\?\s*(.*)$")
RE_CHOICE = re.compile(r"^\s*-\s*(.+)$")
RE_JUMP = re.compile(r"^=>\s*(.+)$")
# 台词：角色（表情）: 文本   —— 角色名不含空格和标点
RE_DIALOGUE = re.compile(r"^([^\s:：（(]{1,12})\s*(?:[（(]([^）)]*)[）)])?\s*[:：]\s*(.+)$")

# 信息点线索：数字、时间词、地点/机构后缀、专名标记
RE_NUM = re.compile(r"[0-9０-９一二三四五六七八九十百千万]")
TIME_WORDS = ("前几天", "昨天", "今天", "明天", "当年", "那天", "上周", "去年", "深夜", "清晨", "傍晚")
PLACE_SUFFIX = ("馆", "城", "村", "镇", "岛", "塔", "宫", "殿", "港", "山", "街", "所", "厅", "府")
STOP_CHARS = set("的了是我你他她它们这那就都还也很不没有和与在着过吗呢吧啊哦嗯把被给让从对为")


class Issue:
    def __init__(self, level, code, line, text, hint):
        self.level = level
        self.code = code
        self.line = line
        self.text = text
        self.hint = hint


def cjk_len(s):
    """按显示成本计字数：中日文字符算 1，其余非空白字符算 0.5。"""
    n = 0.0
    for ch in s:
        if ch.isspace():
            continue
        n += 1.0 if CJK.match(ch) else 0.5
    return int(round(n))


def ngrams(text, lo=2, hi=4):
    chars = [c for c in text if CJK.match(c)]
    out = []
    for n in range(lo, hi + 1):
        for i in range(len(chars) - n + 1):
            g = "".join(chars[i:i + n])
            if all(c in STOP_CHARS for c in g):
                continue
            out.append(g)
    return out


def similarity(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def info_points(text):
    """粗估一句话里的关键信息点数量。"""
    pts = 0
    if RE_NUM.search(text):
        pts += 1
    if any(w in text for w in TIME_WORDS):
        pts += 1
    if any(text.count(s) for s in PLACE_SUFFIX if s in text):
        pts += 1
    # 逗号/顿号分句数超过 3，视为并列信息过多
    clauses = len(re.findall(r"[，,、；;]", text))
    if clauses >= 3:
        pts += 1
    return pts, clauses


class Scene:
    def __init__(self, sid, title, line):
        self.sid = sid
        self.title = title
        self.line = line
        self.has_time = "/" in title or "／" in title
        self.has_bg = False
        self.dialogues = []      # (line, speaker, emotion, text)
        self.beats = []          # 事件流：("dialogue"|"action", line)
        self.text_blob = []


def parse(path):
    scenes = []
    cur = None
    choice_groups = []           # (group_line, group_label, [ (line, raw) ])
    pending_group = None

    with open(path, encoding="utf-8") as fh:
        for no, raw in enumerate(fh, 1):
            line = raw.rstrip("\n").strip()
            if not line or line.startswith("//"):
                continue

            m = RE_SCENE.match(line)
            if m and line.startswith("#"):
                cur = Scene(m.group(1), m.group(2), no)
                scenes.append(cur)
                pending_group = None
                continue

            m = RE_DIRECTIVE.match(line)
            if m:
                if cur:
                    if m.group(1).upper() == "BG":
                        cur.has_bg = True
                    cur.beats.append(("action", no))
                pending_group = None
                continue

            m = RE_NARRATION.match(line)
            if m:
                if cur:
                    cur.beats.append(("action", no))
                    cur.text_blob.append(m.group(1))
                pending_group = None
                continue

            m = RE_CHOICE_GROUP.match(line)
            if m:
                pending_group = (no, m.group(1), [])
                choice_groups.append(pending_group)
                continue

            m = RE_CHOICE.match(line)
            if m and pending_group is not None:
                pending_group[2].append((no, m.group(1)))
                continue

            if RE_JUMP.match(line):
                pending_group = None
                continue

            m = RE_DIALOGUE.match(line)
            if m and cur:
                speaker, emotion, text = m.group(1), m.group(2), m.group(3)
                cur.dialogues.append((no, speaker, emotion, text))
                cur.beats.append(("dialogue", no))
                cur.text_blob.append(text)
                if emotion:
                    cur.beats.append(("action", no))
                pending_group = None
                continue

            pending_group = None

    return scenes, choice_groups


def check(path, max_line, themes, monologue_max, no_action_max, repeat_min):
    scenes, groups = parse(path)
    issues = []

    for sc in scenes:
        if not sc.has_bg:
            issues.append(Issue("E", "MISSING_DIRECTIVE", sc.line, f"场景 {sc.sid}",
                                "缺 `* BG <背景ID>`，美术/程序无法确定场景"))
        if not sc.has_time:
            issues.append(Issue("E", "MISSING_DIRECTIVE", sc.line, f"场景 {sc.sid}",
                                "场景头缺时间（`# 场景 id: 地点 / 时间`），容易出剧情 bug"))

        # 台词级检查
        for (no, speaker, emotion, text) in sc.dialogues:
            n = cjk_len(text)
            if n > max_line:
                issues.append(Issue("W", "LINE_TOO_LONG", no, f"{speaker}: {text[:24]}…",
                                    f"{n} 字 > 上限 {max_line}，拆成两三条短台词"))
            pts, clauses = info_points(text)
            if pts >= 3 or clauses >= 4:
                issues.append(Issue("W", "INFO_DENSITY", no, f"{speaker}: {text[:24]}…",
                                    f"信息点≈{pts}、分句 {clauses}：一句台词只传一个关键信息"))
            for kw in themes:
                if kw in text:
                    issues.append(Issue("E", "THEME_IN_DIALOGUE", no, f"{speaker}: {text[:24]}…",
                                        f"主题词「{kw}」被角色说出口，改用行为/结局来表现"))

        # 连续同角色独白
        run_speaker, run_start, run_len = None, None, 0
        for (no, speaker, _e, _t) in sc.dialogues:
            if speaker == run_speaker:
                run_len += 1
            else:
                run_speaker, run_start, run_len = speaker, no, 1
            if run_len == monologue_max:
                issues.append(Issue("W", "MONOLOGUE", run_start, f"{speaker} 连续 {run_len} 条",
                                    "拆给对手戏，或插入动作/旁白打断"))

        # 连续台词无动作
        streak, streak_start = 0, None
        for kind, no in sc.beats:
            if kind == "dialogue":
                streak += 1
                if streak == 1:
                    streak_start = no
                if streak == no_action_max:
                    issues.append(Issue("W", "NO_ACTION", streak_start,
                                        f"连续 {streak} 条台词无动作/表情/旁白",
                                        "加表情 `（）`、动作旁白或指示行，让台词有动感"))
            else:
                streak = 0

        # 场景内重复词
        blob = "".join(sc.text_blob)
        counter = collections.Counter(ngrams(blob))
        reported = set()
        for gram, cnt in counter.most_common():
            if cnt < repeat_min or len(gram) < 2:
                continue
            if any(gram in r for r in reported):
                continue
            reported.add(gram)
            issues.append(Issue("W", "REPEAT_WORD", sc.line, f"场景 {sc.sid}「{gram}」×{cnt}",
                                "换代称或直接删，重复会让台词显得冗长"))
            if len(reported) >= 3:
                break

        # 开场说明文
        head = sc.dialogues[:3]
        long_head = [d for d in head if cjk_len(d[3]) > max_line * 0.8]
        if len(long_head) >= 2:
            issues.append(Issue("W", "EXPOSITION", head[0][0], f"场景 {sc.sid} 开场",
                                "开场连续长台词=说明文，用事件把设定漏出来"))

    # 选项检查
    for (gline, label, opts) in groups:
        parsed = []
        for (no, raw) in opts:
            has_jump = "->" in raw or "→" in raw
            has_flag = "[set:" in raw or "[set：" in raw
            if not has_jump and not has_flag:
                issues.append(Issue("E", "CHOICE_NO_EFFECT", no, raw[:40],
                                    "选项既无跳转也无 flag：玩家会发现选了跟没选一样"))
            body = re.split(r"->|→|\[", raw)[0]
            body = re.sub(r"[「」\"'\s]", "", body)
            jump = re.search(r"(?:->|→)\s*([\w\-]+)", raw)
            flags = re.findall(r"\[set[:：]\s*([^\]]+)\]", raw)
            parsed.append({
                "line": no,
                "text": body,
                "jump": jump.group(1) if jump else None,
                "flags": tuple(sorted(f.strip() for f in flags)),
            })
        for i in range(len(parsed)):
            for j in range(i + 1, len(parsed)):
                a, b = parsed[i], parsed[j]
                # 后果完全相同 = 无意义选项（最硬的判据）
                if a["jump"] == b["jump"] and a["flags"] == b["flags"] and (a["jump"] or a["flags"]):
                    issues.append(Issue("E", "FLAT_CHOICE", b["line"],
                                        f"{a['text']} / {b['text']}",
                                        "两个选项的跳转与 flag 完全相同：后果一致，玩家会觉得选了没用"))
                    continue
                sim = max(similarity(a["text"], b["text"]),
                          similarity(ngrams(a["text"], 2, 2), ngrams(b["text"], 2, 2)))
                if sim > 0.6:
                    issues.append(Issue("W", "FLAT_CHOICE", b["line"],
                                        f"{a['text']} / {b['text']}",
                                        f"文本重合 {sim:.0%}：选项差异太小，玩家看不出判断依据"))

    return scenes, groups, issues


def main(argv=None):
    ap = argparse.ArgumentParser(description="游戏剧本机械体检")
    ap.add_argument("files", nargs="+", help="剧本文件（见 references/script-format.md）")
    ap.add_argument("--max-line", type=int, default=40, help="单条台词字数上限，默认 40")
    ap.add_argument("--theme", nargs="*", default=[], help="主题词表，出现在台词里即报错")
    ap.add_argument("--monologue-max", type=int, default=3, help="同角色连续台词上限，默认 3")
    ap.add_argument("--no-action-max", type=int, default=4, help="无动作连续台词上限，默认 4")
    ap.add_argument("--repeat-min", type=int, default=3, help="场景内重复词报警次数，默认 3")
    ap.add_argument("--strict", action="store_true", help="存在 E 级问题时退出码 1")
    args = ap.parse_args(argv)

    total_e = total_w = 0
    for path in args.files:
        if not os.path.exists(path):
            print(f"skip {path}: 文件不存在", file=sys.stderr)
            continue
        scenes, groups, issues = check(path, args.max_line, args.theme,
                                       args.monologue_max, args.no_action_max,
                                       args.repeat_min)
        n_dlg = sum(len(s.dialogues) for s in scenes)
        n_opt = sum(len(g[2]) for g in groups)
        print(f"\n=== {os.path.basename(path)} ===")
        print(f"  场景 {len(scenes)} / 台词 {n_dlg} / 选项组 {len(groups)}（选项 {n_opt}）")
        if n_dlg:
            avg = sum(cjk_len(d[3]) for s in scenes for d in s.dialogues) / n_dlg
            print(f"  平均台词长度 {avg:.1f} 字（上限 {args.max_line}）")

        issues.sort(key=lambda i: (i.line, i.code))
        for it in issues:
            print(f"  [{it.level}] {it.code:<18} L{it.line:<4} {it.text}")
            print(f"      → {it.hint}")
        e = sum(1 for i in issues if i.level == "E")
        w = len(issues) - e
        total_e += e
        total_w += w
        print(f"  小结：{e} ERROR / {w} WARN" if issues else "  小结：无问题")

    print(f"\n合计 {total_e} ERROR / {total_w} WARN")
    if args.strict and total_e:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
