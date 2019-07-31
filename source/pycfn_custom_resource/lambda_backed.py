# Changes from original pycfn_custom_resource:
#
#   Changed/updated a couple of imports.
#
#   Removed unused exception variable

from . import util
from botocore.vendored import requests
import json
import uuid
import sys
import traceback

import logging
log = logging.getLogger()
log.addHandler(logging.NullHandler())
log.setLevel(logging.DEBUG)


_DEFAULT_CREATE_TIMEOUT = 30 * 60
_DEFAULT_DELETE_TIMEOUT = 30 * 60
_DEFAULT_UPDATE_TIMEOUT = 30 * 60


class CustomResource(object):
    def __init__(self, event):
        self._event = event
        self._logicalresourceid = event.get("LogicalResourceId")
        self._physicalresourceid = event.get("PhysicalResourceId")
        self._requestid = event.get("RequestId")
        self._resourceproperties = event.get("ResourceProperties")
        self._resourcetype = event.get("ResourceType")
        self._responseurl = event.get("ResponseURL")
        self._requesttype = event.get("RequestType")
        self._servicetoken = event.get("ServiceToken")
        self._stackid = event.get("StackId")
        self._region = self._get_region()
        self.result_text = None
        self.result_attributes = None

        # Set timeout for actions
        self._create_timeout = _DEFAULT_CREATE_TIMEOUT
        self._delete_timeout = _DEFAULT_DELETE_TIMEOUT
        self._update_timeout = _DEFAULT_UPDATE_TIMEOUT

    @property
    def logicalresourceid(self):
        return self._logicalresourceid

    @property
    def physicalresourceid(self):
        return self._physicalresourceid

    @property
    def requestid(self):
        return self._requestid

    @property
    def resourceproperties(self):
        return self._resourceproperties

    @property
    def resourcetype(self):
        return self._resourcetype

    @property
    def responseurl(self):
        return self._responseurl

    @property
    def requesttype(self):
        return self._requesttype

    @property
    def servicetoken(self):
        return self._servicetoken

    @property
    def stackid(self):
        return self._stackid

    def create(self):
        return {}

    def delete(self):
        return {}

    def update(self):
        return {}

    def _get_region(self):
        if 'Region' in self._resourceproperties:
            return self._resourceproperties['Region']
        else: 
            return self._stackid.split(':')[3]

    def determine_event_timeout(self):
        if self.requesttype == "Create":
            timeout = self._create_timeout
        elif self.requesttype == "Delete":
            timeout = self._delete_timeout
        else:
            timeout = self._update_timeout

        return timeout

    def process_event(self):
        if self.requesttype == "Create":
            command = self.create
        elif self.requesttype == "Delete":
            command = self.delete
        else:
            command = self.update

        try:
            self.result_text = command()
            success = True
            if isinstance(self.result_text, dict):
                try:
                    self.result_attributes = { "Data" : self.result_text }
                    log.info(u"Command %s-%s succeeded", self.logicalresourceid, self.requesttype)
                    log.debug(u"Command %s output: %s", self.logicalresourceid, self.result_text)
                except:
                    log.error(u"Command %s-%s returned invalid data: %s", self.logicalresourceid,
                              self.requesttype, self.result_text)
                    success = False
                    self.result_attributes = {}
            else:
                raise ValueError(u"Results must be a JSON object")
        except:
            e = sys.exc_info()
            log.error(u"Command %s-%s failed", self.logicalresourceid, self.requesttype)
            log.debug(u"Command %s output: %s", self.logicalresourceid, e[0])
            log.debug(u"Command %s traceback: %s", self.logicalresourceid, traceback.print_tb(e[2]))
            success = False

        self.send_result(success, self.result_attributes)

    def send_result(self, success, attributes):
        attributes = attributes if attributes else {}
        source_attributes = {
            "Status": "SUCCESS" if success else "FAILED",
            "StackId": self.stackid,
            "RequestId": self.requestid,
            "LogicalResourceId": self.logicalresourceid
        }

        source_attributes['PhysicalResourceId'] = self.physicalresourceid
        if not source_attributes['PhysicalResourceId']:
            source_attributes['PhysicalResourceId'] = str(uuid.uuid4())

        if not success:
            source_attributes["Reason"] = "Unknown Failure"

        source_attributes.update(attributes)
        log.debug(u"Sending result: %s", source_attributes)
        self._put_response(source_attributes)

    @util.retry_on_failure(max_tries=10)
    def __send(self, data):
        requests.put(self.responseurl,
                     data=json.dumps(data),
                     headers={"Content-Type": ""},
                     verify=True).raise_for_status()

    def _put_response(self, data):
        try:
            self.__send(data)
            log.info(u"CloudFormation successfully sent response %s", data["Status"])
        except IOError:
            log.exception(u"Failed sending CloudFormation response")

    def __repr__(self):
        return str(self._event)
