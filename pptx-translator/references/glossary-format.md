# Glossary and Terminology Files

## For Amazon Translate (--terminology)

Use CSV format with these columns:
- `en` (or source language code)
- Target language code

Example `terminology.csv`:
```csv
en,zh
Amazon Web Services,亚马逊云科技
machine learning,机器学习
serverless,无服务器
```

The terminology will be uploaded to Amazon Translate and applied during translation.

## For Bedrock LLM (--glossary)

### JSON Format
```json
{
  "Amazon Web Services": "亚马逊云科技",
  "machine learning": "机器学习",
  "serverless": "无服务器",
  "AWS": "AWS",
  "API": "API"
}
```

### Simple Key-Value Format
```
Amazon Web Services=亚马逊云科技
machine learning=机器学习
serverless=无服务器
AWS=AWS
API=API
```

## Best Practices

1. **Keep it focused**: Include only terms that require specific translations
2. **Brand names**: Decide whether to translate or keep original
3. **Acronyms**: Specify if they should remain in English
4. **Technical terms**: Ensure consistency across the document
5. **Test first**: Run on a few slides to verify glossary works as expected
