######################################################################################################################
#  Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
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

import json
from datetime import datetime
from urllib2 import Request
from urllib2 import urlopen
import boto3
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class Notify(object):
    def __init__(self, logger):
        self.logger = logger

    # API call to notify the customer
    def customer(self, arn, message):
        try:
            sns_client = boto3.resource('sns')
            topic = sns_client.Topic(arn)
            response = topic.publish(
                Subject='EFS Backup Status',
                Message=json.dumps(message, indent=4, cls=DecimalEncoder, sort_keys=True),
            )
            self.logger.info('SNS Publish Response')
            self.logger.info(response)
            return response
        except Exception as e:
            self.logger.error("unhandled exception: Notify_customer", exc_info=1)

    # Send anonymous metrics
    def metrics(self, solution_id, uuid, data, url):
        try:
            time_stamp = {'TimeStamp': str(datetime.utcnow().isoformat())}
            params = {'Solution': solution_id,
                      'UUID': uuid,
                      'Data': data}
            metrics = dict(time_stamp, **params)
            json_data = json.dumps(metrics, indent=4, cls=DecimalEncoder, sort_keys=True)
            headers = {'content-type': 'application/json'}
            req = Request(url, json_data, headers)
            rsp = urlopen(req)
            content = rsp.read()
            rsp_code = rsp.getcode()
            self.logger.info('Response Code: {}'.format(rsp_code))
            self.logger.debug('Response Code: {}'.format(content))
            return rsp_code
        except Exception as e:
            self.logger.error("unhandled exception: Notify_metrics", exc_info=1)





