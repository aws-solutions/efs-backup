from __future__ import unicode_literals

import boto3
from moto import mock_dynamodb2
from lib.logger import Logger
from lib.dynamodb import DDB

log_level = 'critical'
logger = Logger(loglevel=log_level)

def create_test_table():
    client = boto3.client('dynamodb', region_name='us-east-1')
    client.create_table(TableName='mock-table', KeySchema=[
        {'AttributeName': 'primary_key', 'KeyType': 'HASH'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'primary_key', 'AttributeType': 'S'}
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10,
    })
    return client.describe_table(TableName='mock-table')

@mock_dynamodb2
def test_item_add_and_describe_and_update():
    table_desc = create_test_table()
    table_name = table_desc['Table']['TableName']
    ddb = DDB(logger, table_name)

    item = {
        "primary_key": "Test1234",
        "key2" : 1234
    }
    response =  ddb.write_item(item)

    returned_item = ddb.read_item('primary_key', 'Test1234')

    assert dict(returned_item) == item

@mock_dynamodb2
def test_write_item_exception():
    table_desc = create_test_table()
    table_name = table_desc['Table']['TableName']
    ddb = DDB(logger, table_name)

    item = {
        "invalid_key": "Test1234",
        "key2" : 1234
    }
    item = {}
    response =  ddb.write_item(item)

    assert response == 'unhandled exception put'

@mock_dynamodb2
def test_read_item_exception():
    table_desc = create_test_table()
    table_name = table_desc['Table']['TableName']
    ddb = DDB(logger, table_name)

    item = {
        "primary_key": "Test1234",
        "key2" : 1234
    }
    item = {}
    ddb.write_item(item)

    response = ddb.read_item('invalid_key', 'Test1234')

    assert response == 'unhandled exception get'
