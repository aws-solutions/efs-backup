#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./build-s3-dist.sh source-bucket-base-name trademarked-solution-name version-code
#
# Paramenters:
#  - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda
#    code from. The template will append '-[region_name]' to this bucket name.
#    For example: ./build-s3-dist.sh solutions my-solution v1.0.0
#    The template will then expect the source code to be located in the solutions-[region_name] bucket
#
#  - trademarked-solution-name: name of the solution for consistency
#
#  - version-code: version of the package

# Check to see if input has been provided:
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./build-s3-dist.sh solutions trademarked-solution-name v1.0.0"
    exit 1
fi

deployment_dir="$PWD"
template_dist_dir="$deployment_dir/global-s3-assets"
build_dist_dir="$deployment_dir/regional-s3-assets"
source_dir="$deployment_dir/../source"

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old dist folders"
echo "------------------------------------------------------------------------------"
echo "rm -rf $template_dist_dir"
rm -rf $template_dist_dir
echo "mkdir -p $template_dist_dir"
mkdir -p $template_dist_dir
echo "rm -rf $build_dist_dir"
rm -rf $build_dist_dir
echo "mkdir -p $build_dist_dir"
mkdir -p $build_dist_dir

echo "------------------------------------------------------------------------------"
echo "[Packing] Templates"
echo "------------------------------------------------------------------------------"
# CloudFormation template creation
echo "cp -f $deployment_dir/efs*.template $template_dist_dir"
cp -f $deployment_dir/efs*.template $template_dist_dir

if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OS
    echo "Updating code source bucket in the template with $1"
    replace="s/%%BUCKET_NAME%%/$1/g"
    echo "sed -i '' -e $replace $template_dist_dir/efs-to-efs-backup.template"
    sed -i '' -e $replace $template_dist_dir/efs-to-efs-backup.template
    echo "sed -i '' -e $replace $template_dist_dir/efs-to-efs-restore.template"
    sed -i '' -e $replace $template_dist_dir/efs-to-efs-restore.template

    echo "Updating solution name in the template with $2"
    replace="s/%%SOLUTION_NAME%%/$2/g"
    echo "sed -i '' -e $replace $template_dist_dir/efs-to-efs-backup.template"
    sed -i '' -e $replace $template_dist_dir/efs-to-efs-backup.template
    echo "sed -i '' -e $replace $template_dist_dir/efs-to-efs-restore.template"
    sed -i '' -e $replace $template_dist_dir/efs-to-efs-restore.template

    echo "Updating version number in the template with $3"
    replace="s/%%VERSION%%/$3/g"
    echo "sed -i '' -e $replace $template_dist_dir/efs-to-efs-backup.template"
    sed -i '' -e $replace $template_dist_dir/efs-to-efs-backup.template
    echo "sed -i '' -e $replace $template_dist_dir/efs-to-efs-restore.template"
    sed -i '' -e $replace $template_dist_dir/efs-to-efs-restore.template
else
    # Other linux
    echo "Updating code source bucket in the template with $1"
    replace="s/%%BUCKET_NAME%%/$1/g"
    echo "sed -i -e $replace $template_dist_dir/efs-to-efs-backup.template"
    sed -i -e $replace $template_dist_dir/efs-to-efs-backup.template
    echo "sed -i -e $replace $template_dist_dir/efs-to-efs-restore.template"
    sed -i -e $replace $template_dist_dir/efs-to-efs-restore.template

    echo "Updating solution name in the template with $2"
    replace="s/%%SOLUTION_NAME%%/$2/g"
    echo "sed -i -e $replace $template_dist_dir/efs-to-efs-backup.template"
    sed -i -e $replace $template_dist_dir/efs-to-efs-backup.template
    echo "sed -i -e $replace $template_dist_dir/efs-to-efs-restore.template"
    sed -i -e $replace $template_dist_dir/efs-to-efs-restore.template

    echo "Updating version number in the template with $3"
    replace="s/%%VERSION%%/$3/g"
    echo "sed -i -e $replace $template_dist_dir/efs-to-efs-backup.template"
    sed -i -e $replace $template_dist_dir/efs-to-efs-backup.template
    echo "sed -i -e $replace $template_dist_dir/efs-to-efs-restore.template"
    sed -i -e $replace $template_dist_dir/efs-to-efs-restore.template
fi

echo "------------------------------------------------------------------------------"
echo "[Packing] Lambda functions and scripts"
echo "------------------------------------------------------------------------------"
# Create zip file for AWS Lambda function
echo "cd $source_dir"
cd $source_dir
echo "zip -q -r9 $build_dist_dir/efs_to_efs_backup.zip * -x setup.* tests/\* requirements.txt scripts/\*"
zip -q -r9 $build_dist_dir/efs_to_efs_backup.zip * -x setup.* tests/\* requirements.txt scripts/\*

# Copying shell scripts from source/scripts'
echo "cp $source_dir/scripts/efs-* $build_dist_dir"
cp $source_dir/scripts/efs-* $build_dist_dir

echo 'Download the AMI ID lookup package from S3'
echo "curl --connect-timeout 5 --speed-time 5 --retry 10 https://s3.amazonaws.com/cloudformation-examples/lambda/amilookup.zip -o $build_dist_dir/amilookup.zip"
curl --connect-timeout 5 --speed-time 5 --retry 10 https://s3.amazonaws.com/cloudformation-examples/lambda/amilookup.zip -o $build_dist_dir/amilookup.zip