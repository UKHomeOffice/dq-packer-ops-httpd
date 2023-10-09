#!/bin/sh
# Get the instance region and inject it in the conf
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 3600"`
EC2_AVAIL_ZONE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)

EC2_REGION="`echo \"$EC2_AVAIL_ZONE\" | sed 's/[a-z]$//'`"
sed -i -e 's/.*region.*/region = '$EC2_REGION'/' /var/awslogs/etc/aws.conf

# Restart the awslogs agent
systemctl restart awslogs
