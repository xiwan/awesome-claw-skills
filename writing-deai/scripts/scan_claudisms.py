#!/usr/bin/env python3
"""
writing-deai: AI写作痕迹自动检测脚本
扫描文本文件，标记命中 claudisms banlist 的词汇和结构。
输出：行号 + 命中项 + 建议替换
"""

import re
import sys
import json
from pathlib import Path

# === 词汇级检测 ===
VOCAB_PATTERNS = [
    # (pattern, category, suggestion)
    # 伪深沉动词
    (r'\bsit with\b', '伪深沉', '删掉或用具体描述替代'),
    (r'\bworth sitting with\b', '伪深沉', '删掉'),
    (r'\b(keep )?(arriving at|coming back to)\b', '伪深沉', '直接说结论'),
    (r'\bsurface\b(?=\s+(the|a|an|this|that|some|any|insights?|patterns?|issues?))', '伪深沉', '用 reveal/show/find'),
    (r'\b(names?|naming)\b(?=\s+(the|what|this|that|it))', '伪深沉', '用 says/identifies/calls'),
    (r'\bload-bearing\b', '伪深沉', '用 critical/essential'),
    (r'\bthe engine\b', '伪深沉', '用 what drives/what works'),
    (r'\bhits? hardest\b', '伪深沉', '用 is most affected/shows up first'),
    (r'\blands? hardest\b', '伪深沉', '用 is most affected'),
    (r'\bturns on\b(?!\s+(the |a )?(light|switch|device|machine|TV|computer))', '伪深沉', '用 depends on/comes down to'),
    (r'\breaching for\b', '伪深沉', '用 wants/tries for/goes for'),
    (r'\blives\b(?=\s+(in|at|somewhere|between))', '伪深沉', '用 is/happens/shows up'),
    (r'\bhold(ing)?\b(?=\s+(a |the |two |this |that )?(thought|tension|idea|line|both))', '伪深沉', '用 believing both/keeping'),
    (r'\bcarry (this|that|it) with\b', '伪深沉', '用 remember/keep in mind'),

    # 企业黑话
    (r'\bleverage\b', '企业黑话', '用 use'),
    (r'\blean(ing)? into\b', '企业黑话', '用 embrace/try'),
    (r'\bdouble-click(ing)?\s+on\b', '企业黑话', '用 look closer at'),
    (r'\bunpack\b', '企业黑话', '用 explain/break down'),
    (r'\brobust\b', '企业黑话', '用 strong/solid/reliable'),
    (r'\bseamless(ly)?\b', '企业黑话', '用 smooth/easy'),
    (r'\bcomprehensive\b', '企业黑话', '用 complete/thorough'),
    (r'\bholistic\b', '企业黑话', '用 whole/complete'),
    (r'\bnavigate\b(?=\s+(the|this|that|a|an|complex|changing))', '企业黑话', '用 handle/deal with/work through'),
    (r'\bharness\b', '企业黑话', '用 use'),
    (r'\bfoster\b', '企业黑话', '用 support/help/encourage'),
    (r'\bparadigm shift\b', '企业黑话', '用具体描述变了什么'),
    (r'\blessons learned\b', '企业黑话', '用 takeaways/what we found'),
    (r'\bnorth star\b', '企业黑话', '用 goal/guide'),
    (r'\bpressure-test\b', '企业黑话', '用 test/challenge/stress-test'),
    (r'\bstrategic imperative\b', '企业黑话', '删掉，说具体要做什么'),

    # 虚假强调
    (r'\bthe (whole|entire) (game|point|story|lesson|job|thing|ballgame)\b', '虚假强调', '说具体影响，别用绝对化'),
    (r'\bthe only thing that (matters|changed|happened)\b', '虚假强调', '去掉 only，说具体'),
    (r'\bmost people\b', '虚构观察', '有数据就引数据，没有就别说'),
    (r"\bI can't stop thinking about\b", '虚假亲密', '直接说想法'),
    (r'\bhit a nerve\b', '虚假亲密', '说具体什么反应'),
    (r'\bstruck a chord\b', '虚假亲密', '说具体什么反应'),
    (r'\bstayed with me\b', '虚假亲密', '说具体什么印象'),
    (r'\bstuck with me\b', '虚假亲密', '说具体什么印象'),

    # 空洞价值宣告
    (r"\b(it's |it is )?worth (noting|mentioning|asking|exploring|examining|considering|making|drawing)\b", '空洞宣告', '删掉，直接说内容'),
    (r'\bthis matters\b', '空洞宣告', '删掉，让内容自己说话'),
    (r'\bbecause it matters\b', '空洞宣告', '删掉'),
    (r"\bhere'?s where it gets interesting\b", '空洞宣告', '删掉，直接说'),
    (r'\bthe (most )?interesting (part|thing|bit)\b', '空洞宣告', '删掉修饰，直接说内容'),
    (r'\bthe right (time|question|way|answer|tool)\b', '空洞宣告', '考虑是否真的需要这个判断'),
    (r'\bthe point is\b', '空洞宣告', '删掉，直接说 point'),

    # 陈词滥调
    (r'\bat the end of the day\b', '陈词滥调', '删掉'),
    (r'\bshed light on\b', '陈词滥调', '用 explain/show/reveal'),
    (r'\bpave the way\b', '陈词滥调', '用 enable/make possible'),
    (r'\bpivotal\b', '陈词滥调', '用 key/important/critical'),
    (r'\btransformative\b', '陈词滥调', '用具体描述变了什么'),
    (r'\bgame.?changing\b', '陈词滥调', '用具体描述'),
    (r'\bgroundbreaking\b', '陈词滥调', '用 new/first/novel'),
    (r'\bcutting.?edge\b', '陈词滥调', '用 new/latest/advanced'),
    (r'\bdelve\b', '陈词滥调', '用 look at/examine/explore'),
    (r'\bdive into\b', '陈词滥调', '用 look at/explore'),
    (r'\btestament to\b', '陈词滥调', '用 shows/proves/demonstrates'),
    (r'\brealm\b', '陈词滥调', '用 area/field/domain'),
    (r'\blandscape\b(?=\s+(of|is|has|where))', '陈词滥调', '用 field/market/situation'),

    # 过度戏剧化
    (r'\bquietly\b(?=\s+(shift|remove|drop|erode|change|refuse|move))', '过度戏剧化', '删掉或说具体发生了什么'),
    (r"\bwe'?ve seen this movie before\b", '过度戏剧化', '说具体先例'),

    # 伪科学比喻
    (r'\b(different |the )?physics (of|here)\b', '伪科学', '用 how it works/the conditions'),
    (r'\bcompound(s|ing)?\b(?=\s+(over|into|with))', '伪科学', '用 builds/adds up/grows'),

    # 中文版常见AI味（额外）
    (r'值得一提的是', '空洞宣告(中)', '删掉，直接说'),
    (r'不可否认', '空洞宣告(中)', '考虑是否必要'),
    (r'毋庸置疑', '空洞宣告(中)', '删掉'),
    (r'众所周知', '空洞宣告(中)', '删掉或给出处'),
    (r'从某种程度上来?说', '模糊限定(中)', '说具体什么程度'),
    (r'在当今.*时代', '宏大开场(中)', '删掉，直接入题'),
    (r'随着.*的(快速|不断|迅速)(发展|演进|推进)', '宏大开场(中)', '删掉，直接说变化'),
    (r'总而言之', '套话(中)', '考虑是否需要总结'),
    (r'综上所述', '套话(中)', '考虑是否需要总结'),
    (r'一言以蔽之', '套话(中)', '直接说结论'),
]

