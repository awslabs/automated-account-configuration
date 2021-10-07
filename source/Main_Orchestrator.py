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

# Initial point of execution. This lambda will download configurations stored on S3, parse the configurations
# and validate inputs then call into the appropriate step functions to execute API calls

import json
import sys
import boto3
import boto3.exceptions
import os
import random

# Import Lambda layer functions
from Utilities import(
    validate_config_input,
    read_configuration_value)

# Record solution usage
from botocore import config
solution_identifier = json.loads(os.environ['botoConfig'])
config = config.Config(**solution_identifier)


# Load configurations
try:
    # read current account ID
    CustToolsAcctId = boto3.client('sts').get_caller_identity()['Account']
    # build string for the step functions
    rfc_state_machine_arn=str("arn:aws:states:us-east-1:" +CustToolsAcctId + ":stateMachine:rfc-request-automation")
    sr_state_machine_arn= str("arn:aws:states:us-east-1:" +CustToolsAcctId + ":stateMachine:service-request-automation")
    customer_managed_backup_state_machine_arn= str("arn:aws:states:us-east-1:" +CustToolsAcctId + ":stateMachine:customer-managed-backup")
    customer_managed_patch_state_machine_arn= str("arn:aws:states:us-east-1:" +CustToolsAcctId + ":stateMachine:customer-managed-patch")

    # Read the S3 bucket name from environment variables. Value is set during solution deployment
    S3bucket = os.environ['Tools_Account_Conf_Bucket']
    key=os.environ['Tools_Account_Conf_Key']

    # Establish session in the local Lambda
    local_s3_session = boto3.session.Session()
    s3handler = local_s3_session.client('s3')
    data = s3handler.get_object(Bucket=S3bucket, Key=key)

except Exception as Configuration_load_error:
    print("Error loading configurations from the config file"+ str(Configuration_load_error))
    sys.exit("Configurations were not loaded successfully")

try:
    # Load the data from the S3 for the configuration file
    json_data = json.loads(data['Body'].read().decode('utf-8'))
    app_account_list = json_data['app_accounts']

except Exception as Json_Loading_Error:
    print("Error loading configurations from the config file" + " "+ str(Json_Loading_Error))
    sys.exit("Configurations file was loaded successfully")

#
def lambda_handler(evrent, context):
    # Loop through the list of accounts configured in the configuration file and
    # for each account get each account configs
    for app_account in app_account_list:
        for account_id in app_account:
            CustTempAcctConfig = app_account[str(account_id)]
            app_acct_role = CustTempAcctConfig['app_acct_role']
            # Validate input for account ID and account role
            IsValidAppAcctRoleInput = validate_config_input(app_acct_role,"^[A-Za-z0-9-:_/]{1,1000}$",1,1000)
            # Only proceed if the values are valid
            if IsValidAppAcctRoleInput== True:
                try:
                    # For each account get the AMS managed RFCs and SRs call into step functions
                    # to call into Lambda functions to execute the API calls
                    if CustToolsAcctId == account_id:
                        sys.exit("Cannot run inflation scripts on local account")
                    ams_ct_list = CustTempAcctConfig['ams_managed_list']
                    # Check if AWS managed services has a configuration
                    if len(ams_ct_list) > 0:
                        process_ct_list(ams_ct_list,account_id,app_acct_role)
                    else:
                        print('AMS change list is empty')
                except Exception as process_ct_list_failure:
                    print(str(process_ct_list_failure))

                try:
                    if CustToolsAcctId == account_id:
                        sys.exit("Cannot run inflation scripts on local account")
                    customer_change_list = CustTempAcctConfig['customer_managed_list']
                    # Check if customer managed account list has any configurations
                    if len(customer_change_list) > 0:
                        process_ct_list(customer_change_list, account_id,app_acct_role)
                    else:
                        print ('Customer change list is empty' )
                except Exception as process_ct_list_failure:
                    print(str(process_ct_list_failure))
            else:
                sys.exit("Role value" + " " + str(app_acct_role) + "is not valid a input" + str(IsValidAppAcctRoleInput ))

