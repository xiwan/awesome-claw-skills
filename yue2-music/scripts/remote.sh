#!/bin/bash
# Drive the yue2-music skill's own scripts on a remote GPU host over AWS SSM,
# and bring artifacts back through S3.
#
# Why this exists: YuE2 needs a BF16-capable NVIDIA GPU and CUDA. Laptops
# (especially Apple Silicon) cannot run it, so the skill's helpers have to run
# somewhere else. This wrapper keeps the skill usable without SSH, without
# inbound ports, and without hardcoding any account-specific identifier.
#
# Config comes from yue2.env (see yue2.env.example):
#   YUE2_INSTANCE_TAG   Name tag of the GPU instance (preferred over an id)
#   YUE2_INSTANCE_ID    explicit instance id (overrides the tag lookup)
#   YUE2_AWS_REGION     region (default us-east-1)
#   YUE2_BUCKET         S3 bucket used to hand artifacts back
#   YUE2_REMOTE_DIR     install root on the host (default /opt/yue2)
#   YUE2_REMOTE_USER    unprivileged user that owns it (default ubuntu)
#   YUE2_OUT            local output dir (default ~/clawd/output/music)
#
# Usage: remote.sh {status|start|stop|run|push|generate|fetch|listen}

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Locate yue2.env without assuming a fixed install depth.
#   1. $YUE2_ENV_FILE if set
#   2. secrets/yue2.env walking up from this script
#   3. ~/clawd/secrets, ~/.config/yue2, ~/.yue2.env
find_env_file() {
    if [[ -n "${YUE2_ENV_FILE:-}" && -f "$YUE2_ENV_FILE" ]]; then
        echo "$YUE2_ENV_FILE"; return
    fi
    local dir="$SCRIPT_DIR"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/secrets/yue2.env" ]] && { echo "$dir/secrets/yue2.env"; return; }
        dir="$(dirname "$dir")"
    done
    for cand in "$HOME/clawd/secrets/yue2.env" \
                "$HOME/.config/yue2/yue2.env" \
                "$HOME/.yue2.env"; do
        [[ -f "$cand" ]] && { echo "$cand"; return; }
    done
}

ENV_FILE="$(find_env_file)"
if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a
fi

# Expired tokens in the environment silently shadow valid credentials in
# ~/.aws/credentials and every call then fails with AuthFailure. Opt in to
# clearing them by setting YUE2_CLEAR_ENV_CREDS=1.
if [[ "${YUE2_CLEAR_ENV_CREDS:-0}" == "1" ]]; then
    unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
fi

REGION="${YUE2_AWS_REGION:-us-east-1}"
REMOTE_DIR="${YUE2_REMOTE_DIR:-/opt/yue2}"
REMOTE_USER="${YUE2_REMOTE_USER:-ubuntu}"
OUT_DIR="${YUE2_OUT:-$HOME/clawd/output/music}"
SKILL_REMOTE="$REMOTE_DIR/YuE/skills/yue2-music"
VENV="$REMOTE_DIR/venv"
HF_CACHE="$REMOTE_DIR/hf-cache"
WORK="$REMOTE_DIR/work"

die() { echo "error: $*" >&2; exit 1; }

command -v aws >/dev/null || die "aws CLI not found"
command -v python3 >/dev/null || die "python3 not found"

require_config() {
    [[ -n "${YUE2_INSTANCE_ID:-}" || -n "${YUE2_INSTANCE_TAG:-}" ]] \
      || die "set YUE2_INSTANCE_TAG or YUE2_INSTANCE_ID in ${ENV_FILE:-yue2.env} (see yue2.env.example)"
}

resolve_instance() { # [state filter]
    if [[ -n "${YUE2_INSTANCE_ID:-}" ]]; then echo "$YUE2_INSTANCE_ID"; return; fi
    local states="${1:-running}"
    aws ec2 describe-instances --region "$REGION" \
        --filters "Name=tag:Name,Values=$YUE2_INSTANCE_TAG" \
                  "Name=instance-state-name,Values=$states" \
        --query "Reservations[0].Instances[0].InstanceId" --output text 2>/dev/null
}

any_instance() { # resolve across all live states, or die
    require_config
    local id; id="$(resolve_instance 'pending,running,stopping,stopped')"
    [[ -n "$id" && "$id" != "None" ]] \
      || die "no instance matches ${YUE2_INSTANCE_ID:-tag Name=$YUE2_INSTANCE_TAG} in $REGION"
    echo "$id"
}

