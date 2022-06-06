import logging
import boto3
import botocore
import os
from botocore.config import Config

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

CONFIG = Config(
    retries=dict(
        max_attempts=20
    )
)



def check_python_v():

    try:
        version = os.system("/usr/src/Python-3.7.13/python -V")
        return

        print(version)
    except botocore.exceptions.ClientErrors as e:
        if e.response['Error']['Code'] == '503':
            logging.info('Service Reload Failed')
        else:
            raise

check_python_v()

# def upgrade_python():
#
# def gets3content():
#     s3_bucket_name = os.getenv('s3_bucket_name')
#
#     try:
#         s3.Bucket(s3_bucket_name).download_file('ssl.conf', '/etc/httpd/conf.d/ssl.conf')
#     except botocore.exceptions.ClientErrors as e:
#         if e.response['Error']['Code'] == '404':
#             logging.info('The Object does not exist')
#         else:
#             raise
#
#     try:
#         s3.Bucket(s3_bucket_name).download_file('httpd.conf', '/etc/httpd/conf/httpd.conf')
#     except botocore.exceptions.ClientErrors as e:
#         if e.response['Error']['Code'] == '404':
#             logging.info('The Object does not exist')
#         else:
#             raise
#     try:
#         os.system("sudo systemctl reload httpd")
#     except botocore.exceptions.ClientErrors as e:
#         if e.response['Error']['Code'] == '503':
#             logging.info('Service Reload Failed')
#         else:
#             raise
#
# gets3content()
