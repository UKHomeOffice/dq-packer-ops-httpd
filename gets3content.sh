#!/bin/bash

set -e

# Obtain HTTPD SSL configuration from s3 bucket
sudo /bin/aws s3 cp s3://$s3_bucket_name/httpd.conf /etc/httpd/conf/httpd.conf --region eu-west-2
sudo /bin/aws s3 cp s3://$s3_bucket_name/ssl.conf /etc/httpd/conf.d/ssl.conf --region eu-west-2

# Reload HTTPD
sudo systemctl reload httpd
