from __future__ import unicode_literals

from lib.logger import Logger
from lib.dynamodb import DDB
from moto import mock_dynamodb2_deprecated
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.table import Table

log_level = 'critical'
logger = Logger(loglevel=log_level)


def create_table():
    table = Table.create('mock-table', schema=[
        HashKey('primary_key')
    ], throughput={
        'read': 10,
        'write': 10,
    })
    #table.describe()
    return table

@mock_dynamodb2_deprecated
def test_item_add_and_describe_and_update():
    table = create_table()
    ok = table.describe()
    table_name = ok['Table']['TableName']
    ddb = DDB(logger, table_name)

    item = {
        "primary_key": "Test1234",
        "key2" : 1234
    }
    response =  ddb.write_item(item)

    returned_item = ddb.read_item('primary_key', 'Test1234')

    assert dict(returned_item) == item

@mock_dynamodb2_deprecated
def test_write_item_exception():
    table = create_table()
    ok = table.describe()
    table_name = ok['Table']['TableName']
    ddb = DDB(logger, table_name)

    item = {
        "invalid_key": "Test1234",
        "key2" : 1234
    }
    item = {}
    response =  ddb.write_item(item)

    assert response == 'unhandled exception put'

@mock_dynamodb2_deprecated
def test_read_item_exception():
    table = create_table()
    ok = table.describe()
    table_name = ok['Table']['TableName']
    ddb = DDB(logger, table_name)

    item = {
        "primary_key": "Test1234",
        "key2" : 1234
    }
    item = {}
    ddb.write_item(item)

    response = ddb.read_item('invalid_key', 'Test1234')

    assert response == 'unhandled exception get'
