---
name: yue2-music
description: Generate, cover, transcribe, and edit songs with YuE2 and SheetSage2/MERT2. Use for YuE2 full/melody/off generation, audio-to-ABC covers, style or lyric changes, score editing, agentic reharmonization, melody preservation, singable lyric adaptation, and reproducible listening comparisons; also for YuE2 生成、翻唱、改编、改谱、换词和智能体编辑.
triggers:
  - "yue2"
  - "生成音乐"
  - "写一首歌"
  - "本地生成音乐"
  - "翻唱"
  - "改编这首歌"
  - "改谱"
  - "换词"
  - "reharmonize"
---

# YuE2 Music

Turn a musical request into a reproducible song and an audible comparison. Use released
model interfaces. Retain an original song and its plan before making changes.

## Choose the workflow

| Request | Workflow |
| --- | --- |
| Generate with editable melody and harmony | YuE2 `cot="full"` → ABC → song |
| Generate with a melody plan and free accompaniment | YuE2 `cot="melody"` → chord-free ABC → song |
| Generate without symbolic planning | YuE2 `cot="off"` → song; no editable ABC |
| Cover a recording | SheetSage2 → inspect/correct ABC → strip chords → YuE2 `melody` |
| Cover an ABC melody | Inspect/convert native ABC → strip chords → YuE2 `melody` |
| Change harmony, instruments, tempo, structure, or lyrics | Copy full plan → edit ABC/text → regenerate |
| Agentic editing | Export plan/baseline → bounded editing agent → check invariants → render → compare |
| Analyze musical features | Use MERT2 only when continuous features are needed |

```text
audio → SheetSage2 [loads MERT-v2-FullSong itself] → ABC
style + lyrics → YuE2 full/melody planning        → ABC
                                                  edit/validate
style + lyrics + ABC → YuE2 semantic generation → synthesis → latents → VAE → song
style + lyrics      → YuE2 off generation      → synthesis → latents → VAE → song
```

Do not feed public MERT feature tensors to YuE2 as codec tokens. YuE2 exposes no
audio-reference, phoneme-alignment, or local-inpainting argument.

## Set up the needed models

> **打包说明（非上游内容）.** 本目录是上游 skill 的转载，额外补了「怎么在一台远端 GPU
> 机器上跑」这一层——因为 YuE2 需要 CUDA，笔记本（尤其 Apple Silicon）跑不了，上游helper
> 默认在本机执行。新增文件：`scripts/remote.sh`、`references/deploy-aws.md`、
> `yue2.env.example`、`.gitignore`。上游文件未作改动。详见文末「本转载版的改动」。
>
> **如果 YuE2 就装在 agent 所在的机器上**，忽略这一层，直接用下面的 `scripts/*.py`。
> **否则**先读 [deploy-aws.md](references/deploy-aws.md) 建后端，把 `yue2.env.example`
> 填好放到 `secrets/yue2.env`，然后：
>
> ```bash
> scripts/remote.sh status                        # 实例状态 / GPU / 磁盘
> scripts/remote.sh start                         # 唤醒（省 GPU 费用用完即停）
> scripts/remote.sh generate request.json pop     # 推请求 → 生成 → 轮询等待
> scripts/remote.sh generate jazz.json jazz jazz.abc   # 带编辑过的乐谱
> scripts/remote.sh run 'python scripts/abc_tools.py compare a.abc b.abc'
> scripts/remote.sh listen pop jazz               # 对比页并拉回本地
> scripts/remote.sh stop                          # 停机
> ```
>
> 走 SSM，无需 SSH、无需开入站端口。产物经 S3 回传（音频装不进 SSM 命令输出）。

Read [models-and-setup.md](references/models-and-setup.md). Install the YuE2 runtime
from the official GitHub repository source. Use a separate environment
for SheetSage2 because dependency pins differ. Download the public model snapshots and
record their revisions. This skill's original instructions, helpers, and templates are
licensed under [Apache 2.0](LICENSE). Copyright (c) 2026 the YuE2 authors.
Model weights and third-party dependencies retain their applicable licenses.

Use the supported baseline: one request at a time, BF16-capable NVIDIA GPU with 24 GB
VRAM, default YuE2 settings. Do not silently shorten a requested song or lower inference
settings to hide an OOM. Free allocations or choose suitable hardware; report changes.

Use `YuE2-Vae` for listening and `YuE2-Vae-legacy` when reproducing the supplied benchmark
protocol. Keep decoded files separate. Do not infer their roles from the word “legacy.”

Run helper paths below relative to this skill folder, with the appropriate environment's
Python. Select snapshots using `--model`, `--revision`, and `--vae-revision`, or local
model directories plus `--offline`. Use fresh output directories.

## Generate and retain the plan

Start with [assets/prompt.json](assets/prompt.json), an original example. Put genre,
instruments, vocal character, language and intended tempo in `style`; put section tags
and actual words in `lyrics`. Keep implementation notes out of lyrics.

```bash
python scripts/run_yue2.py generate --request assets/prompt.json --output outputs/pop
python scripts/run_yue2.py all-modes --request assets/prompt.json --output outputs/modes
python scripts/run_yue2.py plan --request assets/prompt.json --output outputs/plan
```

Inspect `result.json`, truncation, `score.abc`, `request.json`, and audio. Keep exact
tokens and `latent.npy`; the helper saves native artifacts. Preserve all requested modes
and failures. A successful process or playable file does not establish musical quality.

Read [generation-and-covers.md](references/generation-and-covers.md) for Python, CLI,
exact plan continuation, CFG, sampling, and cached decoding. Load unchanged plans with
`SymbolicPlan.load`; submit modified ABC as a new input. CLI `--resume` verifies a
completed result; it does not continue interrupted generation.

