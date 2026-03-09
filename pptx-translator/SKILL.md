---
name: pptx-translator
description: "Translate PowerPoint (.pptx) files between languages using Amazon Translate or Bedrock LLM. Use when: (1) translating presentations to other languages, (2) localizing slide decks for international audiences, (3) converting Chinese/Japanese/Korean presentations to English or vice versa. Supports two engines: Amazon Translate (fast, cost-effective) and Bedrock LLM (context-aware, better quality for nuanced content). Preserves formatting, styles, and layout."
---

# PPTX Translator

Translate PowerPoint files using AWS services.

## Quick Start

```bash
# Amazon Translate (fast, cheap)
python scripts/translate_pptx.py input.pptx -s zh -t en

# Bedrock LLM (better quality)
python scripts/translate_pptx.py input.pptx -s zh -t en -e bedrock
```

## Engine Selection

| Use Case | Engine | Flag |
|----------|--------|------|
| Technical docs, high volume | Amazon Translate | `-e translate` (default) |
| Marketing, nuanced content | Bedrock LLM | `-e bedrock` |
| Cost-sensitive | Amazon Translate | |
| Quality-sensitive | Bedrock LLM | |

## Commands

### Translate with Amazon Translate
```bash
python scripts/translate_pptx.py input.pptx \
  --source en --target zh \
  --engine translate \
  --terminology terms.csv  # optional
```

### Translate with Bedrock LLM
```bash
python scripts/translate_pptx.py input.pptx \
  --source en --target zh \
  --engine bedrock \
  --model anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --glossary glossary.json \
  --style professional \
  --batch-size 20
```

### Extract texts for review
```bash
python scripts/extract_texts.py input.pptx -o texts.json
```

## Options

| Option | Description |
|--------|-------------|
| `-s, --source` | Source language code (required) |
| `-t, --target` | Target language code (required) |
| `-o, --output` | Output file path |
| `-e, --engine` | `translate` or `bedrock` |
| `-m, --model` | Bedrock model ID |
| `--terminology` | CSV file for Amazon Translate |
| `-g, --glossary` | JSON/text glossary for LLM |
| `--style` | Translation style (professional, casual, technical) |
| `--batch-size` | Texts per LLM batch (default: 20) |
| `--no-batch` | Disable batch mode for LLM |
| `--region` | AWS region |

## Language Codes

Common codes: `en`, `zh`, `zh-TW`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, `it`, `ru`

See [references/language-codes.md](references/language-codes.md) for full list.

## Terminology/Glossary

- **Amazon Translate**: Use `--terminology` with CSV file
- **Bedrock LLM**: Use `--glossary` with JSON or key=value file

See [references/glossary-format.md](references/glossary-format.md) for format details.

## Dependencies

```bash
pip install boto3 python-pptx
```

AWS credentials must be configured (`~/.aws/credentials` or environment variables).

## Examples

### Chinese presentation → English
```bash
python scripts/translate_pptx.py deck-cn.pptx -s zh -t en -e bedrock
# Output: deck-cn-en.pptx
```

### English → Japanese with terminology
```bash
python scripts/translate_pptx.py slides.pptx -s en -t ja \
  --terminology aws-terms.csv
```

### Batch translate with custom style
```bash
python scripts/translate_pptx.py marketing.pptx -s en -t zh \
  -e bedrock --style "friendly and engaging" --glossary brand-terms.json
```
