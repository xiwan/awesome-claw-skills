#!/bin/bash
# Host resource monitor - checks CPU, memory, disk usage

# Thresholds
CPU_WARN=80
CPU_CRIT=95
MEM_WARN=85
MEM_CRIT=95
DISK_WARN=80
DISK_CRIT=90

# Colors (if terminal supports)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Get CPU usage (average over 1 second)
get_cpu() {
    # Use vmstat for reliable CPU reading
    local cpu_idle=$(vmstat 1 2 | tail -1 | awk '{print $15}')
    if [ -z "$cpu_idle" ] || ! [[ "$cpu_idle" =~ ^[0-9]+$ ]]; then
        cpu_idle=99  # Fallback if can't read
    fi
    echo $((100 - cpu_idle))
}

# Get memory usage
get_memory() {
    free | awk '/Mem:/ {printf "%.0f", $3/$2*100}'
}

get_memory_detail() {
    free -h | awk '/Mem:/ {print $3 " / " $2}'
}

# Get disk usage
get_disk() {
    df / | awk 'NR==2 {print $5}' | tr -d '%'
}

get_disk_detail() {
    df -h / | awk 'NR==2 {print $3 " / " $2}'
}

# Get CPU cores
get_cores() {
    nproc
}

# Status indicator
status_icon() {
    local value=$1
    local warn=$2
    local crit=$3
    
    if [ "$value" -ge "$crit" ]; then
        echo "🔴"
    elif [ "$value" -ge "$warn" ]; then
        echo "⚠️"
    else
        echo "✅"
    fi
}

# Main
echo "=== Host Resources ==="

CPU=$(get_cpu)
MEM=$(get_memory)
DISK=$(get_disk)

CPU_ICON=$(status_icon $CPU $CPU_WARN $CPU_CRIT)
MEM_ICON=$(status_icon $MEM $MEM_WARN $MEM_CRIT)
DISK_ICON=$(status_icon $DISK $DISK_WARN $DISK_CRIT)

echo "CPU:    ${CPU}% used ($(get_cores) cores) $CPU_ICON"
echo "Memory: ${MEM}% used ($(get_memory_detail)) $MEM_ICON"
echo "Disk:   ${DISK}% used ($(get_disk_detail)) $DISK_ICON"

# Overall status
echo ""
if [ "$CPU" -ge "$CPU_CRIT" ] || [ "$MEM" -ge "$MEM_CRIT" ] || [ "$DISK" -ge "$DISK_CRIT" ]; then
    echo "Status: 🔴 CRITICAL - Immediate attention needed!"
    exit 2
elif [ "$CPU" -ge "$CPU_WARN" ] || [ "$MEM" -ge "$MEM_WARN" ] || [ "$DISK" -ge "$DISK_WARN" ]; then
    echo "Status: ⚠️ WARNING - Resource pressure detected"
    exit 1
else
    echo "Status: ✅ All OK"
    exit 0
fi
