from lib.cloudwatch import CloudWatchMetric
from lib.logger import Logger
from decimal import Decimal

log_level = 'critical'
logger = Logger(loglevel=log_level)
cw = CloudWatchMetric(logger)


efs_metrics_response = {'SrcBurstCreditBalance': Decimal('23'), 'SrcPermittedThroughput': Decimal('10')}

def test_cw_returns_dict(mocker):
    mocker.patch.object(cw, 'efs_cw_metrics')
    cw.efs_cw_metrics.return_value = efs_metrics_response
    response = cw.efs_cw_metrics('fake_efs_id', 'src')
    assert type(response) == dict

def test_check_efs_metrics(mocker):
    mocker.patch.object(cw, 'efs_cw_metrics')
    cw.efs_cw_metrics.return_value = efs_metrics_response
    cw.efs_cw_metrics('fake_efs_id', 'src')
    for key, value in efs_metrics_response.items():
        assert type(value) == Decimal

s3_metric_response = {'Datapoints': [
    {'Average': 1839341.0, 'Unit': 'Bytes'},
    {'Average': 1839341.0, 'Unit': 'Bytes'}],
    'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200,
                         'RequestId': '6547',
                         'HTTPHeaders': {'x-amzn-requestid': '6547','content-length': '649', 'content-type': 'text/xml'}},
    'Label': 'BucketSizeBytes'}

def test_s3_returns_dict(mocker):
    mocker.patch.object(cw, 's3_cw_metrics')
    cw.s3_cw_metrics.return_value = s3_metric_response
    response = cw.s3_cw_metrics('fake_bucket_name')
    assert type(response) == dict

def test_check_s3_metrics(mocker):
    mocker.patch.object(cw, 's3_cw_metrics')
    cw.s3_cw_metrics.return_value = s3_metric_response
    cw.s3_cw_metrics('fake_bucket_name')
    value = s3_metric_response['Datapoints'][-1]['Average']
    assert type(value) == float