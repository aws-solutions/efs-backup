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

import boto3
from json import dumps, JSONEncoder
from decimal import Decimal

dynamodb_client = boto3.resource('dynamodb')

class DecimalEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class DDB(object):
    def __init__(self, logger, table_name):
        self.logger = logger
        self.table_name = table_name
        self.table = dynamodb_client.Table(self.table_name)

    # DDB API call to get an item
    def read_item(self, key, value):
        try:
            response = self.table.get_item(
                Key={
                    key: value
                }
            )
            item = response['Item']
            self.logger.info('DynamoDB Item')
            self.logger.info(dumps(item, indent=4, cls=DecimalEncoder))
            return item
        except Exception as e:
            self.logger.error("unhandled exception: DDB_read_item", exc_info=1)
            return 'unhandled exception get'

    # DDB API call to put an item
    def write_item(self, item):
        try:
            response = self.table.put_item(
                Item=item
            )
            return response
        except Exception as e:
            self.logger.error("unhandled exception: DDB_write_item", exc_info=1)
            return 'unhandled exception put'