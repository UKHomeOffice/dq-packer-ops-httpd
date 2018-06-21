#!/bin/sh

set -e

# Obtain HTTPD SSL configuration from s3 bucket
aws s3 cp s3://$(curl 169.254.169.254/latest/user-data)/httpd.conf /etc/httpd/conf/httpd.conf --region eu-west-2
aws s3 cp s3://$(curl 169.254.169.254/latest/user-data)/ssl.conf /etc/httpd/conf.d/ssl.conf --region eu-west-2

# Reload HTTPD
sudo systemctl reload httpd
