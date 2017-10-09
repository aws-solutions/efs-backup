from __future__ import unicode_literals
import boto3
from lib.notify import Notify
from lib.logger import Logger
from uuid import uuid4
from moto.packages.responses import responses
from moto import mock_sns
from decimal import Decimal
from unittest import TestCase
from unittest import TestLoader
from unittest import TextTestRunner

log_level = 'info'
logger = Logger(loglevel=log_level)

class NotifyTest(TestCase):
    def setUp(self):
        self.notify = Notify(logger)

    @mock_sns
    def test_customer_notify(self):
        responses.add(
            method="POST",
            url="http://example.com/foobar",
        )

        conn = boto3.client('sns', region_name='us-east-1')
        conn.create_topic(Name="dummy-topic")
        response = conn.list_topics()
        topic_arn = response["Topics"][0]['TopicArn']

        message = {'key_string1': '2017-7-6',
                 'key_string2': '12345',
                 'decimal': Decimal('1')
                 }
        response = self.notify.customer(topic_arn, message)
        self.assertTrue(response['ResponseMetadata']['HTTPStatusCode'] == 200)


    def test_backend_metrics(self):
        uuid = str(uuid4())
        solution_id = 'SO_unit_test'
        customer_uuid = uuid
        logger.info("UUID: " + customer_uuid)
        data = {'key_string1': '2017-7-6',
                 'key_string2': '12345',
                 'decimal': Decimal('1')
                 }
        url = 'https://oszclq8tyh.execute-api.us-east-1.amazonaws.com/prod/generic'
        response = self.notify.metrics(solution_id, customer_uuid, data, url)
        self.assertTrue(response == 200)

if __name__ == '__main__' and __package__ is None:
    suite = TestLoader().loadTestsFromTestCase(NotifyTest)
    TextTestRunner(verbosity=2).run(suite)
