######################################################################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
#                                                                                                                    #
#  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance        #
#  with the License. A copy of the License is located at                                                             #
#                                                                                                                    #
#      http://aws.amazon.com/asl/                                                                                    #
#                                                                                                                    #
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES #
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    #
#  and limitations under the License.                                                                                #
######################################################################################################################

import boto3


class EFS(object):

    def __init__(self, logger):
        self.logger = logger

    def size(self, efs_id):
        # Check the EFS size
        try:
            client = boto3.client('efs')
            self.logger.debug('Checking EFS Size')
            response = client.describe_file_systems(
                MaxItems=2,
                FileSystemId=efs_id
            )
            return (response['FileSystems'][0]['SizeInBytes']['Value'])
        except Exception as e:
            self.logger.error("unhandled exception: EFS_size", exc_info=1)
            return 'unhandled exception'

    def performance_mode(self, efs_id):
        # Check the EFS performance mode
        try:
            client = boto3.client('efs')
            self.logger.debug('Checking EFS Performance Mode')
            response = client.describe_file_systems(
                MaxItems=2,
                FileSystemId=efs_id
            )
            return (response['FileSystems'][0]['PerformanceMode'])
        except Exception as e:
            self.logger.error("unhandled exception: EFS_performance_mode", exc_info=1)
            return 'unhandled exception'
