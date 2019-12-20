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

#!/bin/python

from lib.dynamodb import DDB
from lib.efs import EFS
from lib.notify import Notify
from lib.cloudwatch import CloudWatchMetric
from lib.events import CloudWatchEvent
from lib.logger import Logger
from lib.ssm import SimpleSystemsManager
from lib.asg import AutoScaling
from uuid import uuid4
from datetime import datetime, timedelta
import os

log_level = 'info'
logger = Logger(loglevel=log_level)


# Instantiate dictionaries
ddb_item = {}
replace_dict = {}
notification_message = {}


# Global Variables
ddb_table_name = os.environ['table_name']
backup_id = str(uuid4())[:8]
sns_topic_arn = os.environ['topic_arn']
source_efs_id = os.environ['source_efs']
destination_efs_id = os.environ['destination_efs']
s3_bucket = os.environ['s3_bucket']
backup_window_period = os.environ['backup_window_period']
folder_label = os.environ['folder_label']
retain_period = os.environ['backup_retention_copies']
lambda_function_name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
region = os.environ['AWS_REGION']
customer_uuid = os.environ['uuid']
backup_prefix = os.environ['backup_prefix']
instance_type = os.environ['instance_type']
item_time_to_live_days = 90
send_data = os.environ['send_anonymous_data']
notify_customer = os.environ['notification_on_success']
interval_tag = os.environ['interval_tag']
destination_efs_mode = os.environ['efs_mode']
backup_asg = os.environ['autoscaling_group_name']

solution_id = 'SO0031'
metrics_url = 'https://metrics.awssolutionsbuilder.com/generic'


# Time conversion to epoch for DDB TTL Attribute
def set_item_time_to_live():
    expire_time = datetime.now() + timedelta(days=item_time_to_live_days)  # Default is 30 days
    ttl = expire_time.strftime('%s')
    return ttl


# Custom event constant that invokes lambda function to stop the backup
def terminate_event():
    terminate_instance_event = {
        'mode': 'backup',
        'action': 'stop',
        'backup_id': backup_id,
        'time_stamp': datetime.now()
    }
    return terminate_instance_event


# Condition to check if STOP event was triggered during CloudWatch Event creation
def validate_stop_event(e):
    now = datetime.now()
    time_stamp = e.get('time_stamp')
    fixed_time = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%S.%f') + timedelta(minutes=10)
    if now > fixed_time:
        return True
    else:
        return False

