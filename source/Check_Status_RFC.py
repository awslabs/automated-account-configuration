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

# This lambda function makes a call into AWS Managed Services Request for Change and returns a status back
# to the step function

import os
import sys
# Load AWS Managed Services models. These models are required to allow for AMS RFC and SR calls
os.environ['AWS_DATA_PATH'] = './models'

# Load Lambda layer functions
from get_auth import (
    get_session_with_arn,
    get_session
)

# External ID is passed in the STS  to allow for cross account assume role. This value is set in the
# Cloudformation creating the solution
ExternalId = os.environ['External_id']

# Lambda is called from Step function and passed values to allow it to check on a unique RFC status
def lambda_handler(event, context):
    # parse values passed to the function from the step function
    try:
        ams_app_id= event['app_account_id']
        app_acct_role = event['app_acct_role']
        member_account_session = get_session(
            str(ams_app_id), str(app_acct_role), "check_rfc_status", ExternalId
        )
    except Exception as RFC_Load_Error:
        print("Error loading configurations passed by the step function" + " "+ str(RFC_Load_Error))
        sys.exit("Configurations were not loaded successfully")

    try:
        # get a session in the destination account
        cm = member_account_session.client("amscm")
        # get the RFC ID
        rfcIdtemp = event['rfcId']
        RFC_Status_Code=cm.get_rfc(RfcId=rfcIdtemp)
        RFC_Status = (RFC_Status_Code['Rfc']['Status']['Name'])
        RFC_Mode = (RFC_Status_Code['Rfc']['AutomationStatus']['Id'])
        # Check status of the RFC and return back to the Step function
        if RFC_Status == "Success":
            jobStatus  = "SUCCEEDED"
        elif RFC_Status =="PendingApproval":
            # Check if this is a manual RFC like MOO
            if RFC_Mode == "Manual":
                jobStatus ="MANUAL"
            else:
                jobStatus  = "IN PROGRESS"
        elif RFC_Status =="InProgress":
            jobStatus  = "IN PROGRESS"
        elif RFC_Status in ("Failure","Rejected"):
            jobStatus = "FAILED"
        else:
            RFC_Status_Code=cm.get_rfc(RfcId=rfcIdtemp)
            RFC_Status = (RFC_Status_Code['Rfc']['Status']['Name'])
            jobStatus=RFC_Status
        return jobStatus

    except Exception as AMS_Check_Error:
        print("Error getting RFC status" + " "+ str(AMS_Check_Error))
