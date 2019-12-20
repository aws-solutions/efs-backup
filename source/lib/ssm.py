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
import os
from datetime import date, datetime

from json import dumps, JSONEncoder

ssm_client = boto3.client("ssm")

class DateTimeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            serial = o.isoformat()
            return serial
        raise TypeError("Type %s not serializable" % type(o))

class SimpleSystemsManager(object):
    def __init__(self, logger):
        self.logger = logger

    # reading ssm.sh to send for run-command
    def create_command(self, replace_dict):
        try:
            lines=[]
            src_dir = os.path.dirname(os.path.abspath(__file__))
            self.logger.debug('Abs path: {}'.format(src_dir))
            f = 'ssm.sh'
            with open(os.path.join(src_dir, f)) as file:
                for line in file:
                    for src, target in replace_dict.items():
                        line = line.replace(src, target)
                    lines.append(line)
            return lines
        except Exception as e:
            self.logger.error("unhandled exception: SimpleSystemsManager_create_command", exc_info=1)

    # sending run-command        
    def send_command(self, instance_id, document_name, replace_dict):
        try:
            bucket_name = replace_dict.get('${_s3bucket}')
            self.logger.debug('SSM Bucket Name: {}'.format(bucket_name))
            response = ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName=document_name,
                TimeoutSeconds=120,
                OutputS3BucketName=bucket_name,
                OutputS3KeyPrefix='ssm-logs',
                Parameters={"commands": self.create_command(replace_dict)},
                Comment='EFS Backup Solution: Performs cleanup, '
                        'upload logs files to S3, updates DDB and lifecycle hook. '
            )
            self.logger.debug(dumps(response, indent=4, cls=DateTimeEncoder))
            return response
        except Exception as e:
            self.logger.error("unhandled exception: SimpleSystemsManager_send_command", exc_info=1)
            return 'unhandled exception'
