#!/usr/bin/env bash
# Start / stop / status the EC2 instance hosting ComfyUI.
#
# GPU instances are expensive per hour. Stop the box when idle.
#
# Requires:
#   COMFY_INSTANCE_ID   EC2 instance id
#   COMFY_AWS_REGION    region (default us-east-1)
# Both may come from comfyui.env (auto-discovered by walking up from this
# script, or set COMFY_ENV_FILE to point at it explicitly).
#
# Usage: instance.sh {start|stop|status}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Locate comfyui.env without assuming a fixed install depth.
#   1. $COMFY_ENV_FILE if set
#   2. secrets/comfyui.env walking up from this script
#   3. ~/clawd/secrets, ~/.config/comfyui, ~/.comfyui.env
find_env_file() {
    if [[ -n "${COMFY_ENV_FILE:-}" && -f "$COMFY_ENV_FILE" ]]; then
        echo "$COMFY_ENV_FILE"; return
    fi
    local dir="$SCRIPT_DIR"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/secrets/comfyui.env" ]] && { echo "$dir/secrets/comfyui.env"; return; }
        dir="$(dirname "$dir")"
    done
    for cand in "$HOME/clawd/secrets/comfyui.env" \
                "$HOME/.config/comfyui/comfyui.env" \
                "$HOME/.comfyui.env"; do
        [[ -f "$cand" ]] && { echo "$cand"; return; }
    done
}

ENV_FILE="$(find_env_file)"

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a
fi

REGION="${COMFY_AWS_REGION:-us-east-1}"

if [[ -z "${COMFY_INSTANCE_ID:-}" ]]; then
    echo "error: COMFY_INSTANCE_ID is not set" >&2
    echo "Set it in the environment or in $ENV_FILE" >&2
    exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
    echo "error: AWS CLI not found on PATH" >&2
    exit 1
fi

state() {
    aws ec2 describe-instances --region "$REGION" \
        --instance-ids "$COMFY_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name' --output text
}

case "${1:-}" in
    start)
        echo "starting $COMFY_INSTANCE_ID in $REGION ..."
        aws ec2 start-instances --region "$REGION" \
            --instance-ids "$COMFY_INSTANCE_ID" >/dev/null
        for _ in $(seq 1 30); do
            s="$(state)"
            echo "  $s"
            [[ "$s" == "running" ]] && break
            sleep 10
        done
        echo "instance running. ComfyUI usually needs ~1 more minute."
        echo "Tip: txt2img.sh --wake polls until the API answers."
        ;;
    stop)
        echo "stopping $COMFY_INSTANCE_ID in $REGION ..."
        aws ec2 stop-instances --region "$REGION" \
            --instance-ids "$COMFY_INSTANCE_ID" >/dev/null
        echo "stop requested. Disk (and your models) are preserved."
        echo "Note: the root volume still bills while stopped."
        ;;
    status)
        echo "$COMFY_INSTANCE_ID ($REGION): $(state)"
        ;;
    *)
        echo "Usage: $(basename "$0") {start|stop|status}" >&2
        exit 1
        ;;
esac
