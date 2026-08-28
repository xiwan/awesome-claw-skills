#!/usr/bin/env python3
"""
ComfyUI text-to-image CLI.

Talks to any ComfyUI instance over its HTTP API — local, behind a reverse
proxy, or on a cloud GPU box. No browser, no ComfyUI web UI needed.

Only uses the Python standard library.

Configuration is read from (in order of precedence):
  1. Command-line flags
  2. Environment variables
  3. <clawd_root>/secrets/comfyui.env

Required:
  COMFY_HOST          e.g. http://localhost:8188  or  https://comfy.example.com

Optional:
  COMFY_API_KEY       Sent as an auth header if your endpoint requires one
  COMFY_AUTH_HEADER   Header name for the key (default: X-Comfy-Key)
  COMFY_OUT           Output directory (default: ~/clawd/output/images)
  COMFY_INSTANCE_ID   EC2 instance id, enables --wake / friendlier errors
  COMFY_AWS_REGION    AWS region for the above (default: us-east-1)

See references/api.md for the raw HTTP API and how to add your own workflow.
"""
import argparse
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SECRETS_DIR = SCRIPT_DIR / ".." / ".." / ".." / "secrets"
DEFAULT_OUT = pathlib.Path.home() / "clawd" / "output" / "images"

# ── Workflow presets ────────────────────────────────────────────────
# Each preset lists the model files it needs and how to build the graph.
# "probe" maps a ComfyUI model folder -> filename the preset expects.
# Auto-selection picks the first preset whose files all exist on the server.
PRESETS = {
    "z-image-turbo": {
        "label": "Z-Image Turbo 6B",
        "steps": 8,
        "aliases": ["turbo", "zimage", "z-image"],
        "probe": {
            "diffusion_models": "z_image_turbo_bf16.safetensors",
            "text_encoders": "qwen_3_4b.safetensors",
            "vae": "ae.safetensors",
        },
        "builder": "unet_clip_vae",
        "sampler": "res_multistep",
        "clip_type": "lumina2",
        "shift": 3.0,
        "latent": "EmptySD3LatentImage",
    },
    "flux-schnell": {
        "label": "FLUX.1 schnell (fp8)",
        "steps": 4,
        "aliases": ["schnell", "flux-s"],
        "probe": {"checkpoints": "flux1-schnell-fp8.safetensors"},
        "builder": "checkpoint",
        "sampler": "euler",
        "latent": "EmptyLatentImage",
        "guidance": None,
    },
    "flux-dev": {
        "label": "FLUX.1 dev (fp8)",
        "steps": 20,
        "aliases": ["dev", "flux-d"],
        "probe": {"checkpoints": "flux1-dev-fp8.safetensors"},
        "builder": "checkpoint",
        "sampler": "euler",
        "latent": "EmptyLatentImage",
        "guidance": 3.5,
    },
    "sd-checkpoint": {
        "label": "Generic SD/SDXL checkpoint",
        "steps": 25,
        "aliases": ["sd", "sdxl", "generic"],
        "probe": {},  # matched only when --ckpt is given explicitly
        "builder": "checkpoint",
        "sampler": "euler",
        "latent": "EmptyLatentImage",
        "guidance": None,
        "cfg": 7.0,
    },
}


def resolve_preset(name):
    if name in PRESETS:
        return name
    for key, spec in PRESETS.items():
        if name in spec.get("aliases", []):
            return key
    return None


# ── Config ──────────────────────────────────────────────────────────
def load_env_file():
    """Load secrets/comfyui.env into os.environ without clobbering real env."""
    env_file = (SECRETS_DIR / "comfyui.env").resolve()
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def die(msg, hint=None):
    print(f"\nerror: {msg}", file=sys.stderr)
    if hint:
        print(hint, file=sys.stderr)
    sys.exit(1)


