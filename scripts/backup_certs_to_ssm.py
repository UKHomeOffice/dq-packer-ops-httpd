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

expiry_file = "/home/centos/ssl_expire_script/cert_expiry.txt"
now = datetime.datetime.today()
now = now.strftime("%Y-%m-%d %H:%M:%S")

get_remote_expiry = os.getenv('GET_REMOTE_EXPIRY_COMMAND')
remote_expiry_file = "/home/centos/ssl_expire_script/remote_cert_expiry.txt"
pem_dir_one = os.getenv('PEM_DIR_ONE')
pem_dir_two = os.getenv('PEM_DIR_TWO')
pem_dir_three = os.getenv('PEM_DIR_THREE')


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

def put_ssm_parameter():

    try:
        ssm = boto3.client('ssm')

        with open(pem_dir_one, 'r') as f:
             file1 = f.read()

        response = ssm.put_parameter(
                Name='analysis_proxy_certificate',
                Description='automated backup',
                Value=file1,
                Type='SecureString',
                Overwrite=True,
                Tier='Standard',
                DataType='text'
        )

        with open(pem_dir_two, 'r') as f:
             file1 = f.read()

        response = ssm.put_parameter(
                Name='analysis_proxy_certificate_fullchain',
                Description='automated backup',
                Value=file1,
                Type='SecureString',
                Overwrite=True,
                Tier='Standard',
                DataType='text'
        )

        with open(pem_dir_three, 'r') as f:
             file1 = f.read()

        response = ssm.put_parameter(
                Name='analysis_proxy_certificate_key',
                Description='automated backup',
                Value=file1,
                Type='SecureString',
                Overwrite=True,
                Tier='Standard',
                DataType='text'
        )
    except Exception as err:
        error_handler(sys.exc_info()[2].tb_lineno, err)

def check_remote_expiry():

    try:
        #download remote Cert from ssm parameter and store locally
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(Name='analysis_proxy_certificate', WithDecryption=True)

        with open('/home/centos/ssl_expire_script/remote_cert.pem', 'w') as f:
             sys.stdout = f
             print(parameter['Parameter']['Value'])

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
        renewal_length = now_obj - enddate_obj
        logging.info(f"Remote Renewal length: {renewal_length}")

        #ACQUIRE LOCAL CERT EXIPRY

        #The compairson condition depends on the existance of cert_expiry.txt 
        my_file = Path("/home/centos/ssl_expire_script/cert_expiry.txt")
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
            local_renewal_length = now_obj - local_enddate_obj
            logging.info(f"Local Renewal length: {local_renewal_length}")

            #if the current time is greater than the remote_enddate and current time less than local_enddate send message to slack
            if now_obj > enddate_obj and now_obj < local_enddate_obj:
               logging.info(f"REMOTE SSL Certificates expired by {renewal_length} . Updated certs are present locally. Uploaded local certs to remote ssm")
               put_ssm_parameter()
               send_message_to_slack(f"REMOTE SSL Certificates expired by {renewal_length} . Updated certs are present locally. Uploaded local certs to remote ssm")

    except Exception as err:
        error_handler(sys.exc_info()[2].tb_lineno, err)

check_remote_expiry()
