from lib.logger import Logger
from lib.events import CloudWatchEvent
from json import loads
log_level = 'critical'
logger = Logger(loglevel=log_level)
cwe = CloudWatchEvent(logger, 'uid')

describe_target_response = {'Targets': [{'Input': '{"action": "stop", "backup_id": "4a1e7e2f", "mode": "backup"}', 'Id': 'terminate_event_orchestrator', 'Arn': 'arn:aws:lambda:us-east-1:1234:function:test-cwe-events'}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '8a0', 'HTTPHeaders': {'x-amzn-requestid': '8a0', 'content-length': '206', 'content-type': 'application/x-amz-json-1.1'}}}

create_event_response = {'RuleArn': 'arn:aws:events:us-east-1:1234:rule/stop_backup_9aef9d39', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'e44', 'HTTPHeaders': {'x-amzn-requestid': 'e44', 'content-length': '77', 'content-type': 'application/x-amz-json-1.1'}}}

add_target_response = {'FailedEntries': [], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'e46', 'HTTPHeaders': {'x-amzn-requestid': 'e46', 'content-length': '41', 'content-type': 'application/x-amz-json-1.1'}}, 'FailedEntryCount': 0}

delete_event_response = {'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '3a1', 'HTTPHeaders': {'x-amzn-requestid': '3a1', 'date': 'Mon, 14 Aug 2017 20:21:59 GMT', 'content-length': '0', 'content-type': 'application/x-amz-json-1.1'}}}

remove_target_response = {'FailedEntries': [], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '3a0', 'HTTPHeaders': {'x-amzn-requestid': '3a0', 'date': 'Mon, 14 Aug 2017 20:21:59 GMT', 'content-length': '41', 'content-type': 'application/x-amz-json-1.1'}}, 'FailedEntryCount': 0}

get_lambda_arn_response = {'Code': {'RepositoryType': 'S3'}, 'Configuration': {'TracingConfig': {'Mode': 'PassThrough'}, 'Version': '$LATEST', 'FunctionName': 'test-cwe-events', 'VpcConfig': {'SubnetIds': [], 'SecurityGroupIds': []}, 'MemorySize': 128, 'CodeSize': 316, 'FunctionArn': 'arn:aws:lambda:us-east-1:1234:function:test-cwe-events', 'Environment': {'Variables': {'test1': 'value1', 'test3': 'value3', 'test2': 'value2', 'test5': 'value5', 'test4': 'value4'}}, 'Handler': 'lambda_function.lambda_handler', 'Role': 'arn:aws:iam::1234:role/lambda_basic_execution', 'Timeout': 3, 'Runtime': 'python2.7'}, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'e45', 'HTTPHeaders': {'x-amzn-requestid': 'e45', 'content-length': '1885', 'content-type': 'application/json', 'connection': 'keep-alive'}}}

add_permission_response = {'Statement': '{"Sid":"stop_backup_event","Effect":"Allow","Principal":{"Service":"events.amazonaws.com"},"Action":"lambda:InvokeFunction","Resource":"arn:aws:lambda:us-east-1:1234:function:test-cwe-events","Condition":{"ArnLike":{"AWS:SourceArn":"arn:aws:events:us-east-1:1234:rule/stop_backup_9aef9d39"}}}', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 201, 'RequestId': '7f7', 'HTTPHeaders': {'x-amzn-requestid': '7f7', 'content-length': '354', 'content-type': 'application/json', 'connection': 'keep-alive'}}}

remove_permission_response = {'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 204, 'RequestId': '21c', 'HTTPHeaders': {'x-amzn-requestid': '21c', 'connection': 'keep-alive', 'content-type': 'application/json'}}}


def test_describe_target(mocker):
    mocker.patch.object(cwe, 'describe_target')
    cwe.describe_target.return_value = describe_target_response
    response = cwe.describe_target()
    assert loads(response['Targets'][-1]['Input'])['backup_id'] == '4a1e7e2f'


def test_create_event(mocker):
    mocker.patch.object(cwe, 'create_event')
    cwe.create_event.return_value = create_event_response
    response = cwe.create_event('60', 'arn')
    assert response['RuleArn'] == 'arn:aws:events:us-east-1:1234:rule/stop_backup_9aef9d39'


def test_add_target(mocker):
    mocker.patch.object(cwe, 'add_target')
    cwe.add_target.return_value = add_target_response
    dictionary = {
        'mode': 'backup',
        'action': 'stop',
        'backup_id': 'backup_id'
    }
    response = cwe.add_target('mock_function_name', dictionary)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_delete_event(mocker):
    mocker.patch.object(cwe, 'delete_event')
    cwe.delete_event.return_value = delete_event_response
    response = cwe.delete_event()
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_remove_target(mocker):
    mocker.patch.object(cwe, 'remove_target')
    cwe.remove_target.return_value = remove_target_response
    response = cwe.remove_target()
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_get_lambda_arn(mocker):
    mocker.patch.object(cwe, 'get_lambda_arn')
    cwe.get_lambda_arn.return_value = get_lambda_arn_response
    response = cwe.get_lambda_arn('mock_function_name')
    assert response['Configuration']['FunctionArn'] == 'arn:aws:lambda:us-east-1:1234:function:test-cwe-events'


def test_add_permission(mocker):
    mocker.patch.object(cwe, 'add_permission')
    cwe.add_permission.return_value = add_permission_response
    response = cwe.add_permission('mock_function_name', 'mock_rule_arn')
    assert loads(response['Statement'])['Action'] == 'lambda:InvokeFunction'


def test_remove_permission(mocker):
    mocker.patch.object(cwe, 'remove_permission')
    cwe.remove_permission.return_value = remove_permission_response
    response = cwe.remove_permission('mock_function_name')
    assert response['ResponseMetadata']['HTTPStatusCode'] == 204
