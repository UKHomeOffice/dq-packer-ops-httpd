#!/bin/sh
# Get the instance region and inject it in the conf
EC2_AVAIL_ZONE=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
EC2_REGION="`echo \"$EC2_AVAIL_ZONE\" | sed 's/[a-z]$//'`"
sed -i -e 's/.*region.*/region = '$EC2_REGION'/' /var/awslogs/etc/aws.conf

# Restart the awslogs agent
systemctl restart awslogs
