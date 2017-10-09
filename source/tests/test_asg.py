from lib.asg import AutoScaling
import boto3
from moto import mock_autoscaling
from lib.logger import Logger

log_level = 'critical'
logger = Logger(loglevel=log_level)
asg = AutoScaling(logger, 'test_asg')


@mock_autoscaling
def test_start_instance():
    client = boto3.client('autoscaling', region_name='us-east-1')
    _ = client.create_launch_configuration(
        LaunchConfigurationName='test_launch_configuration'
    )
    _ = client.create_auto_scaling_group(
        AutoScalingGroupName='test_asg',
        LaunchConfigurationName='test_launch_configuration',
        MinSize=0,
        MaxSize=20,
        DesiredCapacity=0
    )

    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=["test_asg"]
    )

    assert response['AutoScalingGroups'][0]['DesiredCapacity'] == 0

    # Start Backup - changes the desired capacity to 1
    asg.update_asg('start_instance')

    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=["test_asg"]
    )

    assert response['AutoScalingGroups'][0]['DesiredCapacity'] == 1

@mock_autoscaling
def test_stop_instance():
    client = boto3.client('autoscaling', region_name='us-east-1')
    _ = client.create_launch_configuration(
        LaunchConfigurationName='test_launch_configuration'
    )
    _ = client.create_auto_scaling_group(
        AutoScalingGroupName='test_asg',
        LaunchConfigurationName='test_launch_configuration',
        MinSize=0,
        MaxSize=20,
        DesiredCapacity=1
    )

    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=["test_asg"]
    )

    assert response['AutoScalingGroups'][0]['DesiredCapacity'] == 1

    # Start Backup - changes the desired capacity to 0
    asg.update_asg('stop_instance')

    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=["test_asg"]
    )

    assert response['AutoScalingGroups'][0]['DesiredCapacity'] == 0

@mock_autoscaling
def test_exception():
    client = boto3.client('autoscaling', region_name='us-east-1')
    _ = client.create_launch_configuration(
        LaunchConfigurationName='test_launch_configuration'
    )
    _ = client.create_auto_scaling_group(
        AutoScalingGroupName='test_asg',
        LaunchConfigurationName='test_launch_configuration',
        MinSize=0,
        MaxSize=20,
        DesiredCapacity=1
    )

    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=["test_asg"]
    )
    # Instantiate class with invalid ASG Name, the function should catch the exception
    asg = AutoScaling(logger, 'test_asg_invalid')
    response = asg.update_asg('invalid')
    assert response == 'unhandled exception'
