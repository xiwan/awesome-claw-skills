#!/usr/bin/env python3
"""
image-gen: AI 图片生成
支持豆包 Seedream (火山方舟) + Pollinations (免费备选)

Usage:
    generate.sh "prompt" [options]

Options:
    --model MODEL        seedream-5.0|4.5|4.0|3.0 (default: seedream-4.5)
    --size SIZE          1K|2K|4K|WxH (default: 2K)
    --source SOURCE      ark|pollinations (default: ark)
    --image URL          参考图 URL（图生图，可多次指定）
    --sequential         组图模式
    --max-images N       组图数量 (default: 3)
    --output PATH        输出文件路径
    --watermark          添加水印
    --n N                生成数量 (default: 1)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import subprocess
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SECRETS_DIR = SCRIPT_DIR / ".." / ".." / ".." / "secrets"
OUTPUT_DIR = Path.home() / "clawd" / "output" / "images"

ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

MODEL_MAP = {
    "seedream-5.0": "doubao-seedream-5-0-260128",
    "seedream-4.5": "doubao-seedream-4-5-251128",
    "seedream-4.0": "doubao-seedream-4-0-250828",
    "seedream-3.0": "doubao-seedream-3-0-t2i-250415",
    "5.0": "doubao-seedream-5-0-260128",
    "4.5": "doubao-seedream-4-5-251128",
    "4.0": "doubao-seedream-4-0-250828",
    "3.0": "doubao-seedream-3-0-t2i-250415",
}

def load_api_key():
    env_file = SECRETS_DIR / "volcengine.env"
    if env_file.exists():
        for line in env_file.read_text().strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()
    return os.environ.get("ARK_API_KEY", "")

def make_slug(prompt, max_len=30):
    """Generate safe filename slug from prompt."""
    import re
    slug = re.sub(r'[^\w\u4e00-\u9fff]+', '_', prompt)[:max_len]
    slug = slug.strip('_')
    return slug or "image"

def generate_pollinations(prompt, size, output_path):
    """Generate image via Pollinations (free, no key)."""
    width, height = 1024, 1024
    if size == "1K":
        width, height = 1024, 1024
    elif size == "2K":
        width, height = 2048, 2048
    elif size == "4K":
        width, height = 4096, 4096
    elif "x" in size:
        width, height = size.split("x")
        width, height = int(width), int(height)

    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"

    print(f"🎨 Generating with Pollinations (free)...", file=sys.stderr)
    print(f"   Prompt: {prompt}", file=sys.stderr)
    print(f"   Size: {width}x{height}", file=sys.stderr)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
        file_size = os.path.getsize(output_path)
        # Verify it's an image
        result = subprocess.run(["file", output_path], capture_output=True, text=True)
        if "image" in result.stdout.lower():
            print(f"✅ Image saved: {output_path} ({file_size} bytes)", file=sys.stderr)
            print(output_path)
            return True
        else:
            print(f"❌ Response is not an image: {result.stdout}", file=sys.stderr)
            os.remove(output_path)
            return False
    except Exception as e:
        print(f"❌ Failed: {e}", file=sys.stderr)
        return False

def generate_ark(prompt, model_id, size, images, sequential, max_images,
                 watermark, num_images, output_path, output_dir, timestamp, slug):
    """Generate image via 火山方舟 Seedream."""
    api_key = load_api_key()
    if not api_key:
        print("❌ ARK_API_KEY not set. Configure secrets/volcengine.env or use --source pollinations", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": model_id,
        "prompt": prompt,
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": watermark,
        "n": num_images,
    }

    if images:
        payload["image"] = images

    if sequential:
        payload["sequential_image_generation"] = "auto"
        payload["sequential_image_generation_options"] = {"max_images": max_images}

    print(f"🎨 Generating with Seedream ({model_id})...", file=sys.stderr)
    print(f"   Prompt: {prompt}", file=sys.stderr)
    print(f"   Size: {size}", file=sys.stderr)
    if images:
        print(f"   Reference images: {len(images)}", file=sys.stderr)

    # Make API call via curl for reliability
    payload_json = json.dumps(payload, ensure_ascii=False)
    
    try:
        req = urllib.request.Request(
            ARK_ENDPOINT,
            data=payload_json.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message", body)
        except:
            msg = body
        print(f"❌ API Error: {msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in data:
        print(f"❌ API Error: {data['error'].get('message', 'Unknown')}", file=sys.stderr)
        sys.exit(1)

    # Download images
    result_images = data.get("data", [])
    usage = data.get("usage", {})

    for i, img in enumerate(result_images):
        url = img.get("url", "")
        img_size = img.get("size", "?")

        if output_path and len(result_images) == 1:
            filepath = output_path
        elif output_path and len(result_images) > 1:
            base, ext = os.path.splitext(output_path)
            filepath = f"{base}_{i}{ext}"
        else:
            suffix = f"_{i}" if len(result_images) > 1 else ""
            filepath = f"{output_dir}/{timestamp}_{slug}{suffix}.jpg"

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        urllib.request.urlretrieve(url, filepath)
        file_size = os.path.getsize(filepath)

        print(f"✅ [{i+1}/{len(result_images)}] {filepath} ({img_size}, {file_size} bytes)", file=sys.stderr)
        print(filepath)

    gen = usage.get("generated_images", "?")
    tokens = usage.get("total_tokens", "?")
    print(f"📊 Generated: {gen} image(s), tokens: {tokens}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="AI Image Generation")
    parser.add_argument("prompt", help="Image description / prompt")
    parser.add_argument("--model", default="5.0", help="Model name (default: 5.0)")
    parser.add_argument("--size", default="2K", help="Image size: 1K|2K|4K|WxH (default: 2K)")
    parser.add_argument("--source", default="ark", choices=["ark", "pollinations"], help="Image source")
    parser.add_argument("--image", action="append", default=[], help="Reference image URL (repeatable)")
    parser.add_argument("--sequential", action="store_true", help="Sequential image generation")
    parser.add_argument("--max-images", type=int, default=3, help="Max images for sequential mode")
    parser.add_argument("--output", default="", help="Output file path")
    parser.add_argument("--watermark", action="store_true", help="Add watermark")
    parser.add_argument("--n", type=int, default=1, help="Number of images to generate")

    args = parser.parse_args()

    # Resolve model ID
    model_id = MODEL_MAP.get(args.model, args.model)

    # Prepare output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = make_slug(args.prompt)

    output_path = args.output
    if not output_path and args.source == "pollinations":
        output_path = str(OUTPUT_DIR / f"{timestamp}_{slug}.jpg")

    if args.source == "pollinations":
        generate_pollinations(args.prompt, args.size, output_path)
    else:
        generate_ark(
            prompt=args.prompt,
            model_id=model_id,
            size=args.size,
            images=args.image,
            sequential=args.sequential,
            max_images=args.max_images,
            watermark=args.watermark,
            num_images=args.n,
            output_path=output_path,
            output_dir=str(OUTPUT_DIR),
            timestamp=timestamp,
            slug=slug,
        )

if __name__ == "__main__":
    main()
