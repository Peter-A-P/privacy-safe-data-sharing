#!/usr/bin/env bash
# After the last `sync.sh pull`: cancel the spot request, terminate the instance (its disk, and the
# IEEE-CIS rows on it, go with it), then remove the security group, the key pair and the budget.
set -euo pipefail
export AWS_PROFILE=${AWS_PROFILE:-facsimile}
export AWS_REGION=ca-central-1
export MSYS_NO_PATHCONV=1  # keep Git Bash from rewriting arguments as paths
NAME=facsimile-aim

REQS=$(aws ec2 describe-spot-instance-requests --filters Name=tag:project,Values=facsimile \
  --query 'SpotInstanceRequests[?State!=`cancelled`].SpotInstanceRequestId' --output text)
[ -n "$REQS" ] && aws ec2 cancel-spot-instance-requests --spot-instance-request-ids $REQS >/dev/null
IDS=$(aws ec2 describe-instances --filters Name=tag:project,Values=facsimile \
  Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [ -n "$IDS" ]; then
  aws ec2 terminate-instances --instance-ids $IDS >/dev/null
  aws ec2 wait instance-terminated --instance-ids $IDS
fi
SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$NAME" --query 'SecurityGroups[0].GroupId' --output text)
[ "$SG" != "None" ] && aws ec2 delete-security-group --group-id "$SG"
aws ec2 delete-key-pair --key-name "$NAME" >/dev/null
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
aws budgets delete-budget --account-id "$ACCOUNT" --budget-name "$NAME" 2>/dev/null || true
aws ec2 describe-volumes --filters Name=tag:project,Values=facsimile --query 'Volumes[].VolumeId' --output text
echo "torn down (no volume ids above means no disk is left)"
