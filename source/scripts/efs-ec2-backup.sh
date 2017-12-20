#!/bin/bash
#
#========================================================================
#
# master script to run efs-backup
# fetches EFS mount IPs
# runs efs-backup scripts
# uploads logs to S3
# updates status on DynamoDB
#
#========================================================================
# author: aws-solutions-builder@


clear
echo "This is the master script to perform efs backup"
sleep 2

_source_efs=$1 ## {type:string, description:source efs id}
_destination_efs=$2 ## {type:string, description:destination efs id}
_interval=$3 ## {type:string, description:interval for backup daily/weekly/monthly}
_retain=$4 ## {type:number, description:number of copies to retain}
_folder_label=$5 ## {type:string, description:backup folder identifier}
_backup_prefix=$6 ## {type:string, description:backup source prefix}

echo "## input from user ##"
echo "_source_efs: ${_source_efs}"
echo "_destination_efs: ${_destination_efs}"
echo "_interval: ${_interval}"
echo "_retain: ${_retain}"
echo "_folder_label: ${_folder_label}"
echo "_backup_prefix: ${_backup_prefix}"

#
# get region and instance-id from instance meta-data
#
_az=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone/)
_region=${_az::-1}
echo "region is ${_region}"
_instance_id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "instance-id is ${_instance_id}"

#
# getting source/destination efs mount ip
# parameters : [_source_efs, _region]
#
echo "-- $(date -u +%FT%T) -- resolving source address ${_source_efs}.efs.${_region}.amazonaws.com"
until dig ${_source_efs}.efs.${_region}.amazonaws.com +short
do
  sleep 1
done
_src_mount_ip=$(dig ${_source_efs}.efs.${_region}.amazonaws.com +short)
echo "-- $(date -u +%FT%T) -- src mount ip: ${_src_mount_ip}"

echo "-- $(date -u +%FT%T) -- resolving destination address ${_destination_efs}.efs.${_region}.amazonaws.com"
until dig ${_destination_efs}.efs.${_region}.amazonaws.com +short
do
  sleep 1
done
_dst_mount_ip=$(dig ${_destination_efs}.efs.${_region}.amazonaws.com +short)
echo "-- $(date -u +%FT%T) -- dst mount ip: ${_dst_mount_ip}"

if [ -z "${_src_mount_ip}" ] || [ -z "${_dst_mount_ip}" ]; then
  echo "-- $(date -u +%FT%T) -- ERROR:efs_mount_ip_not_found"
  echo "-- $(date -u +%FT%T) -- Either or both mount IPs not found, skipping EFS backup script. Please verify if the EC2 instance was launched in the same AZ as the EFS systems."
else
  #
  # running EFS backup script
  # parameters : [_src_mount_ip, _dst_mount_ip, _interval, _retain, _folder_label, _backup_window]
  #
  echo "-- $(date -u +%FT%T) -- running EFS backup script"
  # _timeout_val=$(((${_backup_window}-1)*60)) # timeout 1 minute less than given window -> timeout in SSM
  # timeout --preserve-status --signal=2 ${_timeout_val} ./efs-backup-fpsync.sh ${_src_mount_ip}:/ ${_dst_mount_ip}:/ ${_interval} ${_retain} ${_folder_label}
  /home/ec2-user/efs-backup-fpsync.sh ${_src_mount_ip}:${_backup_prefix} ${_dst_mount_ip}:/ ${_interval} ${_retain} ${_folder_label}
fi


#
# changing auto scaling capacity
# parameters : [_asg_name]
#
echo "-- $(date -u +%FT%T) -- Backup script finished before the backup window, stopping the ec2 instance."
_asg_name=$(aws ec2 describe-tags --region ${_region} --filters "Name=resource-id,Values=${_instance_id}" --query 'Tags[?Key==`aws:autoscaling:groupName`]'.Value --output text)
aws autoscaling set-desired-capacity --region ${_region} --auto-scaling-group-name ${_asg_name} --desired-capacity 0