# Main Lambda function to catch different CW Rules
def lambda_handler(event, context):
    logger.debug('Lambda Event')
    logger.debug(event)

    # Event triggered when AutoScaling updated from 1 to 0 desired capacity
    if event.get('detail', {}).get('LifecycleTransition') == 'autoscaling:EC2_INSTANCE_TERMINATING':
        logger.info("ASG Event: Instance Terminating")
        # Instantiate Custom classes
        cwe = CloudWatchEvent(logger, customer_uuid[:8])
        ssm = SimpleSystemsManager(logger)

        b_id = cwe.describe_target()  # Retrieve unique backup id from cwe target
        hook_name = event['detail']['LifecycleHookName']
        asg_name = event['detail']['AutoScalingGroupName']
        instance_id = event['detail']['EC2InstanceId']
        document_name = "AWS-RunShellScript"
        replace_dict.update({'${_s3bucket}': s3_bucket})
        replace_dict.update({'${_interval}': interval_tag})
        replace_dict.update({'${_ddb_table_name}': ddb_table_name})
        replace_dict.update({'${_backup_id}': b_id})
        replace_dict.update({'${_autoscaling_grp_name}': asg_name})
        replace_dict.update({'${_lifecycle_hookname}': hook_name})
        replace_dict.update({'${_folder_label}': folder_label})
        replace_dict.update({'${_source_efs}': source_efs_id})

        # Send message to SSM
        ssm.send_command(instance_id, document_name, replace_dict)

    # Event triggered when lifecycle hook on instance completes
    elif event.get('detail-type') == 'EC2 Instance Terminate Successful':
        logger.info("ASG Event: EC2 Instance Terminate Successful")
        # Instantiate Custom classes
        cwe = CloudWatchEvent(logger, customer_uuid[:8])
        notify = Notify(logger)
        ddb = DDB(logger, ddb_table_name)

        b_id = cwe.describe_target()
        data = ddb.read_item('BackupId', b_id)

        # Create SNS notification message
        if data is not None:
            if data.get('BackupStatus') == 'Incomplete':
                data.update({'Message': 'The EFS backup was incomplete. Either backup window expired before full backup or fpsync process was not completed.'})
                notify.customer(sns_topic_arn, data)
            elif data.get('BackupStatus') == 'Unsuccessful':
                data.update({'Message': 'The EFS backup was unsuccessful. '
                                        'The EC2 instance was unable to find the mount IP OR mount EFS'})
                notify.customer(sns_topic_arn, data)
            elif data.get('BackupStatus') == "fpsync failed":
                data.update({'Message': 'fpsync process in backup script failed or did not start'})
                notify.customer(sns_topic_arn, data)
            elif data.get('BackupStatus') == "Rsync Delete Incomplete":
                data.update({'Message': 'rsync --delete process could not complete'})
                notify.customer(sns_topic_arn, data)
            elif data.get('BackupStatus') is None:
                data.update({'Message': 'The SSM script could not update the DynamoDB table with backup status, '
                                        'please check the logs in the S3 bucket for the details.'})
                data.update({'BackupStatus': 'Unknown'})
                notify.customer(sns_topic_arn, data)
            else:
                if notify_customer.lower() == 'yes':
                    data.update({'Message': 'The EFS was backed up successfully'})
                    notify.customer(sns_topic_arn, data)
        else:
            notification_message.update({'Message': 'Could not find the backup id: {} in the DDB table'.format(b_id)})
            notify.customer(sns_topic_arn, notification_message)

        # Send anonymous notification
        if send_data.lower() == 'yes':
            customer_data = ['SourceEfsId', 'DestinationEfsId', 'BackupPrefix', 'ExpireItem', 'Message']
            for key in customer_data:
                data.pop(key, None)
            data.update({'Region': region})
            notify.metrics(solution_id, customer_uuid, data, metrics_url)

        # Delete CWE
        cwe.remove_target()
        cwe.delete_event()
        cwe.remove_permission(lambda_function_name)

    else:
        # Event to Start Backup
        if event.get('mode') == 'backup' and event.get('action') == 'start':
            logger.info("Starting Backup")
            # Instantiate Custom classes
            ddb = DDB(logger, ddb_table_name)
            cw = CloudWatchMetric(logger)
            efs = EFS(logger)
            cwe = CloudWatchEvent(logger, customer_uuid[:8])
            asg = AutoScaling(logger, backup_asg)

            # Change the ASG desired capacity
            asg.update_asg('start_instance')

            # Creating DDB Item (dict)
            efs_cw_metrics = cw.efs_cw_metrics(source_efs_id, 'Source')
            ddb_item.update({'BackupId': backup_id})
            ddb_item.update({'BackupWindow': backup_window_period})
            ddb_item.update({'IntervalTag': interval_tag})
            ddb_item.update({'RetainPeriod': retain_period})
            ddb_item.update({'ExpireItem': set_item_time_to_live()})
            ddb_item.update({'S3BucketSize': cw.s3_cw_metrics(s3_bucket)})
            ddb_item.update({'SourceEfsSize': efs.size(source_efs_id)})
            ddb_item.update({'SourceEfsId': source_efs_id})
            ddb_item.update({'DestinationEfsId': destination_efs_id})
            ddb_item.update({'BackupPrefix': backup_prefix})
            ddb_item.update({'DestinationEfsSize': efs.size(destination_efs_id)})
            ddb_item.update({'SourcePerformanceMode': efs.performance_mode(source_efs_id)})
            ddb_item.update({'InstanceType': instance_type})
            ddb_item.update({'DestinationPerformanceMode': destination_efs_mode})
            ddb_item.update({'BackupStartTime': (datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))})
            item = dict(ddb_item, **efs_cw_metrics)  # Merging two dictionaries

            # Put DDB item
            ddb.write_item(item)

            # Create CWE to update desired capacity in ASG
            event_rule_arn = cwe.create_event(backup_window_period)
            cwe.add_target(lambda_function_name, terminate_event())
            cwe.add_permission(lambda_function_name, event_rule_arn)

        # Event to Stop Backup
        elif event.get('mode') == 'backup' and event.get('action') == 'stop' and \
                validate_stop_event(event):
            logger.info("Stopping Backup")
            # Instantiate Custom classes
            asg = AutoScaling(logger, backup_asg)

            # Change the ASG desired capacity
            asg.update_asg('stop_instance')

        else:
            if not validate_stop_event(event):
                # If stop event triggered lambda during CloudWatch event creation, it should be ignored
                logger.info('Ignoring STOP backup event occurring within 10 minutes of the START backup event.')
            else:
                logger.error('Invalid Event. No action taken.')