need_running() {
    require_config
    local id; id="$(resolve_instance running)"
    if [[ -z "$id" || "$id" == "None" ]]; then
        echo "error: no running instance for ${YUE2_INSTANCE_ID:-tag Name=$YUE2_INSTANCE_TAG} in $REGION." >&2
        echo "It may be stopped to save GPU cost. Try: $(basename "$0") start" >&2
        exit 1
    fi
    echo "$id"
}

# Run one shell command on the host, print its output, exit non-zero on failure.
ssm_run() { # command [poll_iterations]
    local cmd="$1" tries="${2:-90}" cid st
    cid=$(aws ssm send-command --region "$REGION" --instance-ids "$IID" \
            --document-name AWS-RunShellScript \
            --parameters "$(python3 -c 'import json,sys;print(json.dumps({"commands":[sys.argv[1]]}))' "$cmd")" \
            --query 'Command.CommandId' --output text) \
        || die "send-command failed (is SSM Agent running and the instance role attached?)"
    for _ in $(seq 1 "$tries"); do
        st=$(aws ssm get-command-invocation --region "$REGION" --command-id "$cid" \
              --instance-id "$IID" --query 'Status' --output text 2>/dev/null)
        case "$st" in Success|Failed|Cancelled|TimedOut) break;; esac
        sleep 2
    done
    aws ssm get-command-invocation --region "$REGION" --command-id "$cid" \
        --instance-id "$IID" \
        --query '{S:Status,O:StandardOutputContent,E:StandardErrorContent}' --output json \
    | python3 -c '
import json,sys
d=json.load(sys.stdin)
sys.stdout.write(d["O"])
if d["E"].strip(): sys.stderr.write("--- remote stderr ---\n"+d["E"])
sys.exit(0 if d["S"]=="Success" else 1)'
}

# Same, as the unprivileged owner with the YuE2 environment preset.
as_user() { # command [poll_iterations]
    ssm_run "sudo -u $REMOTE_USER -H bash -c 'export PATH=$VENV/bin:\$PATH HF_HOME=$HF_CACHE HF_HUB_ENABLE_HF_TRANSFER=1; cd $SKILL_REMOTE; $1'" "${2:-90}"
}

need_bucket() { [[ -n "${YUE2_BUCKET:-}" ]] || die "YUE2_BUCKET is required to move files"; }

