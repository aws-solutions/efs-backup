# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5] - 2019-12-20
### Updated
- Update Node.JS runtime from 8.10 to 12
- Update Python runtime from 3.7 to 3.8
- Update software license
- Update ```README.md```
- Update ```build-s3-dist.sh``` script
- Update ```efs-to-backup.template``` Auto Scaling launch configuration userdata and Lambda function code ```S3Bucket``` and ```S3Key```
- Update ```efs-to-restore.template``` Auto Scaling launch configuration userdata and Lambda function code ```S3Bucket``` and ```S3Key```
- Update ```solution-helper.py``` to remove ```pycfn_custom_resource``` and add send response function

### Added
- Add ```CHANGELOG.md```
- Add sending anonymous metrics whiling creating, updating, and deleting the solution

### Removed
- Remove ```lambda-build.py```
- Remove ```pycfn_custom_resource```

## [1.4] - 2019-07-31
### Added
- Add security group to outputs in backup and restore templates

### Updated
- Upgrade Python code from version 2.7 to 3.7
- Update unit tests
- Making encryption/access control changes to log bucket to be consistent with best practices
- Where applicable, add constraints for parameters to make them required

## [1.3] - 2018-07-18
### Added
- Parallel operations to improve removal of old backups
- Parallel operations to improve creation of hardlinks for backups
- Drop down options for backup window selection

### Updated
- Improve backup notifications
- Update Node.JS runtime to 8.10
- DynamoDB Read/Write provisioned capacity units reduced to 2
- Instance size selection defaults to c5.xlarge

## [1.2.0] - 2018-05-09
### Added
- Add support for restoring sub directory from the backup

### Updated
- Fix timeout issue with custom lambda resource fetching latest AMI
- Fix false notification when efs mount targets not mounted
- Backup window provided in form of drop down menu to avoid input errors
- Parallelized removal of snapshot in ec2-backup-fpsync.sh
- Improved overall backup and restore experience

### Removed
- Remove duplicate line in efs-to-efs-backup.template

## [1.0.0] - 2017-09-05
### Added
- AWS EFS-to-EFS Backup Solution release