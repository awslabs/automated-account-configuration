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
import logging
from botocore.exceptions import ClientError, BotoCoreError

def handle_session_name_length(session_name):
    return session_name

def get_session_with_arn(role_arn, session_name, external_id, base_session):
    if not base_session:
        base_session = boto3.Session()

    if not session_name:
        session_name = "aws_common_utils"

    session_name = handle_session_name_length(session_name)
    client = base_session.client("sts")

    try:
        response = client.assume_role(RoleArn=role_arn, RoleSessionName=session_name, ExternalId=external_id)
        access_key = response["Credentials"]["AccessKeyId"]
        secret = response["Credentials"]["SecretAccessKey"]
        session_token = response["Credentials"]["SessionToken"]

        return boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            aws_session_token=session_token,
        )
    except (BotoCoreError, ClientError) as e:
        logging.error(
            "get_session_with_arn() failed trying to assume %s \
                       due to clienterror or botocore error",
            role_arn,
        )
        logging.error(str(e))
        raise e

def get_session(account_id, role_name, session_name,external_id):
    print("entering get session function")

    temp_session = get_session_with_arn(
        "arn:aws:iam::{}:role/{}".format(account_id, role_name), session_name, external_id, None)
    return(temp_session)