## Cover a recording

1. Transcribe in the SheetSage2 environment. Select the vocal melody or the full lead
   melody, including instrumental passages.
2. Inspect warnings and correct missed notes, meter or key before attributing errors
   to YuE2. Preserve source audio and raw transcription.
3. Export chord-free ABC. Select a retained voice explicitly when dropping a part;
   removing chords alone should preserve both melodic voices and their rests.
4. Render with `cot="melody"`, target style and suitable lyrics. This supplies a symbolic
   melody condition; it does not preserve the source singer's identity or waveform.

```bash
# SheetSage2 environment.
python scripts/transcribe.py reference.wav --task melody-full --output outputs/transcription
python scripts/abc_tools.py strip-chords outputs/transcription/score.abc outputs/cover.abc

# YuE2 environment; the request supplies target style and lyrics.
python scripts/run_yue2.py generate --request assets/prompt.json --cot melody \
  --abc-file outputs/cover.abc --output outputs/cover-song
```

`cot="melody"` does not remove chord symbols automatically. To retain the original
harmony as well, use full transcription and `cot="full"`; call this score-conditioned
regeneration with melody and harmony.

## Edit or delegate an edit

Read [editing-workflows.md](references/editing-workflows.md) and
[abc-editing.md](references/abc-editing.md) before changing a score.

1. Render a baseline from the full plan. Freeze its original directory.
2. Define invariants: exact pitches; pitch plus rhythm; contour only; or bounded melodic
   adaptation. Specify voices/passages, lyrics, instruments, tempo, meter and structure.
3. If delegation is available, give a score-editing agent raw ABC, prompt, lyrics, the
   requested change and the [edit brief](assets/edit-brief.md). Request a new ABC,
   revised style/lyrics as needed, and an edit manifest. Give a separate reviewer the
   before/after artifacts and constraints. Without delegation, perform these stages
   yourself. Keep model generation sequential per GPU.
4. Check musical events, not character strings: ties, accidentals and compressed rests
   matter. Run:

   ```bash
   python scripts/abc_tools.py inspect edits/jazz.abc
   python scripts/abc_tools.py compare outputs/plan/score.abc edits/jazz.abc --voices Vocal
   python scripts/run_yue2.py generate --request edits/jazz.json --cot full \
     --abc-file edits/jazz.abc --output outputs/jazz
   ```

   Add `--allow-tempo-change` for intentional tempo changes. Exact comparison should
   fail for intentional rhythm changes; audit permitted differences from its report
   instead of relabeling the result “melody preserved.”
   Keep the edited score connected through `--abc-file` or request `abc_path`;
   omitting both with `abc: null` generates a fresh plan and discards the edit.
5. Regenerate after changing style, lyrics or ABC. Old acoustic latents can be decoded
   again, but cannot implement a musical or lyric edit.
6. Compare full songs and short passages around the edit. Revise when the requested
   effect fails; retain each attempt and its actual prompt.

For lyric translation, adapt syllables, stress, vowels and breath points. Keep a
syllable/phoneme-to-note sidecar. Do not invent a `phonemes` field or mistake the sidecar
for hard acoustic alignment. Use ASR/PER and listening as separate evidence.

## Deliver an audible result

Read [listening-and-evaluation.md](references/listening-and-evaluation.md). Return playable
audio, full prompt/lyrics, before/after ABC, invariant checks and requested evaluations.
Keep model/decoder identity and failures visible.

```bash
python scripts/listen.py outputs/pop outputs/jazz --output outputs/comparison
```

This creates a local HTML player, copies audio, and includes the exact requests. It does
not publish or upload. Distinguish symbolic checks, ASR, listening and quality scores.
Deliver custom edit manifests and before/after comparison reports alongside the page;
the player copies a fixed set of native artifacts, not arbitrary sidecars.
Do not claim exact note realization, instrument removal or sample-accurate preservation
from an ABC check or SongBench score alone.

---

## 来源与许可

本 skill 转载自 YuE2 官方仓库 [`multimodal-art-projection/YuE`](https://github.com/multimodal-art-projection/YuE)
的 `skills/yue2-music/`。

- 上游指令、helper 与模板：**Apache License 2.0**，见 [LICENSE](LICENSE)。
  Copyright (c) 2026 the YuE2 authors。
- **模型权重另有许可（CC BY-NC 4.0，即禁止商用）**，随权重仓库分发，不受本目录的
  Apache 2.0 覆盖。商用前务必自行确认。
- 第三方依赖保留各自许可。

### 本转载版的改动

上游的 12 个文件（`SKILL.md`、`references/` 5 篇、`scripts/` 5 个、`assets/`、`agents/`）
逐字保留，**仅在 `SKILL.md` 中新增两处**：YAML frontmatter 里加了本仓库约定的 `triggers`
字段，以及顶部的「打包说明」引用块和文末本节。

新增的四个文件均非上游内容：

| 文件 | 作用 |
|------|------|
| `scripts/remote.sh` | 经 AWS SSM 在远端 GPU 机器上执行上游脚本，产物经 S3 回传 |
| `references/deploy-aws.md` | 后端部署笔记：显存实测、容量策略、bootstrap、最小权限 |
| `yue2.env.example` | 配置模板（占位符），真实配置放 `secrets/yue2.env` |
| `.gitignore` | 防止提交 `secrets/`、`*.env`、输出目录 |

脚本内**不含任何硬编码的账号 ID、实例 ID、主机名、桶名或密钥**，全部来自
自动发现的 `yue2.env`。
