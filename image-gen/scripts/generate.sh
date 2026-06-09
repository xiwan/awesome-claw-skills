#!/bin/bash
# Wrapper for generate.py
exec python3 "$(dirname "$0")/generate.py" "$@"
