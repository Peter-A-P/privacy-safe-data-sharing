#!/usr/bin/env bash
# One spot instance for the AIM work, with its spend controls. Decided 2026-10-17 (PLAN.md
# section 7): a 32-vCPU, 128 GB spot instance in ca-central-1, hard 72-hour power-off. Launched
# 2026-10-17 as m6a.8xlarge at US$0.50 an hour with MAX_PRICE_USD=0.55, after m8i-flex had no
# capacity for an hour; estimate CA$34, at most CA$54 of the project's CA$55. AWS rather than
# Azure because the Azure spot-core quota request was still unanswered after a day; this account
# already had 32 spot vCPUs.
#
# Spend controls, in the order they bite:
#   1. The queue powers the machine off when it runs out of work (`queue run --then`).
#   2. An `at` job armed at first boot powers it off 72 hours after boot (cloud-init.yaml).
#   3. Spot price capped at US$0.45 an hour: above it AWS interrupts rather than charges more.
#      Launches in the cheapest zone under the cap that has capacity.
#   4. A budget on this instance type's spot usage emails at 50, 80 and 100 percent of US$30
#      (about CA$40).
# Powering off stops the instance (shutdown behaviour "stop", persistent request, interruption
# behaviour "stop"): a stopped instance bills only its 64 GB disk, and an interrupted one
# resumes its queue when capacity returns.
#
# Access: SSH key only, from one IP address, IMDSv2 only, no instance role. The IEEE-CIS rows go
# to this machine by Peter's decision of 2026-10-17 (docs/data.md): a private instance in his
# account, terminated with its disk by teardown.sh after the run.
set -euo pipefail
export AWS_PROFILE=${AWS_PROFILE:-facsimile}
export AWS_REGION=ca-central-1
export MSYS_NO_PATHCONV=1  # Git Bash would rewrite the /aws/service parameter name as a path
NAME=facsimile-aim
# 32 vCPU and 128 GB. m8i-flex because AWS's spot advisor put its interruption rate in
# ca-central-1 under 5 percent on 2026-10-17; m5 and m5a were over 20 percent, and a first
# m5a.8xlarge was interrupted ten minutes after launch.
TYPES=${TYPES:-m8i-flex.8xlarge}
MAX_PRICE_USD=${MAX_PRICE_USD:-0.45}
MY_IP=${MY_IP:-$(curl -s https://api.ipify.org)}
KEY=${KEY:-$HOME/.ssh/facsimile_aim.pub}
EMAIL=${EMAIL:?set EMAIL to the address the budget alerts go to}
HERE=$(cd "$(dirname "$0")" && pwd)
TAG="Key=project,Value=facsimile"

aws ec2 describe-key-pairs --key-names "$NAME" >/dev/null 2>&1 \
  || aws ec2 import-key-pair --key-name "$NAME" --public-key-material "fileb://$(cygpath -m "$KEY" 2>/dev/null || echo "$KEY")" \
       --tag-specifications "ResourceType=key-pair,Tags=[{$TAG}]" >/dev/null

VPC=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)
SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$NAME" "Name=vpc-id,Values=$VPC" \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = "None" ]; then
  SG=$(aws ec2 create-security-group --group-name "$NAME" --vpc-id "$VPC" \
    --description "SSH from the build desktop only" \
    --tag-specifications "ResourceType=security-group,Tags=[{$TAG}]" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 22 \
    --cidr "$MY_IP/32" >/dev/null
fi

AMI=$(aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
  --query Parameter.Value --output text)

# Every (type, zone) under the price cap, cheapest first; the first with capacity wins.
OFFERS=$(aws ec2 describe-spot-price-history --instance-types $TYPES --product-descriptions Linux/UNIX \
  --start-time "$(date -u +%FT%TZ)" \
  --query "sort_by(SpotPriceHistory[?to_number(SpotPrice) < \`$MAX_PRICE_USD\`], &SpotPrice)[].[InstanceType, AvailabilityZone, SpotPrice]" \
  --output text)
ID=
while read -r TYPE AZ PRICE; do
  [ -n "$TYPE" ] || continue
  SUBNET=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC" "Name=availability-zone,Values=$AZ" \
    "Name=default-for-az,Values=true" --query 'Subnets[0].SubnetId' --output text </dev/null)
  echo "trying $TYPE in $AZ at US\$$PRICE" >&2
  ID=$(aws ec2 run-instances --image-id "$AMI" --instance-type "$TYPE" --key-name "$NAME" \
    --security-group-ids "$SG" --subnet-id "$SUBNET" --associate-public-ip-address \
    --instance-market-options "{\"MarketType\":\"spot\",\"SpotOptions\":{\"MaxPrice\":\"$MAX_PRICE_USD\",\"SpotInstanceType\":\"persistent\",\"InstanceInterruptionBehavior\":\"stop\"}}" \
    --instance-initiated-shutdown-behavior stop \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":64,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
    --metadata-options HttpTokens=required,HttpEndpoint=enabled \
    --user-data "fileb://$(cygpath -m "$HERE" 2>/dev/null || echo "$HERE")/cloud-init.yaml" \
    --tag-specifications "ResourceType=instance,Tags=[{$TAG},{Key=Name,Value=$NAME}]" \
      "ResourceType=volume,Tags=[{$TAG}]" "ResourceType=spot-instances-request,Tags=[{$TAG}]" \
    --query 'Instances[0].InstanceId' --output text </dev/null) && break
done <<< "$OFFERS"
[ -n "$ID" ] || { echo "no capacity under US\$$MAX_PRICE_USD in any zone" >&2; exit 1; }
aws ec2 wait instance-running --instance-ids "$ID"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
aws budgets describe-budget --account-id "$ACCOUNT" --budget-name "$NAME" >/dev/null 2>&1 \
  || aws budgets create-budget --account-id "$ACCOUNT" \
    --budget "{\"BudgetName\":\"$NAME\",\"BudgetLimit\":{\"Amount\":\"30\",\"Unit\":\"USD\"},\"TimeUnit\":\"MONTHLY\",\"BudgetType\":\"COST\",\"CostFilters\":{\"UsageType\":[\"CAN1-SpotUsage:m8i-flex.8xlarge\",\"CAN1-SpotUsage:m6a.8xlarge\",\"CAN1-SpotUsage:m5a.8xlarge\",\"CAN1-EBS:VolumeUsage.gp3\"]}}" \
    --notifications-with-subscribers "$(python -c "import json,sys; print(json.dumps([{'Notification':{'NotificationType':'ACTUAL','ComparisonOperator':'GREATER_THAN','Threshold':t,'ThresholdType':'PERCENTAGE'},'Subscribers':[{'SubscriptionType':'EMAIL','Address':sys.argv[1]}]} for t in (50,80,100)]))" "$EMAIL")"

IP=$(aws ec2 describe-instances --instance-ids "$ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "$ID $IP $TYPE $AZ $PRICE"
