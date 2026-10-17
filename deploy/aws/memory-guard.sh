#!/usr/bin/env bash
# AIM's memory grows for as long as it runs, so jobs that fitted when they started can outgrow
# the machine hours later (on 2026-10-17, 22 AIM grid cells went from 23 to 116 GB in three
# hours). The queue starts nothing unless the machine has room; this guard handles growth after
# the start. Every 30 seconds, if swap passes 85 percent, it kills one job before the kernel's
# out-of-memory killer picks one at random. The queue records the job as failed and a later
# queue run starts it again.
#
# Which job: the cheapest to lose. Groundhog fits first (minutes each), then the grid cells from
# the lowest epsilon up, the youngest first within a rank. The epsilon 8 cells are the longest
# and set the finishing time, so they go last.
#
# Pausing jobs (SIGSTOP) was tried first and does not work: a paused process keeps its memory
# resident until the kernel is short enough to swap it out, so free memory never rose, the guard
# kept pausing, and within 30 minutes 21 of 22 jobs were paused and nothing ran.
#
#   memory-guard.sh   (run as root by the facsimile-guard service, see start-queue.sh)
set -uo pipefail
log=/home/ubuntu/facsimile/data/runs/memory-guard.log
pattern='facsimile[.]cli (synth|groundhog-fit)'

swap_pct() { awk '/SwapTotal/ {t=$2} /SwapFree/ {f=$2} END {print (t ? int(100 * (t - f) / t) : 0)}' /proc/meminfo; }
note() { echo "$(date -u +%FT%TZ) $*" >> "$log"; }

# "rank elapsed pid" for every job; the lowest sorts first and is killed first.
ranked() {
  for pid in $(pgrep -f "$pattern"); do
    args=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null) || continue
    case "$args" in
      *groundhog-fit*) rank=0 ;;
      *"--epsilon 0.5 "* | *"--epsilon 1 "*) rank=1 ;;
      *"--epsilon 2 "*) rank=2 ;;
      *"--epsilon 4 "*) rank=4 ;;
      *"--epsilon 8 "*) rank=8 ;;
      *) rank=0 ;;
    esac
    echo "$rank $(ps -o etimes= -p "$pid" | tr -d ' ') $pid"
  done
}

while true; do
  sleep 30
  if [ "$(swap_pct)" -gt 85 ]; then
    pid=$(ranked | sort -k1,1n -k2,2n | head -1 | awk '{print $3}')
    [ -n "$pid" ] || continue
    note "killed $pid ($(tr '\0' ' ' < "/proc/$pid/cmdline" | sed -E 's/.*cli //')): swap at $(swap_pct) percent"
    kill -KILL "$pid"
    sleep 60
  fi
done