# === 结构级检测 ===
STRUCTURE_PATTERNS = [
    (r"(it'?s|this is) not (just |only |merely )?(about )?\w+[,.]?\s*(it'?s|this is) (about |really )", '负面平行结构(一眼AI)', '重写：直接说 Y 是什么，不要先否定 X'),
    (r'\bNot only\b.*\bbut (also )?\b', '负面平行结构', '考虑拆成两句或直接说'),
    (r'^No \w+\.\s*No \w+\.\s*(Just|Only) ', '断句否定式', '直接说你要表达的'),
    (r"^(Let'?s|Let us) (explore|dive|break|look|turn|examine|unpack)", '路标过渡', '删掉，直接开始内容'),
    (r'^(Now |So )(let\'?s |we\'ll )(turn|move|look|shift)', '路标过渡', '删掉'),
    (r'^In today\'?s (rapidly )?(evolving|changing|fast-moving|dynamic)', '宏大开场', '删掉，直接入题'),
    (r'—', 'Em dash', '用 - (空格短横空格) 代替'),
    (r"^(Here'?s|Here is) (where|the (thing|part|moment|analogy|question))", '讲台式宣告', '删掉，直接说内容'),
    (r'\bGreat question\b', '开场马屁', '删掉，直接回答'),
    (r"\b(I'?d be |I would be |I'?m )happy to help\b", '开场马屁', '删掉，直接回答'),
    (r'^Absolutely[.!]', '开场马屁', '删掉，直接回答'),
]


