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

from pycfn_custom_resource.lambda_backed import CustomResource
import logging
import uuid
import json
import boto3

log = logging.getLogger()
log.setLevel(logging.INFO)

class SolutionHelperResource(CustomResource):
    def __init__(self, event):
        super(SolutionHelperResource, self).__init__(event)

    def generateId(self):
        try:
            # Value of CreateUniqueID does not matter
            log.info("Creating Unique ID")
            # Generate new random Unique ID
            newID = uuid.uuid4()

            response = {"Status": "SUCCESS", "UUID": str(newID)}
            log.debug("%s", response)

            # Results dict referenced by GetAtt in template
            return response

        except Exception as e:
            log.error("Exception: %s", e)
            return {"Status": "FAILED", "Reason": str(e)}

    def create(self):
        return self.generateId()

    def update(self):
        return self.generateId()

    def delete(self):
        # Nothing for delete to do--just return success.
        return {"Status": "SUCCESS" }

def lambda_handler(event, context):
    resource = SolutionHelperResource(event)
    resource.process_event()
    return {'message': 'done'}
