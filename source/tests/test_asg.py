import boto3
from moto import mock_autoscaling
from moto import mock_ec2
from lib.logger import Logger
from lib.asg import AutoScaling

log_level = 'critical'
logger = Logger(loglevel=log_level)
asg = AutoScaling(logger, 'test_asg')

def create_test_subnet():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    vpc = list(ec2.vpcs.all())[0]
    subnet = ec2.create_subnet(
        VpcId=vpc.id,
        CidrBlock='10.11.1.0/24',
        AvailabilityZone='us-east-1a')
    return subnet

def get_test_image_id():
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    ec2_images = ec2_client.describe_images()
    return ec2_images['Images'][0]['ImageId']

@mock_autoscaling
@mock_ec2
def test_start_instance():
    subnet = create_test_subnet()

    client = boto3.client('autoscaling', region_name='us-east-1')
    _ = client.create_launch_configuration(
        LaunchConfigurationName='test_launch_configuration',
        ImageId=get_test_image_id()
    )
    _ = client.create_auto_scaling_group(
        AutoScalingGroupName='test_asg',
        LaunchConfigurationName='test_launch_configuration',
        MinSize=0,
        MaxSize=20,
        DesiredCapacity=0,
        VPCZoneIdentifier=subnet.id
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
@mock_ec2
def test_stop_instance():
    subnet = create_test_subnet()

    client = boto3.client('autoscaling', region_name='us-east-1')
    _ = client.create_launch_configuration(
        LaunchConfigurationName='test_launch_configuration',
        ImageId=get_test_image_id()
    )
    _ = client.create_auto_scaling_group(
        AutoScalingGroupName='test_asg',
        LaunchConfigurationName='test_launch_configuration',
        MinSize=0,
        MaxSize=20,
        DesiredCapacity=1,
        VPCZoneIdentifier=subnet.id
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
@mock_ec2
def test_exception():
    subnet = create_test_subnet()

    client = boto3.client('autoscaling', region_name='us-east-1')
    _ = client.create_launch_configuration(
        LaunchConfigurationName='test_launch_configuration',
        ImageId=get_test_image_id()
    )
    _ = client.create_auto_scaling_group(
        AutoScalingGroupName='test_asg',
        LaunchConfigurationName='test_launch_configuration',
        MinSize=0,
        MaxSize=20,
        DesiredCapacity=1,
        VPCZoneIdentifier=subnet.id
    )

    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=["test_asg"]
    )
    # Instantiate class with invalid ASG Name, the function should catch the exception
    asg = AutoScaling(logger, 'test_asg_invalid')
    response = asg.update_asg('invalid')
    assert response == 'unhandled exception'