def process_ct_list(ctlistjson,appaccountid,appacctrole):
     # Check if the step function ARN values are valid values
    IsValidRfcSm = validate_config_input(rfc_state_machine_arn,"^[A-Za-z0-9-:_]{1,1000}$",1,1000)
    IsValidSrSm = validate_config_input(sr_state_machine_arn,"^[A-Za-z0-9-:_]{1,1000}$",1,1000)
    IsValidCMBackUpSm = validate_config_input(customer_managed_backup_state_machine_arn,"^[A-Za-z0-9-:_]{1,1000}$",1,1000)
    IsValidCMPatchSm = validate_config_input(customer_managed_patch_state_machine_arn,"^[A-Za-z0-9-:_]{1,1000}$",1,1000)

    # Only proceed if the values are valid
    if IsValidRfcSm==False or IsValidSrSm==False or IsValidCMBackUpSm==False or IsValidCMPatchSm==False :
        sys.exit("State machine ARNs or role values are not valid inputs")
    else:
        #  Go through each requested change, AMS or customer managed and then make a call to the step
        #  function required to make the lambda calls.
        #  For RFC next call is Create_RFC.py, for ServiceRequests Create_SR.py and so on.
        try:
            for ct in ctlistjson:
                ChangeType = (ct['Key'])
                pause_time = (ct['Wait_Time'])
                exec_params = (ct['Exec_Params'])
                # Validate input
                IsValild_keyChangeType = validate_config_input(ChangeType,"^[A-Za-z0-9-:_]{1,1000}$",1,1000)
                IsValidPauseTime = validate_config_input(str(pause_time),"^[0-9]{1,1000}$",1,1000)

                if IsValild_keyChangeType==False or IsValidPauseTime==False:
                    sys.exit("Change type, Pause time or exec param values are not valid inputs")
                if ChangeType =="ct-2hyozbpa0sx0m":
                    process_step_function(rfc_state_machine_arn,"ct-2hyozbpa0sx0m",pause_time,appaccountid,exec_params,appacctrole)
                elif ChangeType == "ct-0el2j07llrxs7":
                    process_step_function(rfc_state_machine_arn,"ct-0el2j07llrxs7",pause_time,appaccountid,exec_params,appacctrole)
                elif ChangeType == "Service_Request":
                    process_step_function(sr_state_machine_arn,"Service_Request",pause_time,appaccountid,exec_params,appacctrole)
                elif ChangeType == "backup":
                    process_step_function(customer_managed_backup_state_machine_arn,"Base_AWS_BackUp",pause_time,appaccountid,exec_params,appacctrole)
                elif ChangeType == "patch":
                    process_step_function(customer_managed_patch_state_machine_arn,"Base_AWS_Patch",pause_time,appaccountid,exec_params,appacctrole)
                else:
                    print("Unknown_Change_Type")
        except Exception as ct_list_step_function_error:
            print("Error while trying to call step functions" + " " + str(ct_list_step_function_error))
        else:
            print('Launched operational baseline successfully' )


def process_step_function(StateMachineArn,AmsChangeTypeId,pausetime,appaccountid,exec_params,app_acct_role):
    try:
        # assign a random number to the step function execution to allow for multiple calls
        exec_random_string= random.randint(0, 100000)
        local_stepfunction_session = boto3.session.Session()
        client = local_stepfunction_session.client('stepfunctions')
        # initialize the execution of the step function
        response = client.start_execution(
            stateMachineArn=str(StateMachineArn),
            name=AmsChangeTypeId +"_"+ str(exec_random_string),
            input= str("{\"wait_time\":" + str(pausetime) + ",\"change_type_id\":" + "\""+ AmsChangeTypeId + "\",\"app_account_id\":" + "\""+ appaccountid + "\",\"exec_params\":" + "\""+ exec_params  + "\",\"app_acct_role\":" + "\""+ app_acct_role +"\""+ "}")
        )
        return (str(response))
    except Exception as step_function_failure:
        print("Failed to execute step function for" + StateMachineArn + " " + str(step_function_failure))