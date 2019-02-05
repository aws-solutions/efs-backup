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

```python
$ bash deployment/run-unit-tests.sh
Installing dependencies using pip
```
***

#### Build S3 Assets

```bash
$ bash deployment/build-s3-dist.sh {code-bucket-name} {cf-template-bucket-name} {version-number}
python source/scripts/lambda_build.py

 Directory ../../deployment/dist not found, creating now...

 Following files will be zipped in efs_to_efs_backup.zip and saved in the deployment/dist folder.
--------------------------------------------------------------------------------------
./orchestrator.py
./lib/__init__.py
./lib/asg.py
./lib/cloudwatch.py
./lib/dynamodb.py
./lib/efs.py
./lib/events.py
./lib/logger.py
./lib/notify.py
./lib/ssm.py
./lib/ssm.sh
cp -f deployment/efs*.template deployment/dist
Updating code source bucket in template with solutions
sed -i '' -e s/%DIST_BUCKET_NAME%/solutions/g deployment/dist/efs-backup.template
sed -i '' -e s/%DIST_BUCKET_NAME%/solutions/g deployment/dist/efs-restore.template
Updating template bucket in template with solutions-reference
sed -i '' -e s/%TEMPLATE_BUCKET_NAME%/solutions-reference/g deployment/dist/efs-backup.template
sed -i '' -e s/%TEMPLATE_BUCKET_NAME%/solutions-reference/g deployment/dist/efs-restore.template
Updating version number in the template with v1.0
sed -i '' -e s/%VERSION%/v1.0/g deployment/dist/efs-to-efs-backup.template
sed -i '' -e s/%VERSION%/v1.0/g deployment/dist/efs-to-efs-restore.template
Download the fpart package from github
wget https://github.com/martymac/fpart/archive/fpart-0.9.3.zip; mv fpart-0.9.3.zip fpart.zip
https://codeload.github.com/martymac/fpart/zip/fpart-0.9.3
Resolving codeload.github.com (codeload.github.com)...
Connecting to codeload.github.com (codeload.github.com)|... connected.
HTTP request sent, awaiting response... 200 OK
Length: unspecified [application/zip]
Saving to: 'fpart-0.9.3.zip'
0K .......... .......... .......... .......... .......... 14.3M
50K .......... .......... .... 15.4M=0.005s
(14.6 MB/s) - 'fpart-0.9.3.zip' saved [76187]
cp source/scripts/efs-* deployment/dist

$ ls -l deployment/dist     
-rw-r--r--      efs-backup-fpsync.sh
-rw-r--r--      efs-backup.template
-rw-r--r--      efs-ec2-backup.sh
-rw-r--r--      efs-ec2-restore.sh
-rw-r--r--      efs-restore-fpsync.sh
-rw-r--r--      efs-restore.template
-rw-r--r--      efs_to_efs_backup.zip
-rw-r--r--      fpart.zip
-rw-r--r--      amilookup.zip
```
***

#### S3 Bucket Structure

```bash
CloudFormation Template Bucket
- Copy following assets to {cf-template-bucket-name}:
    * efs-restore.template
    * efs-backup.template
    * efs-restore-fpsync.sh
    * efs-ec2-restore.sh
    * efs-ec2-backup.sh
    * efs-backup-fpsync.sh

Code Bucket Name:
- Copy following assets to {code-bucket-name}-<AWS_REGION_NAME>:
    * efs_to_efs_backup.zip
    * amilookup.zip
```

***

#### v1.2 changes

```bash
* fixed timeout issue with custom lambda resource fetching latest AMI
* removed duplicate line in efs-to-efs-backup.template
* error handling for efs mount targets not mounted
* fixed false notification when efs mount targets not mounted
* added support for restoring sub directory from the backup
* backup window provided in form of drop down menu to avoid input errors
* parallelized removal of snapshot in ec2-backup-fpsync.sh
* improved overall backup and restore experience
```

***

#### v1.3 changes

```bash
* parallel operations to improve removal of old backups
* parallel operations to improve creation of hardlinks for backups
* improving backup notifications
* drop down options for backup window selection
* instance size selection defaults to c5.xlarge
* node.js runtime update to 8.10
* DynamoDB Read/Write provisioned capacity units reduced to 2
```

***

Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/asl/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
