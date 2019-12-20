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

asg_client = boto3.client('autoscaling')

class AutoScaling(object):
    def __init__(self, logger, asg_name):
        self.logger = logger
        self.asg_name = asg_name

    # update ASG desired capacity    
    def update_asg(self, action):
        try:
            global desired_capacity
            if action == 'start_instance':
                desired_capacity = 1
            elif action == 'stop_instance':
                desired_capacity = 0
            self.logger.info("Changing desired capacity to {}".format(desired_capacity))
            response = asg_client.update_auto_scaling_group(
                AutoScalingGroupName=self.asg_name,
                DesiredCapacity=desired_capacity
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: AutoScaling_start_instance", exc_info=1)
            return 'unhandled exception'
