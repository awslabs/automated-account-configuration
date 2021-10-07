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

# import from lambda layer
from get_auth import (
    get_session
)
from Utilities import(
    read_configuration_value)

from botocore import config
solution_identifier = json.loads(os.environ['botoConfig'])
config = config.Config(**solution_identifier)

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
        patch_plan_id= event['change_type_id']
        ams_app_id= event['app_account_id']
        local_exec_params = event['exec_params']
        app_acct_role = event['app_acct_role']

        local_s3_session = boto3.session.Session()
        s3handler = local_s3_session.client('s3')
        bucket = S3bucket
        key= templateS3Key + local_exec_params
        PatchPlanData= s3handler.get_object(Bucket=bucket, Key=key)
        PatchBaseLineExecParams= json.loads(PatchPlanData['Body'].read().decode('utf-8'))
    except Exception as cust_patch_plan_input_failure:
        return (str(cust_patch_plan_input_failure))

    if patch_plan_id =="Base_AWS_Patch":
        try:
            member_account_session = get_session(
            str(ams_app_id), str(app_acct_role), "customer_managed_patch",ExternalId
            )

            cfhandler = member_account_session.client("ssm")
            patch_response = cfhandler.create_patch_baseline(
                OperatingSystem=PatchBaseLineExecParams['OperatingSystem'],
                Name=PatchBaseLineExecParams['Name'],
                GlobalFilters={
                    'PatchFilters': [
                        {
                            'Key': PatchBaseLineExecParams['GlobalFilters']['PatchFilters'][0]['Key'],
                            'Values': [
                                PatchBaseLineExecParams['GlobalFilters']['PatchFilters'][0]['Values'][0],
                            ]
                        },
                    ]
                },
                ApprovalRules={
                    'PatchRules': [
                        {
                            'PatchFilterGroup': {
                                'PatchFilters': [
                                    {
                                        'Key': PatchBaseLineExecParams['ApprovalRules']['PatchRules'][0]['PatchFilterGroup']['PatchFilters'][0]['Key'],
                                        'Values': [
                                            PatchBaseLineExecParams['ApprovalRules']['PatchRules'][0]['PatchFilterGroup']['PatchFilters'][0]['Values'][0],
                                        ]
                                    },
                                ]
                            },
                            'ComplianceLevel': PatchBaseLineExecParams['ApprovalRules']['PatchRules'][0]['ComplianceLevel'],
                            'ApproveUntilDate': PatchBaseLineExecParams['ApprovalRules']['PatchRules'][0]['ApproveUntilDate'],
                            'EnableNonSecurity':bool(PatchBaseLineExecParams['ApprovalRules']['PatchRules'][0]['EnableNonSecurity'])
                        },
                    ]
                }
            )
            BaseLineId = patch_response['BaselineId']
            return {'BaselineId': BaseLineId}

        except Exception as patch_plan_create_failure:
            print(str(patch_plan_create_failure))

    else:
        return('Unknown Request')
