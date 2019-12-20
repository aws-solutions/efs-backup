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

import logging
import uuid
import json
import boto3

from urllib import request
from datetime import datetime

log = logging.getLogger()
log.setLevel(logging.INFO)

# Send anonymous metric function
def send_anonymous_metric(solution_id, solution_version, solution_uuid, region, event_type, request_type):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    metric_url = 'https://metrics.awssolutionsbuilder.com/generic'
    response_body = json.dumps({
        "Solution": solution_id,
        "UUID": solution_uuid,
        "TimeStamp": now,
        "Data": {
            "Launch": now,
            "Region": region,
            "Version": solution_version,
            "EventType": event_type,
            "RequestType": request_type
        }
    })
    log.info('Metric Body: {}'.format(response_body))

    try:
        data = response_body.encode('utf-8')
        req = request.Request(metric_url, data=data)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', len(response_body))
        response = request.urlopen(req)

        log.info('Status code: {}'.format(response.getcode()))
        log.info('Status message: {}'.format(response.msg))
    except Exception as e:
        log.error('Error occurred while sending metric: {}'.format(json.dumps(response_body)))
        log.error('Error: {}'.format(e))

# Send response function
def send_response(event, context, response_status, response_data):
    try:
        response_body = json.dumps({
            "Status": response_status,
            "Reason": 'See the details in CloudWatch Log Stream: {}'.format(context.log_stream_name),
            "PhysicalResourceId": context.log_stream_name,
            "StackId": event['StackId'],
            "RequestId": event['RequestId'],
            "LogicalResourceId": event['LogicalResourceId'],
            "Data": response_data
        })

        log.info('Response URL: {}'.format(event['ResponseURL']))
        log.info('Response Body: {}'.format(response_body))

        data = response_body.encode('utf-8')
        req = request.Request(event['ResponseURL'], data=data, method='PUT')
        req.add_header('Content-Type', '')
        req.add_header('Content-Length', len(response_body))
        response = request.urlopen(req)

        log.info('Status code: {}'.format(response.getcode()))
        log.info('Status message: {}'.format(response.msg))
    except Exception as e:
        log.error('Custom resource send_response error: {}'.format(e))

def lambda_handler(event, context):
    log.info('Received event: {}'.format(json.dumps(event)))
    response_data = {
        "Message": "No action is needed."
    }
    properties = event['ResourceProperties']

    try:
        if event['RequestType'] in ['Create', 'Update']:
            response_data = {
                "UUID": str(uuid.uuid4())
            }

        if event['ResourceType'] == 'Custom::SendAnonymousMetrics' and properties['SendAnonymousMetrics'] == 'Yes':
            solution_id = properties['SolutionId']
            solution_version = properties['SolutionVersion']
            solution_uuid = properties['SolutionUuid']
            region = properties['Region']
            event_type = properties['EventType']
            send_anonymous_metric(solution_id, solution_version, solution_uuid, region, event_type, event['RequestType'])
            response_data = {
                "Message": "Sent anonymous metric"
            }

        send_response(event, context, 'SUCCESS', response_data)
    except Exception as e:
        log.error('Error: {}'.format(e))
        response_data = {
            'Error': e
        }
        send_response(event, context, 'FAILED', response_data)