def scan_text(text: str, filename: str = "input") -> list:
    """Scan text and return list of findings."""
    findings = []
    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        # Skip code blocks
        if line.strip().startswith('```'):
            continue

        # Vocab patterns
        for pattern, category, suggestion in VOCAB_PATTERNS:
            matches = list(re.finditer(pattern, line, re.IGNORECASE))
            for m in matches:
                findings.append({
                    'file': filename,
                    'line': i,
                    'col': m.start() + 1,
                    'match': m.group(),
                    'category': category,
                    'suggestion': suggestion,
                    'context': line.strip()[:120]
                })

        # Structure patterns
        for pattern, category, suggestion in STRUCTURE_PATTERNS:
            matches = list(re.finditer(pattern, line, re.IGNORECASE))
            for m in matches:
                findings.append({
                    'file': filename,
                    'line': i,
                    'col': m.start() + 1,
                    'match': m.group(),
                    'category': f'[结构] {category}',
                    'suggestion': suggestion,
                    'context': line.strip()[:120]
                })

    return findings


def format_findings(findings: list, output_format: str = "text") -> str:
    """Format findings for output."""
    if not findings:
        return "✅ 没有检测到 AI 写作痕迹。干净！"

    if output_format == "json":
        return json.dumps(findings, ensure_ascii=False, indent=2)

    # Group by category
    by_category = {}
    for f in findings:
        cat = f['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f)

    lines = []
    lines.append(f"⚠️ 检测到 {len(findings)} 处 AI 写作痕迹\n")

    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        lines.append(f"### {cat} ({len(items)}处)")
        for item in items[:10]:  # Max 10 per category
            lines.append(f"  L{item['line']}: \"{item['match']}\" → {item['suggestion']}")
            lines.append(f"        {item['context']}")
        if len(items) > 10:
            lines.append(f"  ... 还有 {len(items)-10} 处")
        lines.append("")

    # Summary
    lines.append("---")
    lines.append(f"总计: {len(findings)} 处 | 分类: {len(by_category)} 类")
    top_cats = sorted(by_category.items(), key=lambda x: -len(x[1]))[:3]
    lines.append(f"重灾区: {', '.join(f'{c}({len(i)})' for c,i in top_cats)}")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scan_claudisms.py <file> [--json]")
        print("      cat text.md | python3 scan_claudisms.py -")
        sys.exit(1)

    output_format = "json" if "--json" in sys.argv else "text"
    filepath = sys.argv[1]

    if filepath == "-":
        text = sys.stdin.read()
        filename = "stdin"
    else:
        path = Path(filepath)
        if not path.exists():
            print(f"❌ 文件不存在: {filepath}")
            sys.exit(1)
        text = path.read_text(encoding='utf-8')
        filename = path.name

    findings = scan_text(text, filename)
    print(format_findings(findings, output_format))


if __name__ == "__main__":
    main()
