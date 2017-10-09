#!/bin/bash

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the base source bucket name where the lambda code, bucket name where template will eventually reside and the version number."
    echo "Example: `basename $0` solutions templates v1.0"
    exit 1
fi

# Create zip file for AWS Lambda function
echo 'python source/scripts/lambda_build.py'
python source/scripts/lambda_build.py

# Copying shell scripts from source/scripts'
echo 'cp source/scripts/efs-* deployment/dist'
cp source/scripts/efs-* deployment/dist

# CloudFormation template creation
echo "cp -f deployment/efs*.template deployment/dist"
cp -f deployment/efs*.template deployment/dist

echo "Updating code source bucket in the template with $1"
replace="s/%DIST_BUCKET_NAME%/$1/g"
echo "sed -i '' -e $replace deployment/dist/efs-to-efs-backup.template"
sed -i '' -e $replace deployment/dist/efs-to-efs-backup.template
echo "sed -i '' -e $replace deployment/dist/efs-to-efs-restore.template"
sed -i '' -e $replace deployment/dist/efs-to-efs-restore.template

echo "Updating template bucket in the template and scripts with $2"
replace="s/%TEMPLATE_BUCKET_NAME%/$2/g"
echo "sed -i '' -e $replace deployment/dist/efs-to-efs-backup.template"
sed -i '' -e $replace deployment/dist/efs-to-efs-backup.template
echo "sed -i '' -e $replace deployment/dist/efs-to-efs-restore.template"
sed -i '' -e $replace deployment/dist/efs-to-efs-restore.template
echo "sed -i '' -e $replace deployment/dist/efs-backup-fpsync.sh"
sed -i '' -e $replace deployment/dist/efs-backup-fpsync.sh
echo "sed -i '' -e $replace deployment/dist/efs-restore-fpsync.sh"
sed -i '' -e $replace deployment/dist/efs-restore-fpsync.sh

echo "Updating version number in the template with $3"
replace="s/%VERSION%/$3/g"
echo "sed -i '' -e $replace deployment/dist/efs-to-efs-backup.template"
sed -i '' -e $replace deployment/dist/efs-to-efs-backup.template
echo "sed -i '' -e $replace deployment/dist/efs-to-efs-restore.template"
sed -i '' -e $replace deployment/dist/efs-to-efs-restore.template

echo 'Download the fpart package from github'
echo 'wget https://github.com/martymac/fpart/archive/fpart-0.9.3.zip; mv fpart-0.9.3.zip deployment/dist/fpart.zip'
wget https://github.com/martymac/fpart/archive/fpart-0.9.3.zip; mv fpart-0.9.3.zip deployment/dist/fpart.zip

echo 'Download the AMI ID lookup package from S3'
echo 'wget https://s3.amazonaws.com/cloudformation-examples/lambda/amilookup.zip; mv amilookup.zip deployment/dist/amilookup.zip'
wget https://s3.amazonaws.com/cloudformation-examples/lambda/amilookup.zip; mv amilookup.zip deployment/dist/amilookup.zip