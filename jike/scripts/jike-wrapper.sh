#!/usr/bin/env bash
# Jike API wrapper - auto-loads tokens from secrets file
# Usage: ./jike-wrapper.sh feed --limit 5
#        ./jike-wrapper.sh post --content "Hello"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SECRETS_FILE="${JIKE_SECRETS_FILE:-$HOME/clawd/secrets/jike.json}"

if [[ ! -f "$SECRETS_FILE" ]]; then
    echo "Error: $SECRETS_FILE not found. Run auth.py first." >&2
    exit 1
fi

# Load tokens
export JIKE_ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$SECRETS_FILE'))['access_token'])")
export JIKE_REFRESH_TOKEN=$(python3 -c "import json; print(json.load(open('$SECRETS_FILE'))['refresh_token'])")

# Run command
python3 "$SCRIPT_DIR/client.py" "$@"
