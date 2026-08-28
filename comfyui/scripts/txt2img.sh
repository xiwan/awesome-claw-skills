#!/bin/bash
# Wrapper for txt2img.py
exec python3 "$(dirname "$0")/txt2img.py" "$@"
