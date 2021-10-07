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

from botocore import config
solution_identifier = json.loads(os.environ['botoConfig'])
config = config.Config(**solution_identifier)

# AMS RFCs are referenced as a part of the lambda zip file
os.environ['AWS_DATA_PATH'] = './models'

# import from lambda layer
from get_auth import (
    get_session
)
from Utilities import(
    read_configuration_value)

try:
    # Download the initial configuration JSON file for the account, these values are set when creating temp.yaml
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

    # Get inputs from the lambda JSON inputs
    try:
        backup_plan_id= event['change_type_id']
        ams_app_id= event['app_account_id']
        local_exec_params = event['exec_params']
        app_acct_role = event['app_acct_role']

        if backup_plan_id =="Base_AWS_BackUp":
            # Location of the input files, these directories are set in temp.yaml
            local_s3_session = boto3.session.Session()
            s3handler = local_s3_session.client('s3')

            bucket = S3bucket
            key = templateS3Key + local_exec_params
            BackupPlanData = s3handler.get_object(Bucket=bucket, Key=key)
            BackUpExecParams  = json.loads(BackupPlanData['Body'].read().decode('utf-8'))
            ResourceTagKey = BackUpExecParams['Parameters']['ResourceTagKey']
            ResourceTagValue = BackUpExecParams['Parameters']['ResourceTagValue']
            BackupPlanName = BackUpExecParams['Parameters']['BackupPlanName']

    except Exception as cust_backup_plan_input_failure:
        return (str(cust_backup_plan_input_failure))

    try:

        member_account_session = get_session(str(ams_app_id), str(app_acct_role), "customer_managed_backup",ExternalId)
        VaultBackUpClient = member_account_session.client('backup')
        VaultBackUpClient.create_backup_vault(
            BackupVaultName=BackUpExecParams['Parameters']['BackupRule1Vault'],
        )
    except Exception as VaultException:
        return (str(VaultException))

    try:
        member_account_session = get_session(str(ams_app_id), str(app_acct_role), "customer_managed_backup",ExternalId)
        BackUpClient = member_account_session.client('backup')

        response = BackUpClient.create_backup_plan(
            BackupPlan={
                'BackupPlanName': BackUpExecParams['Parameters']['BackupPlanName'],
                'Rules': [
                    {
                        'RuleName': BackUpExecParams['Parameters']['BackupRule1Name'],
                        'TargetBackupVaultName': BackUpExecParams['Parameters']['BackupRule1Vault'],
                        'ScheduleExpression': BackUpExecParams['Parameters']['BackupRule1ScheduleExpression'],
                        'StartWindowMinutes': BackUpExecParams['Parameters']['BackupRule1StartWindowMinutes'],
                        'CompletionWindowMinutes': BackUpExecParams['Parameters']['BackupRule1CompletionWindowMinutes'],
                        'Lifecycle': {
                            'MoveToColdStorageAfterDays': BackUpExecParams['Parameters']['BackupRule1MoveToColdStorageAfterDays'],
                            'DeleteAfterDays': BackUpExecParams['Parameters']['BackupRule1DeleteAfterDays']
                        },
                    },
                ]
            },
            BackupPlanTags={
                BackUpExecParams['Parameters']['ResourceTagKey']:BackUpExecParams['Parameters']['ResourceTagValue']
            },
        )
        NewPlanId = response['BackupPlanId']
        BackUpClient.create_backup_selection(
            BackupPlanId=NewPlanId,
            BackupSelection={
                'SelectionName': BackupPlanName + '-tag-selection',
                'IamRoleArn': 'arn:aws:iam::' + ams_app_id + ':role/service-role/AWSBackupDefaultServiceRole',
                'ListOfTags': [
                    {
                        'ConditionType': 'STRINGEQUALS',
                        'ConditionKey': ResourceTagKey,
                        'ConditionValue': ResourceTagValue
                    },
                ]
             }
            )

        return {'planId': NewPlanId}
    except Exception as backup_plan_create_failure:
        return (str(backup_plan_create_failure))