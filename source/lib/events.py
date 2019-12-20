###################################################################################
#  Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                                 #
#  Licensed under the Apache License, Version 2.0 (the "License").                #
#  You may not use this file except in compliance with the License.               #
#  A copy of the License is located at                                            #
#                                                                                 #
#      http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                                 #
#  or in the "license" file accompanying this file. This file is distributed      #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either      #
#  express or implied. See the License for the specific language governing        #
#  permissions and limitations under the License.                                 #
###################################################################################

import boto3
from json import dumps, loads, JSONEncoder
from datetime import datetime, date

cwe_client = boto3.client('events')
lambda_client = boto3.client('lambda')


class DateTimeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            serial = o.isoformat()
            return serial
        raise TypeError("Type %s not serializable" % type(o))


class CloudWatchEvent(object):
    def __init__(self, logger, uid):
        self.logger = logger
        self.rule_name = 'stop_backup' + '_' + uid
        self.target_id = 'terminate_event_orchestrator'

    # API call to get backup id from the stop CWE
    def describe_target(self):
        try:
            response = cwe_client.list_targets_by_rule(
                Rule=self.rule_name
            )
            return loads(response['Targets'][-1]['Input'])['backup_id']
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_describe_target", exc_info=1)

    # API call to create the CWE that stops the backup
    def create_event(self, minutes):
        try:
            time_to_run_ssm_command = 15  # minutes
            time = int(minutes) - time_to_run_ssm_command  # subtracting time from the backup window
            backup_window = 'rate(' + str(time) + ' minutes)'
            response = cwe_client.put_rule(
                Name=self.rule_name,
                ScheduleExpression=backup_window,
                State='ENABLED',
                Description='EFS Backup Solution: CloudWatch Event created by Lambda to stop the backup instance',
            )
            return response['RuleArn']
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_create_event", exc_info=1)

    # API call to obtain name of the lambda function
    def get_lambda_arn(self, lambda_function_name):
        try:
            response = lambda_client.get_function(
                FunctionName=lambda_function_name
            )
            return response['Configuration']['FunctionArn']
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_get_lambda_arn", exc_info=1)

    # CloudWatch API call to add the Orchestrator lambda function as the target
    def add_target(self, lambda_function_name, event):
        try:
            json_event = dumps(event, indent=4, cls=DateTimeEncoder)
            response = cwe_client.put_targets(
                Rule=self.rule_name,
                Targets=[
                    {
                        'Id': self.target_id,
                        'Arn': self.get_lambda_arn(lambda_function_name),
                        'Input': json_event
                    },
                ]
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_add_target", exc_info=1)

    # Lambda API call to add the permission for CWE to invoke Orchestrator lambda function
    def add_permission(self, lambda_function_name, event_rule_arn):
        try:
            response = lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId='stop_backup_event',
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=event_rule_arn
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_add_permission", exc_info=1)

    # API call to delete the CWE that stops the backup
    def delete_event(self):
        try:
            response = cwe_client.delete_rule(
                Name=self.rule_name
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_delete_event", exc_info=1)

    # CloudWatch API call to delete the Orchestrator lambda function as the target
    def remove_target(self):
        try:
            response = cwe_client.remove_targets(
                Rule=self.rule_name,
                Ids=[
                    self.target_id
                ]
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_remove_target", exc_info=1)

    # Lambda API call to remove the permission for CWE to invoke Orchestrator lambda function
    def remove_permission(self, lambda_function_name):
        try:
            response = lambda_client.remove_permission(
                FunctionName=lambda_function_name,
                StatementId='stop_backup_event'
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchEvent_remove_permission", exc_info=1)
