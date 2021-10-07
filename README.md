# automated-account-configuration
The Automated account configuration is a sample solution to enable operational scale for AWS customers by automating repeatable
steps required before AWS accounts are used for customer workloads. Steps include setting up backups and patching for the 
resources within the account. 

## Disclaimer
This solution collects anonymous operational metrics to help AWS improve the quality of features of the solution. For more information, including how to disable this capability, please see the [implementation guide](https://docs.aws.amazon.com/solutions/latest/<solution-trademark-name>/collection-of-operational-metrics.html).

## File Structure

```
|-deployment/
  |-build-s3-dist.sh                                              [ shell script for packaging distribution assets ]
  |-run-unit-tests.sh                                             [ shell script for executing unit tests ]
  |-automated-account-configuration.template                      [ solution CloudFormation deployment template to deploy S3 and IAM Roe ]
  |-automated-account-configuration-step-2.template               [ solution CloudFormation deployment template to deploy tools account policies, Lambda functions and step functions]
  |-automated-account-configuration-step-3.template               [ solution CloudFormation deployment template to deploy tools account IAM role into the application account]
  |-automated-account-configuration-step-4.template               [ solution CloudFormation deployment template to setup trust into the tools accounts]
|-source/
  |-deployment_packages                                           [ Folder containing Lambda function packages ]
  |-models                                                        [ Folder containing AMS service models to enable RFC creation ]
  |-python                                                        [ Folder containing Lambda layer files and functions ]
    | - get_auth.py                                               [ Functions to obtain credentials from the application acount IAM role ]
    | - Utilities.py                                              [ Utility functions to read configurations ]
  |-S3_Files                                                      [ Folder containing multiple subfolders for the solution configuration and source code for lambda functions ]
    | - Account_Configuration                                     [ Folder containing configuration file for the solution to run ]
        | - Account_Config.json                                   [ File containing all the configurtions for the solution ]
    | - functions                                                 [ Folder containing Lambda function code including layer and necessary models ]     
    | - JSON_Template                                             [ Folder containing input to the backup, patch used by Lambda functions in the solution, for more details about AMS CT types please visit https://console.aws.amazon.com/managedservices/docs/managedservices/latest/ctref/what-are-change-types.html]    
  |-Main_Orchestrator.py                                          [ Lambda that acts as the initial point of execution of the solution]
  |-Check_Status_RFC.py                                           [ Lambda function to check the status of an AMS Request For Change ]
  |-Config.ini                                                    [ Configuration file storing values used by Lambda functions ]
  |-Create_RFC.py                                                 [ Lambda function to create AMS Request For Change ]
  |-Create_SR.py                                                  [ Lambda function to create AMS Service Request ]
  |-customer_managed_backup.py                                    [ Lambda function to create a native AWS Backup Plan and vault ]
  |-customer_managed_patch.py                                     [ Lambda function to create a native AWS default patch window]
```

Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the the MIT-0 License. See the LICENSE file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
