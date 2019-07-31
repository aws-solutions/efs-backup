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

from datetime import datetime, timedelta
import boto3
from decimal import Decimal


class CloudWatchMetric(object):
    def __init__(self, logger):
        self.logger = logger

    # CloudWatch API call to get EFS metrics
    def efs_cw_metrics(self, efs_id, name):
        try:
            cw_client = boto3.client('cloudwatch')
            cw_metrics = {}
            metrics = {
                'BurstCreditBalance': 'Average',
                'PermittedThroughput': 'Average'
            }
            now = datetime.utcnow()
            start_time = now - timedelta(seconds=300)
            end_time = min(now, start_time + timedelta(seconds=3600))  # 5 min window
            for metric in metrics:
                data = cw_client.get_metric_statistics(
                    Namespace='AWS/EFS',
                    MetricName=metric,
                    Dimensions=[{
                        'Name': 'FileSystemId',
                        'Value': efs_id}],
                    Period=300,
                    StartTime=start_time,
                    EndTime=end_time,
                    Statistics=[metrics[metric]])['Datapoints']
                for d in data:
                    key = name + metric
                    value = Decimal(d[metrics[metric]])
                    cw_metrics[key] = value
            return cw_metrics
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchMetric_efs_cw_metrics", exc_info=1)

    # CloudWatch API call to get S3 metrics
    def s3_cw_metrics(self, bucket_name):
        try:
            cw_client = boto3.client('cloudwatch')
            response = cw_client.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {
                        "Name": "BucketName",
                        "Value": bucket_name
                    },
                    {
                        "Name": "StorageType",
                        "Value": "StandardStorage"
                    }
                ],
                StartTime=datetime.now() - timedelta(days=1),
                EndTime=datetime.now(),
                Period=300,
                Statistics=['Average']
            )
            if not response['Datapoints']:
                self.logger.debug("S3 bucket size is zero. This is an empty bucket.")
                return '0'
            else:
                bucket_size_bytes = response['Datapoints'][-1]['Average']
                return Decimal(bucket_size_bytes)
        except Exception as e:
            self.logger.error("unhandled exception: CloudWatchMetric_s3_cw_metrics", exc_info=1)
