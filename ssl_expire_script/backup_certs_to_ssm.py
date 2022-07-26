import json
import logging
import urllib.parse
import datetime
import sys
import os
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

CONFIG = Config(
    retries=dict(
        max_attempts=20
    )
)

logging.basicConfig(filename='/home/ec2-user/ssl_expire_script/backup.log', level=logging.INFO)

now = datetime.datetime.today()
now = now.strftime("%Y-%m-%d %H:%M:%S")
expiry_file = "/home/ec2-user/ssl_expire_script/cert_expiry.txt"
get_remote_expiry = os.getenv('GET_REMOTE_EXPIRY_COMMAND')
remote_expiry_file = "/home/ec2-user/ssl_expire_script/remote_cert_expiry.txt"
bucket = os.getenv('BUCKET')
s3_file_landing = os.getenv('S3_FILE_LANDING')
live_certs = os.getenv('LIVE_CERTS')


def error_handler(lineno, error, fail=True):

    try:
        logging.error('The following error has occurred on line: %s', lineno)
        logging.error(str(error))

        send_message_to_slack(
            'An Error has occured with the get certificate expiry script!')
        if fail:
            sys.exit(1)

    except Exception as err:
        error_handler(sys.exc_info()[2].tb_lineno, err)
        logging.error(
            'The following error has occurred on line: %s',
            sys.exc_info()[2].tb_lineno)
        logging.error(str(err))
        sys.exit(1)


def send_message_to_slack(text):
    """
    Formats the text provides and posts to a specific Slack web app's URL
    Args:
        text : the message to be displayed on the Slack channel
    Returns:
        Slack HTTPD repsonse
    """

    try:
        post = {
            "text": ":fire: :sad_parrot: *SSL Certificate BACKUP SCRIPT Status for HTTPD Proxy:* :sad_parrot: :fire:",
            "attachments": [
                {
                    "text": "{0}".format(text),
                    "color": "#B22222",
                    "attachment_type": "default",
                    "fields": [
                        {
                            "title": "Priority",
                            "value": "High",
                            "short": "false"
                        }
                    ],
                    "footer": "AWS HTTPD",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
                }
            ]
        }

        ssm_param_name = 'slack_notification_webhook'
        ssm = boto3.client('ssm', config=CONFIG, region_name='eu-west-2')
        try:
            response = ssm.get_parameter(
                Name=ssm_param_name, WithDecryption=True)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                LOGGER.info(
                    'Slack SSM parameter %s not found. No notification sent', ssm_param_name)
                return
            else:
                logging.error(
                    "Unexpected error when attempting to get Slack webhook URL: %s", e)
                return
        if 'Value' in response['Parameter']:
            url = response['Parameter']['Value']

            json_data = json.dumps(post)
            req = urllib.request.Request(
                url,
                data=json_data.encode('ascii'),
                headers={'Content-Type': 'application/json'})
            LOGGER.info('Sending notification to Slack')
            response = urllib.request.urlopen(req)

        else:
            LOGGER.info(
                'Value for Slack SSM parameter %s not found. No notification sent', ssm_param_name)
            return

    except Exception as err:
        logging.error(
            'The following error has occurred on line: %s',
            sys.exc_info()[2].tb_lineno)
        logging.error(str(err))


def check_remote_expiry():

    try:
        os.system(f"/bin/aws s3 cp s3://{bucket}/analysis/letsencrypt/cert.pem {s3_file_landing}")
        os.system(f"sudo {get_remote_expiry} > {remote_expiry_file}")

        #strip unwanted text from get_expiry to get enddate <class 'str'>
        f = open(remote_expiry_file, "r")
        for date in f:
            date = date[9:]
            # remove whitespace after enddate
            enddate_str = date.strip()

        #convert enddate_str to datetime
        enddate_obj = datetime.datetime.strptime(enddate_str, "%b %d %H:%M:%S %Y %Z")
        logging.info(f"Remote Certificate expiry datetime is: {enddate_obj}")

        #convert now_str to datetime
        now_obj = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        logging.info(f"Current datetime is: {now_obj}")

        #Get the length of period between now and enddate
        renewal_length =  enddate_obj - now_obj
        logging.info(f"Remote Renewal length: {renewal_length}")

        #ACQUIRE LOCAL CERT EXIPRY

        #The compairson condition depends on the existance of cert_expiry.txt
        my_file = Path("/home/ec2-user/ssl_expire_script/cert_expiry.txt")
        if my_file.is_file():
            #strip unwanted text from get_expiry to get enddate <class 'str'>
            l = open(expiry_file, "r")
            for local_date in l:
                local_date = local_date[9:]
                # remove whitespace after enddate
                local_enddate_str = local_date.strip()

            #convert local_enddate_str to datetime
            local_enddate_obj = datetime.datetime.strptime(local_enddate_str, "%b %d %H:%M:%S %Y %Z")
            logging.info(f"Local Certificate expiry datetime is: {local_enddate_obj}")

            #Get the length of period between now and local_enddate
            local_renewal_length = local_enddate_obj - now_obj
            logging.info(f"Local Renewal length: {local_renewal_length}")

            # #if the current time is greater than the remote_enddate and current time less than local_enddate send message to slack
            # if now_obj > enddate_obj and now_obj < local_enddate_obj:
            #     file_list = os.listdir(live_certs)
            #     for i in file_list:
            #         os.system(f"aws s3 cp {live_certs}/{i} s3://{bucket}/analysis/letsencrypt/")
            #         logging.info(f"REMOTE SSL Certificates expired by {renewal_length} . Local certficates are valid. Uploaded local certs to s3")

            #if local reneal lenth is greater than remote renewal then upload local certs to s3
            if local_renewal_length > renewal_length:
                os.system(f"sudo aws s3 cp {live_certs}/cert.pem s3://{bucket}/analysis/letsencrypt/")
                os.system(f"sudo aws s3 cp {live_certs}/chain.pem s3://{bucket}/analysis/letsencrypt/")
                os.system(f"sudo aws s3 cp {live_certs}/fullchain.pem s3://{bucket}/analysis/letsencrypt/")
                os.system(f"sudo aws s3 cp {live_certs}/privkey.pem s3://{bucket}/analysis/letsencrypt/")
                logging.info(f"REMOTE SSL Cert renwal length {renewal_length} is greater than Local cert renewal_length {local_renewal_length}. Uploaded local certs to s3")


    except Exception as err:
        error_handler(sys.exc_info()[2].tb_lineno, err)

check_remote_expiry()
