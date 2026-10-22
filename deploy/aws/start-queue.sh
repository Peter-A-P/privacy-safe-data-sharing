#!/usr/bin/env bash
# Run on the rented machine after `sync.sh push`: the queue as a systemd service, so that a spot
# interruption (the instance stops, then starts again when capacity returns) resumes it. The
# queue skips every job whose output exists, stops starting jobs at 70 hours and powers the
# machine off when it is done; the 72-hour `at` job is the backstop. It disables itself before
# powering off: a queue with nothing left to do, started again at boot, would power the machine
# straight back off and leave no window to pull the results (2026-10-19).
#
#   start-queue.sh JOBS_FILE PARALLEL MEMORY_GB
set -euo pipefail
jobs_file=$1
parallel=$2
memory_gb=$3
repo=$HOME/facsimile
sudo tee /etc/systemd/system/facsimile-queue.service >/dev/null <<EOF
[Unit]
Description=facsimile job queue
After=network-online.target

[Service]
User=$USER
WorkingDirectory=$repo
ExecStart=$repo/.venv/bin/python -m facsimile.cli queue run $jobs_file --jobs $parallel --memory-gb $memory_gb --hours 70 --then "sudo systemctl disable facsimile-queue; sudo /usr/sbin/shutdown -h now" --log data/runs/cloud-queue.log
Restart=no

[Install]
WantedBy=multi-user.target
EOF
sudo tee /etc/systemd/system/facsimile-guard.service >/dev/null <<EOF
[Unit]
Description=pause AIM jobs before they exhaust memory (memory-guard.sh)

[Service]
ExecStart=/bin/bash $repo/deploy/aws/memory-guard.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now facsimile-guard.service
sudo systemctl enable facsimile-queue.service
sudo systemctl restart facsimile-queue.service
systemctl --no-pager status facsimile-queue.service | head -5
