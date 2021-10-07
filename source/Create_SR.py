#########################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.                    #
# SPDX-License-Identifier: MIT-0                                                        #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy of this  #
# software and associated documentation files (the "Software"), to deal in the Software #
# without restriction, including without limitation the rights to use, copy, modify,    #
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to    #
# permit persons to whom the Software is furnished to do so.                            #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,   #
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A         #
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT    #
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION     #
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE        #
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                #
#########################################################################################
import boto3
import json
import sys
import os
import logging
from botocore.exceptions import ClientError, BotoCoreError

# AMS RFCs are referenced as a part of the lambda zip file
os.environ['AWS_DATA_PATH'] = './models'

from botocore import config
solution_identifier = json.loads(os.environ['botoConfig'])
config = config.Config(**solution_identifier)

# import from lambda layer
from get_auth import (
    get_session_with_arn,
    get_session
)
from Utilities import(
    validate_config_input,
    read_configuration_value)

try:
    # Download the initial configuration JSON file for the account, these values are set when creating temp.yaml
    CustToolsAcctId = boto3.client('sts').get_caller_identity()['Account']
    S3bucket = os.environ['Tools_Account_Conf_Bucket']
    key=os.environ['Tools_Account_Conf_Key']
    templateS3Key = os.environ['Json_Template_S3_Key']
    ExternalId = os.environ['External_id']

    # Establish session in the local Lambda
    local_s3_session = boto3.session.Session()
    s3handler = local_s3_session.client('s3')
    data = s3handler.get_object(Bucket=S3bucket, Key=key)

except Exception as Configuration_load_error:
    print("Error loading configurations from the config file"+ str(Configuration_load_error))
    sys.exit("Configurations were not loaded successfully")

def lambda_handler(event, context):
    try:
        # Parse the Lambda event JSON and get values needed for the creation of the SR
        ams_ct_id= event['change_type_id']
        ams_app_id= event['app_account_id']
        local_exec_params = event['exec_params']
        app_acct_role = event['app_acct_role']

    except Exception as missing_lambda_input:
        return(str(missing_lambda_input))


    if ams_ct_id == "Service_Request":
        #load the inputs for the SR from the local S3
        local_s3_session = boto3.session.Session()
        s3handler = local_s3_session.client('s3')
        bucket = S3bucket
        key  = templateS3Key + local_exec_params
        data = s3handler.get_object(Bucket=bucket, Key=key)
        # Load the SR exec params
        SRExecParams  = json.loads(data['Body'].read().decode('utf-8'))
        # Get a session in the destination account
        try:
            member_account_session = get_session(
                str(ams_app_id), str(app_acct_role), "create_sr",ExternalId
            )
        except (BotoCoreError, ClientError) as e:
            print("error getting session")
            logging.error(
            "get_session_with_arn() failed trying to assume role \
               due to clienterror or botocore error",
        )
        # Create an SR in the destination account
        try:
            supporthandler = member_account_session.client("support")
            print(supporthandler)
            response = supporthandler.create_case(
                subject=SRExecParams['subject'],
                serviceCode=SRExecParams['serviceCode'],
                severityCode=SRExecParams['severityCode'],
                categoryCode=SRExecParams['categoryCode'],
                communicationBody=SRExecParams['communicationBody'],
                ccEmailAddresses=[SRExecParams['ccEmailAddresses']]
            )
            NewCaseId = response['caseId']
            return {'caseId': NewCaseId}
        except Exception as create_sr_failure:
            return (str(create_sr_failure))

    else:
        return("Unknow_Request")