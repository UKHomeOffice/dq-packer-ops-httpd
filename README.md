# dq-packer-ops-httpd
This repository creates an AMI in AWS with latest version of HTTPD

## Features

### `packer.json`
This file contains the install script and deploys AMI using redhat

Installing the following:
- latest version of HTTPD service
- script to pull HTTPD config from s3
- scripts to check expiry of certs and if remote backups are out of date
- aazon cloudwatch agent

### `templates`

#### `gets3content.sh`
This file is copied to `/home/ec2-user` and cron entry created to run it every minute

## Deploying / Publishing
Drone min ver 0.5 is needed to deploy with `.drone.yaml` file


## Configuration


## Contributing

If you'd like to contribute, please fork the repository and use a feature
branch. Pull requests are warmly welcome.

More information in [`CONTRIBUTING`](./CONTRIBUTING)

## Licensing
The code in this project is licensed under this [`LICENSE`](./LICENSE)