# Arguments are interpolated into a shell command string that SSM executes on
# the host, so validate anything that becomes part of that string. `run` is
# deliberately exempt: passing an arbitrary command is its entire purpose.
safe_name() { # reject anything that is not a plain identifier
    [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] \
      || die "invalid name '$1' — use letters, digits, dot, dash, underscore only"
}
safe_path() { # absolute path, no shell metacharacters
    [[ "$1" == /* ]] || die "remote path must be absolute: $1"
    [[ "$1" != *..* ]] || die "remote path must not contain '..': $1"
    [[ "$1" =~ ^[A-Za-z0-9/._-]+$ ]] \
      || die "remote path contains unsupported characters: $1"
}

cmd="${1:-help}"; shift || true
case "$cmd" in

status)
    IID="$(any_instance)" || exit 1
    aws ec2 describe-instances --region "$REGION" --instance-ids "$IID" \
      --query "Reservations[].Instances[].{Id:InstanceId,Type:InstanceType,State:State.Name,AZ:Placement.AvailabilityZone}" \
      --output json
    state=$(aws ec2 describe-instances --region "$REGION" --instance-ids "$IID" \
             --query "Reservations[0].Instances[0].State.Name" --output text)
    [[ "$state" == running ]] || { echo "(not running — start it to query the GPU)"; exit 0; }
    ssm_run 'nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv; df -h / | tail -1'
    ;;

start)
    IID="$(any_instance)" || exit 1
    aws ec2 start-instances --region "$REGION" --instance-ids "$IID" \
      --query 'StartingInstances[].{Id:InstanceId,Prev:PreviousState.Name,Now:CurrentState.Name}' --output json
    echo "waiting for SSM to come online..."
    for _ in $(seq 1 60); do
        [[ "$(aws ssm describe-instance-information --region "$REGION" \
              --filters "Key=InstanceIds,Values=$IID" \
              --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null)" == Online ]] \
          && { echo "online"; exit 0; }
        sleep 5
    done
    echo "still not online; check the instance console output" >&2; exit 1
    ;;

stop)
    require_config
    IID="$(resolve_instance 'pending,running')"
    [[ -n "$IID" && "$IID" != "None" ]] || { echo "already stopped"; exit 0; }
    aws ec2 stop-instances --region "$REGION" --instance-ids "$IID" \
      --query 'StoppingInstances[].{Id:InstanceId,Now:CurrentState.Name}' --output json
    ;;

run)
    [[ $# -ge 1 ]] || die "run needs a command string"
    IID="$(need_running)" || exit 1; as_user "$1" "${2:-90}"
    ;;

push) # local-file remote-path
    [[ $# -eq 2 ]] || die "push needs <local-file> <remote-path>"
    [[ -f "$1" ]] || die "no such file: $1"
    safe_path "$2"
    IID="$(need_running)" || exit 1
    B64=$(base64 < "$1" | tr -d '\n')
    ssm_run "sudo -u $REMOTE_USER -H bash -c 'mkdir -p \$(dirname $2) && echo $B64 | base64 -d > $2' && ls -la $2"
    ;;

generate) # request.json name [abc-file]
    [[ $# -ge 2 ]] || die "generate needs <request.json> <name> [abc-file]"
    REQ="$1"; NAME="$2"; ABC="${3:-}"
    safe_name "$NAME"
    IID="$(need_running)" || exit 1
    "$0" push "$REQ" "$WORK/inputs/$NAME.json" >/dev/null || die "could not push the request"
    ABCARG=""
    if [[ -n "$ABC" ]]; then
        "$0" push "$ABC" "$WORK/inputs/$NAME.abc" >/dev/null || die "could not push the score"
        ABCARG="--abc-file $WORK/inputs/$NAME.abc"
    fi
    echo "generating '$NAME' on $IID (roughly real time: a 1-minute song takes about a minute)"
    # Detached, so a long generation cannot outlive the SSM invocation window.
    as_user "nohup python scripts/run_yue2.py generate --request $WORK/inputs/$NAME.json $ABCARG --output $WORK/$NAME > $WORK/$NAME.log 2>&1 & echo pid \$!"
    for i in $(seq 1 80); do
        sleep 15
        if as_user "test -f $WORK/$NAME/result.json && echo DONE" 2>/dev/null | grep -q DONE; then
            echo "done after about $((i*15))s"
            as_user "tail -2 $WORK/$NAME.log"
            exit 0
        fi
        printf '.'
    done
    echo
    echo "still running after 20 minutes. Inspect with:" >&2
    echo "  $(basename "$0") run 'tail -30 $WORK/$NAME.log'" >&2
    exit 1
    ;;

fetch) # remote-dir [local-dir]
    [[ $# -ge 1 ]] || die "fetch needs <remote-dir> [local-dir]"
    safe_path "$1"
    need_bucket; IID="$(need_running)" || exit 1
    LOCAL="${2:-$OUT_DIR/$(basename "$1")}"
    KEY="transfer/$(basename "$1")-$(date +%s)"
    as_user "aws s3 cp $1 s3://$YUE2_BUCKET/$KEY/ --recursive --only-show-errors && echo uploaded" 120 \
      || die "upload failed — the instance role needs s3:PutObject on $YUE2_BUCKET"
    mkdir -p "$LOCAL"
    aws s3 cp "s3://$YUE2_BUCKET/$KEY/" "$LOCAL/" --recursive --only-show-errors --region "$REGION" \
      || die "download failed"
    find "$LOCAL" -type f | sort
    ;;

listen) # name-a name-b [local-dir]
    [[ $# -ge 2 ]] || die "listen needs <name-a> <name-b> [local-dir]"
    safe_name "$1"; safe_name "$2"
    IID="$(need_running)" || exit 1
    as_user "rm -rf $WORK/cmp-$1-$2 && python scripts/listen.py $WORK/$1 $WORK/$2 --output $WORK/cmp-$1-$2"
    "$0" fetch "$WORK/cmp-$1-$2" "${3:-$OUT_DIR/cmp-$1-$2}"
    echo "open the index.html in that directory to compare"
    ;;

*)
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    [[ "$cmd" == help || "$cmd" == -h || "$cmd" == --help ]] && exit 0
    exit 1
    ;;
esac
