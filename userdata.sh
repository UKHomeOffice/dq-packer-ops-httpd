#!/bin/bash

dnf -y update
dnf install -y openssl-devel
dnf install -y  wget
dnf install -y  python39
dnf install -y python3-pip
dnf install -y cloud-utils-growpart.noarch
dnf install -y httpd
dnf install -y install -y mod_ssl
dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
dnf install -y python3-certbot-apache
dnf install -y policycoreutils-python-utils-2.8-16.1.el8.noarch
dnf install -y awscli
pip3 install install boto3 futures lxml

systemctl start httpd
semanage permissive -a httpd_t
setsebool httpd_can_network_relay on
setsebool -P httpd_can_network_relay on
aws s3 cp s3://dq-config-bucket/dq-packer-ops-httpd /tmp/install --recursive
cp -f /tmp/install/httpd.conf /etc/httpd/conf/httpd.conf
cp -f /tmp/install/ssl.conf /etc/httpd/conf.d/ssl.conf
cp -f /tmp/install/config.ini /etc/letsencrypt/config.ini
chmod 644 /etc/letsencrypt/config.ini
wget https://s3.amazonaws.com//aws-cloudwatch/downloads/latest/awslogs-agent-setup.py > /tmp/awslogs-agent-setup.py
chmod +x /tmp/awslogs-agent-setup.py
wget https://s3.amazonaws.com/amazoncloudwatch-agent/centos/amd64/latest/amazon-cloudwatch-agent.rpm > /tmp/amazon-cloudwatch-agent.rpm
chmod +x /tmp/amazon-cloudwatch-agent.rpm
