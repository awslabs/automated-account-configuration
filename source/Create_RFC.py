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
    # create service client using the assumed role credentials
    # Process received CT list from the step function in the lambda event. The passed list is in JSON format
    try:
        ams_app_id= event['app_account_id']
        app_acct_role = event['app_acct_role']
        ams_ct_id= event['change_type_id']
        local_exec_params = event['exec_params']

    except Exception as ct_id_failure:
        return(str(ct_id_failure))
    if ams_ct_id == "ct-2hyozbpa0sx0m":
        try:
            # If the requested CT is a backup Plan
            local_s3_session = boto3.session.Session()
            s3handler = local_s3_session.client('s3')
            bucket = S3bucket
            key = templateS3Key + local_exec_params
            data = s3handler.get_object(Bucket=bucket, Key=key)
            RFCExecParams  = json.loads(data['Body'].read().decode('utf-8'))

        except Exception as s3_load_failre:
            return(str(s3_load_failre))
        # Get a session in the destination account or where the RFC will be created. This is a call to lambda layer function
        # that returns the aws key, secret key and session from the destination account
        try:
            member_account_session = get_session(
                str(ams_app_id), str(app_acct_role), "create_rfc",ExternalId
            )
        except (BotoCoreError, ClientError) as e:
            print("error getting session")
            logging.error(
                "get_session_with_arn() failed trying to assume role \
                   due to clienterror or botocore error",
            )
        try:
            # Initialize the AMS API
            rfc_handler = member_account_session.client("amscm")
            # Pass the RFC inputs, these inputs can also be read from a JSPN
            cts = rfc_handler.create_rfc \
                (ChangeTypeId="ct-2hyozbpa0sx0m",
                 ChangeTypeVersion="2.0",
                 Title="Creating backup Plan",
                 ExecutionParameters=json.dumps(RFCExecParams)
                 )
            # Get the RFC ID just created
            NewRfcID = cts['RfcId']
            # Submit the RFC, this is a step in the AMS API flow
            rfc_handler.submit_rfc(RfcId=NewRfcID)
            return {'rfcId': NewRfcID,'app_account_id':ams_app_id,'app_acct_role':app_acct_role}
        except Exception as create_ams_backup_failure:
           return(str(create_ams_backup_failure))

    if ams_ct_id == "ct-0el2j07llrxs7":
        try:
            # If the requested CT is a patch baseline Plan
            local_s3_session = boto3.session.Session()
            s3handler = local_s3_session.client('s3')

            bucket = S3bucket
            key = templateS3Key + local_exec_params
            data = s3handler.get_object(Bucket=bucket, Key=key)
            RFCExecParams  = json.loads(data['Body'].read().decode('utf-8'))
            member_account_session = get_session(
                str(ams_app_id), str(app_acct_role), "created_rfc",ExternalId
            )
            cm = member_account_session.client("amscm")
            cts = cm.create_rfc \
                (ChangeTypeId="ct-0el2j07llrxs7",
                 ChangeTypeVersion="1.0",
                 Title="Creating patch Baseline",
                 ExecutionParameters=json.dumps(RFCExecParams)
                 )
            NewRfcID = cts['RfcId']
            RFC_Submit_Return=cm.submit_rfc(RfcId=NewRfcID)
            return {'rfcId': NewRfcID,'app_account_id':ams_app_id,'app_acct_role':app_acct_role}
        except Exception as create_ams_patch_failure:
            return(str(create_ams_patch_failure))