# ── HTTP ────────────────────────────────────────────────────────────
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Surface 3xx as HTTPError instead of following it.

    Auth proxies (ALB + Cognito, oauth2-proxy, ...) answer unauthenticated
    API calls with a 302 to a login page. If we followed it we would get a
    200 full of HTML and fail later with a confusing JSON parse error.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, host, key, header):
        self.host = host.rstrip("/")
        self.key = key
        self.header = header
        self._opener = urllib.request.build_opener(_NoRedirect)

    def _headers(self):
        return {self.header: self.key} if self.key else {}

    def _auth_hint(self):
        sending = f"{self.header}: {'<set>' if self.key else '<empty>'}"
        return ("The endpoint wants credentials, or the key is wrong.\n"
                f"  currently sending: {sending}\n"
                "  set COMFY_API_KEY, and COMFY_AUTH_HEADER if the header is "
                "not X-Comfy-Key.")

    def call(self, path, payload=None, timeout=180, raw=False, allow_404=False):
        headers = self._headers()
        data = None
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.host + path, data=data, headers=headers)
        try:
            with self._opener.open(req, timeout=timeout) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code == 404 and allow_404:
                return None
            if e.code in (301, 302, 303, 307, 308):
                die(f"HTTP {e.code} on {path} — redirected to "
                    f"{e.headers.get('Location', '?')[:80]}", self._auth_hint())
            if e.code in (401, 403):
                die(f"HTTP {e.code} on {path} — access denied.", self._auth_hint())
            detail = e.read()[:300].decode(errors="replace")
            die(f"HTTP {e.code} on {path}\n{detail}")
        except urllib.error.URLError as e:
            die(f"cannot reach {self.host} ({e.reason})", wake_hint())

        if raw:
            return body
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            if b"<html" in body[:400].lower():
                die(f"{path} returned HTML instead of JSON.",
                    "Usually an auth layer serving a login page.\n"
                    + self._auth_hint())
            die(f"{path} returned unparseable response "
                f"(Content-Type: {ctype or 'unknown'})")

    def models(self, folder):
        """List models in a folder. Tolerates folders this build doesn't know."""
        return self.call(f"/api/models/{folder}", timeout=30, allow_404=True) or []

    def reachable(self, timeout=10):
        try:
            req = urllib.request.Request(self.host + "/api/system_stats",
                                         headers=self._headers())
            with self._opener.open(req, timeout=timeout):
                return True
        except Exception:
            return False


def wake_hint():
    iid = os.environ.get("COMFY_INSTANCE_ID")
    region = os.environ.get("COMFY_AWS_REGION", "us-east-1")
    if iid:
        return ("The backend may be stopped. Start it with:\n"
                f"  aws ec2 start-instances --region {region} --instance-ids {iid}\n"
                "  (or re-run this command with --wake)\n"
                "Service is usually ready ~1 minute after boot.")
    return ("Check that COMFY_HOST is correct and the ComfyUI server is running.\n"
            "If it runs on EC2, set COMFY_INSTANCE_ID to enable --wake.")


