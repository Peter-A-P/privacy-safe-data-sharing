#!/usr/bin/env bash
# Move work to and from the rented machine with tar over SSH (no rsync on the Windows desktop).
#
#   sync.sh push IP   the code (tracked and new files, nothing git ignores), the built splits and
#                     the Groundhog pools and the job files. No raw file goes: the machine only
#                     needs the coded data.
#   sync.sh pull IP   every file the machine wrote after the push: grid tables and records,
#                     Groundhog features, the queue log. Files that came from the desktop are left
#                     alone.
set -euo pipefail
cmd=$1
ip=$2
key=${KEY:-$HOME/.ssh/facsimile_aim}
user=${SSH_USER:-ubuntu}
repo=$(cd "$(dirname "$0")/.." && pwd)
remote=facsimile
ssh_=(ssh -i "$key" -o StrictHostKeyChecking=accept-new "$user@$ip")

case "$cmd" in
  push)
    cd "$repo"
    { git ls-files -co --exclude-standard; find data/build -type f; find data/groundhog -maxdepth 2 -type f \( -name pools.parquet -o -name targets.json \); find data/runs -maxdepth 1 -name '*.jsonl'; } \
      | sort -u | tar czf - -T - | "${ssh_[@]}" "mkdir -p $remote && tar xzf - -C $remote && touch $remote/.pushed-at"
    "${ssh_[@]}" "cd $remote && ~/.local/bin/uv sync --locked --extra reference -q && .venv/bin/python -c 'import facsimile, snsynth; print(\"ready\")'"
    ;;
  pull)
    "${ssh_[@]}" "cd $remote && find results data/synth data/groundhog data/runs -type f -newer .pushed-at -print0 | tar czf - --null -T -" \
      | tar xzf - -C "$repo"
    ;;
  *)
    echo "usage: sync.sh push|pull IP" >&2
    exit 2
    ;;
esac
