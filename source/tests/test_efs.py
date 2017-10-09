from lib.logger import Logger
from lib.efs import EFS
log_level = 'critical'
logger = Logger(loglevel=log_level)
efs = EFS(logger)

response = {
    'ResponseMetadata':
        {
            'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '7feeb7b6-760e-11e7-81f2-d7792aa8bdb2',
            'HTTPHeaders': {
                'x-amzn-requestid': '7feeb7b6-760e-11e7-81f2-d7792aa8bdb2',
                'date': 'Mon, 31 Jul 2017 16:37:10 GMT', 'content-length': '375',
                'content-type': 'application/json'
            }
        },
        u'FileSystems': [
            {
                u'SizeInBytes': {
                    u'Value': 99
                },
                u'Name': u'gen-purpose-src',
                u'CreationToken': u'console-ea5e8735-901f-44a1-87c7-53d45ad666ba',
                u'PerformanceMode': u'generalPurpose',
                u'FileSystemId': u'fs-7c9e1835',
                u'NumberOfMountTargets': 5,
                u'LifeCycleState': u'available',
                u'OwnerId': u'36'
            }
        ]
}


def test_efs_size(mocker):
    mocker.patch.object(efs, 'size')
    efs.size.response = response
    efs.size('mock-efs-id')
    assert response['FileSystems'][0]['SizeInBytes']['Value'] == 99


def test_performance_mode(mocker):
    mocker.patch.object(efs, 'performance_mode')
    efs.performance_mode.response = response
    efs.size('mock-efs-id')
    assert response['FileSystems'][0]['PerformanceMode'] == 'generalPurpose'


def test_size_method_exception():
    response = efs.size('mock-efs-id')
    assert response == 'unhandled exception'


def test_performance_mode_method_exception():
    response = efs.performance_mode('mock-efs-id')
    assert response == 'unhandled exception'