def wake_instance(client, timeout=300):
    iid = os.environ.get("COMFY_INSTANCE_ID")
    if not iid:
        die("--wake needs COMFY_INSTANCE_ID to be set.")
    if not shutil.which("aws"):
        die("--wake needs the AWS CLI on PATH.")
    region = os.environ.get("COMFY_AWS_REGION", "us-east-1")
    print(f"starting instance {iid} in {region} ...")
    subprocess.run(["aws", "ec2", "start-instances", "--region", region,
                    "--instance-ids", iid],
                   check=False, stdout=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if client.reachable():
            print(f"backend ready after {time.time()-t0:.0f}s\n")
            return
        print(f"\r  waiting for backend ... {time.time()-t0:>4.0f}s",
              end="", flush=True)
        time.sleep(10)
    print()
    die(f"instance did not become ready within {timeout}s")


# ── Graph builders ──────────────────────────────────────────────────
def build_graph(spec, prompt, negative, w, h, steps, seed, cfg, files):
    """Return a ComfyUI API-format prompt graph."""
    sampler = spec["sampler"]
    latent_node = spec["latent"]
    save = {"class_type": "SaveImage",
            "inputs": {"filename_prefix": "txt2img", "images": ["dec", 0]}}

    if spec["builder"] == "unet_clip_vae":
        g = {
            "unet": {"class_type": "UNETLoader",
                     "inputs": {"unet_name": files["diffusion_models"],
                                "weight_dtype": "default"}},
            "clip": {"class_type": "CLIPLoader",
                     "inputs": {"clip_name": files["text_encoders"],
                                "type": spec["clip_type"], "device": "default"}},
            "shift": {"class_type": "ModelSamplingAuraFlow",
                      "inputs": {"shift": spec["shift"], "model": ["unet", 0]}},
            "vae": {"class_type": "VAELoader",
                    "inputs": {"vae_name": files["vae"]}},
            "pos": {"class_type": "CLIPTextEncode",
                    "inputs": {"text": prompt, "clip": ["clip", 0]}},
            "neg": {"class_type": "CLIPTextEncode",
                    "inputs": {"text": negative, "clip": ["clip", 0]}},
            "lat": {"class_type": latent_node,
                    "inputs": {"width": w, "height": h, "batch_size": 1}},
            "ks": {"class_type": "KSampler",
                   "inputs": {"seed": seed, "steps": steps, "cfg": cfg,
                              "sampler_name": sampler, "scheduler": "simple",
                              "denoise": 1.0, "model": ["shift", 0],
                              "positive": ["pos", 0], "negative": ["neg", 0],
                              "latent_image": ["lat", 0]}},
            "dec": {"class_type": "VAEDecode",
                    "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}},
            "save": save,
        }
        return g

    # checkpoint builder: all-in-one file provides MODEL / CLIP / VAE
    g = {
        "ckpt": {"class_type": "CheckpointLoaderSimple",
                 "inputs": {"ckpt_name": files["checkpoints"]}},
        "pos": {"class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["ckpt", 1]}},
        "neg": {"class_type": "CLIPTextEncode",
                "inputs": {"text": negative, "clip": ["ckpt", 1]}},
        "lat": {"class_type": latent_node,
                "inputs": {"width": w, "height": h, "batch_size": 1}},
        "ks": {"class_type": "KSampler",
               "inputs": {"seed": seed, "steps": steps, "cfg": cfg,
                          "sampler_name": sampler, "scheduler": "simple",
                          "denoise": 1.0, "model": ["ckpt", 0],
                          "positive": ["pos", 0], "negative": ["neg", 0],
                          "latent_image": ["lat", 0]}},
        "dec": {"class_type": "VAEDecode",
                "inputs": {"samples": ["ks", 0], "vae": ["ckpt", 2]}},
        "save": save,
    }
    if spec.get("guidance") is not None:
        g["guide"] = {"class_type": "FluxGuidance",
                      "inputs": {"guidance": spec["guidance"],
                                 "conditioning": ["pos", 0]}}
        g["ks"]["inputs"]["positive"] = ["guide", 0]
    return g


# ── Helpers ─────────────────────────────────────────────────────────
def parse_size(s):
    parts = [p for p in re.split(r"[x*×,\s]+", str(s).strip().lower()) if p]
    try:
        if len(parts) == 1:
            w = h = int(parts[0])
        elif len(parts) == 2:
            w, h = int(parts[0]), int(parts[1])
        else:
            raise ValueError
    except ValueError:
        die(f"cannot parse size {s!r}", "examples: 1024   1280x720")
    if not (256 <= w <= 4096 and 256 <= h <= 4096):
        die(f"size {w}x{h} out of range", "width and height must be 256-4096")
    align = lambda v: max(256, round(v / 16) * 16)  # noqa: E731
    aw, ah = align(w), align(h)
    if (aw, ah) != (w, h):
        print(f"note: {w}x{h} aligned to {aw}x{ah} (models need multiples of 16)")
    return aw, ah


def slug(text, n=40):
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:n].rstrip("-") or "image"


def pick_preset(client, requested, ckpt_override):
    """Resolve which preset to use, validating against server-side models."""
    if ckpt_override:
        key = resolve_preset(requested) if requested else "sd-checkpoint"
        key = key or "sd-checkpoint"
        spec = dict(PRESETS[key])
        return key, spec, {"checkpoints": ckpt_override}

    if requested:
        key = resolve_preset(requested)
        if not key:
            die(f"unknown model {requested!r}",
                "available: " + ", ".join(PRESETS) +
                "\nOr pass --ckpt <filename> for any checkpoint on the server.")
        spec = PRESETS[key]
        files = {}
        for folder, fname in spec["probe"].items():
            have = client.models(folder)
            if fname not in have:
                die(f"preset {key!r} needs {folder}/{fname} but the server "
                    f"does not have it.",
                    f"Server has in {folder}: {have or '(none)'}\n"
                    "Use --list-models to see everything, or --ckpt to point at "
                    "a file you do have.")
            files[folder] = fname
        return key, spec, files

    # auto: first preset whose files are all present
    cache = {}
    for key, spec in PRESETS.items():
        if not spec["probe"]:
            continue
        files, ok = {}, True
        for folder, fname in spec["probe"].items():
            if folder not in cache:
                cache[folder] = client.models(folder)
            if fname not in cache[folder]:
                ok = False
                break
            files[folder] = fname
        if ok:
            return key, spec, files

    ckpts = cache.get("checkpoints") or client.models("checkpoints")
    if ckpts:
        return ("sd-checkpoint", dict(PRESETS["sd-checkpoint"]),
                {"checkpoints": ckpts[0]})
    die("no usable model found on the server.",
        "Run with --list-models to see what is installed.")


def list_models(client):
    print(f"models on {client.host}\n")
    for folder in ("checkpoints", "diffusion_models", "text_encoders", "vae",
                   "loras"):
        items = client.models(folder)
        print(f"  {folder}:")
        for i in items:
            print(f"    {i}")
        if not items:
            print("    (none)")
    print("\npresets:")
    for key, spec in PRESETS.items():
        need = ", ".join(f"{k}/{v}" for k, v in spec["probe"].items()) or "any --ckpt"
        print(f"  {key:<16} {spec['label']:<28} needs: {need}")


# ── Generation ──────────────────────────────────────────────────────
def generate(client, args, spec, files, w, h, steps, cfg, seed, idx, total):
    tag = f"[{idx}/{total}] " if total > 1 else ""
    print(f"{tag}{spec['label']} · {w}x{h} · {steps} steps · seed {seed}")

    graph = build_graph(spec, args.prompt, args.negative, w, h, steps, seed,
                        cfg, files)
    resp = client.call("/prompt", {"prompt": graph})
    if resp.get("node_errors"):
        die("server rejected the workflow:\n" +
            json.dumps(resp["node_errors"], ensure_ascii=False, indent=2)[:1200])
    pid = resp["prompt_id"]

    t0 = time.time()
    entry = None
    while time.time() - t0 < args.timeout:
        time.sleep(2)
        hist = client.call(f"/history/{pid}", timeout=60)
        if pid in hist:
            entry = hist[pid]
            break
        print(f"\r{tag}  generating ... {time.time()-t0:>4.0f}s", end="", flush=True)
    print("\r" + " " * 46 + "\r", end="")
    if entry is None:
        die(f"timed out after {args.timeout}s waiting for the image")

    status = entry["status"]["status_str"]
    gen_s = time.time() - t0
    if status != "success":
        die(f"generation failed ({status}):\n" +
            json.dumps(entry["status"].get("messages"), ensure_ascii=False)[:1500])

    imgs = [i for o in entry.get("outputs", {}).values() for i in o.get("images", [])]
    if not imgs:
        die("generation succeeded but returned no image")
    img = imgs[0]

    q = (f"filename={urllib.parse.quote(img['filename'])}"
         f"&subfolder={urllib.parse.quote(img.get('subfolder', ''))}"
         f"&type={img['type']}")
    if args.png:
        ext = "png"
    else:
        q += f"&preview=webp;{args.quality}"
        ext = "webp"

    t1 = time.time()
    data = client.call(f"/view?{q}", timeout=900, raw=True)
    dl_s = max(time.time() - t1, 0.01)

    name = (f"{time.strftime('%Y%m%d-%H%M%S')}_{args.model or 'auto'}"
            f"_{w}x{h}_{slug(args.prompt)}.{ext}")
    path = args.dir / name
    path.write_bytes(data)

    print(f"{tag}done   gen {gen_s:.0f}s · dl {len(data)/1024:.0f}KB/{dl_s:.1f}s "
          f"({len(data)/dl_s/1024:.0f}KB/s)")
    print(f"{tag}       {path}")
    return path


# ── Main ────────────────────────────────────────────────────────────
def main():
    load_env_file()

    ap = argparse.ArgumentParser(
        prog="txt2img",
        description="Generate images from text via a ComfyUI HTTP API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Presets: " + " | ".join(
            f"{k} ({s['steps']} steps)" for k, s in PRESETS.items()))
    ap.add_argument("prompt", nargs="?", help="text prompt (omit for interactive)")
    ap.add_argument("size", nargs="?", default=None,
                    help="resolution, e.g. 1024 or 1280x720 (default 1024)")
    ap.add_argument("-m", "--model", help="preset name or alias (default: auto-detect)")
    ap.add_argument("--ckpt", help="use this checkpoint filename directly")
    ap.add_argument("-b", "--batch", type=int, default=1, help="how many images")
    ap.add_argument("-n", "--steps", type=int, help="sampling steps")
    ap.add_argument("--cfg", type=float, help="CFG scale")
    ap.add_argument("--seed", type=int, default=0, help="seed, 0 = random")
    ap.add_argument("--negative", default="", help="negative prompt")
    ap.add_argument("-d", "--dir", type=pathlib.Path, help="output directory")
    ap.add_argument("--png", action="store_true",
                    help="download lossless PNG (~10x larger and slower)")
    ap.add_argument("-q", "--quality", type=int, default=90, help="webp quality")
    ap.add_argument("--host", help="ComfyUI base URL (overrides COMFY_HOST)")
    ap.add_argument("--timeout", type=int, default=900,
                    help="seconds to wait per image (default 900)")
    ap.add_argument("--wake", action="store_true",
                    help="start the EC2 backend first (needs COMFY_INSTANCE_ID)")
    ap.add_argument("--list-models", action="store_true",
                    help="show models installed on the server, then exit")
    ap.add_argument("--no-open", action="store_true",
                    help="do not reveal the file in Finder afterwards")
    args = ap.parse_args()

    host = args.host or os.environ.get("COMFY_HOST")
    if not host:
        die("COMFY_HOST is not set.",
            "Set it in the environment, in secrets/comfyui.env, or pass --host.\n"
            "  example: COMFY_HOST=http://localhost:8188")
    client = Client(host,
                    os.environ.get("COMFY_API_KEY", ""),
                    os.environ.get("COMFY_AUTH_HEADER", "X-Comfy-Key"))

    if args.wake:
        wake_instance(client)

    if args.list_models:
        list_models(client)
        return

    if not args.prompt:
        try:
            args.prompt = input("prompt: ").strip()
            if not args.prompt:
                die("prompt cannot be empty")
            s = input("size [1024]: ").strip()
            if s:
                args.size = s
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(130)

    key, spec, files = pick_preset(client, args.model, args.ckpt)
    args.model = args.model or key
    w, h = parse_size(args.size or 1024)
    steps = args.steps or spec["steps"]
    cfg = args.cfg if args.cfg is not None else spec.get("cfg", 1.0)

    out = args.dir or pathlib.Path(os.environ.get("COMFY_OUT", DEFAULT_OUT))
    args.dir = out.expanduser()
    args.dir.mkdir(parents=True, exist_ok=True)

    print(f"prompt  {args.prompt}")
    print(f"output  {args.dir}\n")

    saved = []
    try:
        for i in range(1, args.batch + 1):
            if args.seed and args.batch == 1:
                seed = args.seed
            elif args.seed:
                seed = args.seed + i - 1
            else:
                seed = int.from_bytes(os.urandom(4), "big")
            saved.append(generate(client, args, spec, files, w, h, steps, cfg,
                                  seed, i, args.batch))
    except KeyboardInterrupt:
        print("\ninterrupted")

    if saved:
        print(f"\n{len(saved)} image(s) in {args.dir}")
        if not args.no_open and platform.system() == "Darwin":
            subprocess.run(["open", "-R", str(saved[-1])], check=False)


if __name__ == "__main__":
    main()
