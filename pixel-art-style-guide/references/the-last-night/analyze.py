#!/usr/bin/env python3
"""The Last Night 风格量化分析 / 验收脚本。

零第三方依赖（纯标准库），只读 24/32-bit 未压缩 BMP。
先把截图转成 BMP（建议等比缩放，画幅比输出才有意义）：
    macOS:  sips -s format bmp --resampleWidth 300 shot.png --out /tmp/shot.bmp
    其他:   ffmpeg -i shot.png -vf scale=300:-1 -pix_fmt bgr24 /tmp/shot.bmp

用法：
    python3 analyze.py /tmp/shot.bmp [more.bmp ...]

输出：亮度分布、平均饱和度、主导色相带、高光聚类色，
并对照 the-last-night-visual-analysis.md 的实测区间给出 PASS/WARN。
"""

import colorsys
import collections
import os
import struct
import sys

DARK_T = 0.15    # 近黑阈值
BRIGHT_T = 0.50  # 亮部阈值
HOT_T = 0.80     # 过曝阈值
HUE_BUCKET = 15  # 色相分桶宽度（度）


def read_bmp(path):
    """返回 (width, height, [(r,g,b), ...])。"""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"BM":
        raise ValueError(f"{path}: 不是 BMP 文件（先用 sips/ffmpeg 转换）")
    offset = struct.unpack_from("<I", data, 10)[0]
    width, height = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    if bpp not in (24, 32):
        raise ValueError(f"{path}: 只支持 24/32-bit BMP，实际 {bpp}-bit")
    step = bpp // 8
    stride = ((width * step) + 3) // 4 * 4
    pixels = []
    for y in range(abs(height)):
        base = offset + y * stride
        for x in range(width):
            i = base + x * step
            pixels.append((data[i + 2], data[i + 1], data[i]))
    return width, abs(height), pixels


def luminance(rgb):
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def analyze(path):
    width, height, pixels = read_bmp(path)
    total = len(pixels)

    lums = []
    sat_sum = 0.0
    hues = collections.Counter()
    highlights = collections.Counter()

    for rgb in pixels:
        lums.append(luminance(rgb))
        h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
        sat_sum += s
        if s > 0.35 and v > 0.20:
            hues[int(h * 360) // HUE_BUCKET * HUE_BUCKET] += 1
        if v > 0.75 and s > 0.30:
            highlights[(rgb[0] // 32 * 32, rgb[1] // 32 * 32, rgb[2] // 32 * 32)] += 1

    lums.sort()
    dark = sum(1 for v in lums if v < DARK_T) / total
    bright = sum(1 for v in lums if v >= BRIGHT_T) / total
    hot = sum(1 for v in lums if v >= HOT_T) / total
    mid = 1.0 - dark - bright
    median = lums[total // 2]
    mean_sat = sat_sum / total
    aspect = width / height if height else 0

    sat_px = sum(hues.values()) or 1
    ranked = hues.most_common()
    # 主导色相 = 相邻两个 15° 桶合成的 30° 带
    def band_share(start):
        return (hues.get(start, 0) + hues.get((start + HUE_BUCKET) % 360, 0)) / sat_px
    best_band = max(hues, key=band_share) if hues else 0
    dominant = band_share(best_band)
    second = 0.0
    for start in hues:
        if abs(((start - best_band + 180) % 360) - 180) >= 45:
            second = max(second, band_share(start))

    print(f"\n=== {os.path.basename(path)}  {width}x{height} ===")
    print(f"  画幅比        {aspect:.2f} : 1  （仅参考，不参与判定）")
    print(f"  近黑 <{DARK_T}    {dark:.0%}")
    print(f"  中间调        {mid:.0%}")
    print(f"  亮部 >={BRIGHT_T}   {bright:.0%}")
    print(f"  过曝 >={HOT_T}   {hot:.1%}")
    print(f"  中位亮度      {median:.3f}")
    print(f"  平均饱和度    {mean_sat:.2f}")
    print(f"  主导色相带    {best_band}-{best_band + 30}deg  占饱和像素 {dominant:.0%}")
    print(f"  次色相带      {second:.0%}")
    print("  高光聚类      " + " ".join("#%02X%02X%02X" % c for c, _ in highlights.most_common(5)))
    print("  色相分布      " + " ".join(
        f"{k}deg:{v * 100 // sat_px}%" for k, v in ranked[:5]))

    fog_mode = dark < 0.05
    # 画幅比只作参考输出，不参与判定（截图/裁图/项目自身画幅都会不同）
    checks = [
        ("过曝 <5%", hot < 0.05),
        ("主导色相 >=45%", dominant >= 0.45),
        ("次色相 <=20%", second <= 0.20),
        ("最亮聚类非白", bool(highlights)),
    ]
    if fog_mode:
        checks.append(("雾模式：饱和 <=0.30", mean_sat <= 0.30))
        checks.append(("雾模式：中位亮度 0.35-0.55", 0.35 <= median <= 0.55))
        mode = "雾抬黑场模式"
    else:
        checks.append(("深夜模式：近黑 20-80%", 0.20 <= dark <= 0.80))
        checks.append(("深夜模式：饱和 >=0.35", mean_sat >= 0.35))
        mode = "深夜/室内模式"

    print(f"  判定为「{mode}」")
    for name, ok in checks:
        print(f"    [{'PASS' if ok else 'WARN'}] {name}")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    for path in argv[1:]:
        try:
            analyze(path)
        except (OSError, ValueError) as exc:
            print(f"skip {path}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
