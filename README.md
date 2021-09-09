## AWS EFS-to-EFS Backup Solution

### Description
The EFS-to-EFS backup solution leverages Amazon CloudWatch and AWS Lambda to
automatically create incremental backups of an Amazon Elastic File System (EFS) file system on a customer-
defined schedule. The solution is easy to deploy and provides automated backups for data
recovery and protection. For example, an organization can use this backup solution in a
production environment to automatically create backups of their file system(s) on daily basis,
and keep only a specified number of backups. For customers who do not have a mechanism
for backing up their Amazon EFS file systems, this solution provides an easy way to improve
data protection and recoverability.

### Architectural Workflow
•	The orchestrator lambda function is first invoked by CW event (start backup) schedule defined by the customer. The lambda function creates a 'Stop Backup' CWE event and add the orchestrator (itself) lambda function as the target. It also updates desired capacity of the autoscaling group (ASG) to 1 (one). Auto Scaling Group (ASG) launches an EC2 instance that mounts the source and target EFS and backup the primary EFS.

•	The orchestrator lambda function writes backup metadata to the DDB table with backup id as the primary key.

•	Fifteen minutes before the backup window defined by the customer, the 'Stop' CWE invokes orchestrator lambda to change the desired capacity of ASG to 0 (zero).

•	The lifecycle hook CWE is triggered by ASG event (EC2_Instance_Terminating). This CWE invokes the orchestrator lambda function that use ‘AWS-RunShellScript’ document name to make send_command api call to the SSM service.

•	During the lifecycle hook event, the EC2 instance will stop/cleanup rsync process gracefully and update the DDB table with the KPIs, upload logs to the S3 bucket.

•	The EC2 successful termination trigger another lifecycle hook event. This event triggers the orchestrator lambda function to send the anonymous metrics, notify customer if complete backup was not done.

### Setup

#### Run Unit Tests (pytest)
*Note: Use **sudo** if necessary to install python dependencies*

```bash
$ bash deployment/run-unit-tests.sh
```
***

#### Build S3 Assets

* Configure the build paraemters.
```bash
export EFS_BACKUP_PATH=`pwd`
export DIST_OUTPUT_BUCKET=my-bucket-name # bucket where customized code will reside
export VERSION=my-version # version number for the customized code
export SOLUTION_NAME=efs-backup # solution name for the customized code
```
_Note:_ You would have to create an S3 bucket with the prefix 'my-bucket-name-<aws_region>' as whole Lambda functions are going to get the source codes from the 'my-bucket-name-<aws_region>' bucket; aws_region is where you are deployting the customized solution (e.g. us-east-1, us-east-2, etc.).

* Build the customized solution
```bash
cd $EFS_BACKUP_PATH/deployment
chmod +x ./build-s3-dist.sh
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
```

* Deploy the source codes to an Amazon S3 bucket in your account. _Note:_ You must have the AWS Command Line Interface installed and create the Amazon S3 bucket in your account prior to copy source codes.
```bash
export AWS_REGION=us-east-1 # the AWS region you are going to deploy the solution in your account.
export AWS_PROFILE=default # the AWS Command Line Interface profile

aws s3 cp $EFS_BACKUP_PATH/deployment/global-s3-assets/ s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control --profile $AWS_PROFILE
aws s3 cp $EFS_BACKUP_PATH/deployment/regional-s3-assets/ s3://$DIST_OUTPUT_BUCKET-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control --profile $AWS_PROFILE
```

## Deploying the customized solution
* Get the link of the efs-to-efs-backup.template and efs-to-efs-restore.template uploaded to your Amazon S3 bucket.
* Deploy the EFS Backup solution to your account by launching a new AWS CloudFormation stack using the link of the efs-to-efs-backup.template and efs-to-efs-restore.template.

## Collection of operational metrics
This solution collects anonymous operational metrics to help AWS improve the quality and features of the solution. For more information, including how to disable this capability, please see the [implementation guide](https://docs.aws.amazon.com/solutions/latest/amazon-virtual-andon/collection-of-operational-metrics.html).

***

Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/LICENSE-2.0

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
