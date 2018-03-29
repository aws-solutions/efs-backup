#!/bin/bash
#
#========================================================================
#
# master script to run efs-restore-fpsync
# fetches EFS mount IPs
# runs efs-restore scripts
# uploads logs to S3
# updates status on DynamoDB
#
#========================================================================
# author: aws-solutions-builder@


clear
echo "This is the master script to perform efs restore"
sleep 2

_source_efs=$1 ## {type:string, description:source efs id}
_backup_efs=$2 ## {type:string, description:backup efs id}
_interval=$3 ## {type:string, description:interval for backup daily/weekly/monthly}
_backup_num=$4 ## {type:number, description:backup number to restore}
_folder_label=$5 ## {type:string, description:backup identifier}
_src_prefix=$6 ## {type:string, description:source prefix where files will be restored}
_s3bucket=$7 ## {type:string, description:s3 bucket to publish logs}
_sns_topic=$8 ## {type:string, description:sns topic arn for restore notifications}

echo "## input from user ##"
echo "_source_efs: ${_source_efs}"
echo "_backup_efs: ${_backup_efs}"
echo "_interval: ${_interval}"
echo "_backup_num: ${_backup_num}"
echo "_folder_label: ${_folder_label}"
echo "_src_prefix: ${_src_prefix}"
echo "_s3bucket: ${_s3bucket}"
echo "_sns_topic: ${_sns_topic}"

#
# get region from instance meta-data
#
_az=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone/)
_region=${_az::-1}
echo "region is ${_region}"
_instance_id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "instance-id is ${_instance_id}"
_instance_type=$(curl -s http://169.254.169.254/latest/meta-data/instance-type/)
echo "instance-type is ${_instance_type}"

#
# getting source/backup efs mount ip
# parameters : [_source_efs, _region]
#
echo "-- $(date -u +%FT%T) -- resolving source efs address ${_source_efs}.efs.${_region}.amazonaws.com"
until dig ${_source_efs}.efs.${_region}.amazonaws.com +short
do
  sleep 1
done
_src_mount_ip=$(dig ${_source_efs}.efs.${_region}.amazonaws.com +short)
echo "-- $(date -u +%FT%T) -- src mount ip: ${_src_mount_ip}"

echo "-- $(date -u +%FT%T) -- resolving backup efs address ${_backup_efs}.efs.${_region}.amazonaws.com"
until dig ${_backup_efs}.efs.${_region}.amazonaws.com +short
do
  sleep 1
done
_backup_mount_ip=$(dig ${_backup_efs}.efs.${_region}.amazonaws.com +short)
echo "-- $(date -u +%FT%T) -- backup mount ip: ${_backup_mount_ip}"

if [ -z "${_src_mount_ip}" ] || [ -z "${_backup_mount_ip}" ]; then
  echo "-- $(date -u +%FT%T) -- ERROR:efs_mount_ip_not_found"
  echo "-- $(date -u +%FT%T) -- Either or both mount IPs not found, skipping EFS restore script. Please verify if the EC2 instance was launched in the same AZ as the EFS systems."
  echo "-- $(date -u +%FT%T) -- Notify customer of failure"
  aws sns publish --region ${_region} \
  --topic-arn ${_sns_topic} \
  --message '{
    SourceEFS:'${_source_efs}',
    BackupEFS:'${_backup_efs}',
    Interval:'${_interval}',
    BackupNum:'${_backup_num}',
    FolderLabel:'${_folder_label}',
    SourcePrefix:'${_src_prefix}',
    LogBucket:'${_s3bucket}',
    RestoreStatus:Unable to find the mount IP address of either source or backup EFS. Please verify if the EC2 instance was launched in the same AZ as the EFS systems. Terminating instance.
  }'
else
  #
  # running efs restore script
  # parameters : [_src_mount_ip, _backup_mount_ip, _interval, _retain, _folder_label, _backup_window]
  #
  echo "-- $(date -u +%FT%T) -- running efs restore script"
  _restore_start_time=$(date -u +%FT%T)
  # _timeout_val=$(((${_backup_window}-1)*60)) # timeout 1 minute less than given window -> timeout in SSM
  # timeout --preserve-status --signal=2 ${_timeout_val} ./efs-backup-fpsync.sh ${_src_mount_ip}:/ ${_backup_mount_ip}:/ ${_interval} ${_retain} ${_folder_label}
  /home/ec2-user/efs-restore-fpsync.sh ${_src_mount_ip}:${_src_prefix} ${_backup_mount_ip}:/ ${_interval} ${_backup_num} ${_folder_label} ${_s3bucket}
  restoreStatus=$?
  _restore_stop_time=$(date -u +%FT%T)
  echo "-- $(date -u +%FT%T) -- fpsync finished with status: $restoreStatus"

  #
  # uploading efs restore logs to s3
  # parameters : [s3bucket, efsid]
  #
  echo "-- $(date -u +%FT%T) -- upload efs restore fpsync logs to S3 bucket"
  aws s3 cp /tmp/efs-restore.log s3://${_s3bucket}/efs-restore-logs/${_folder_label}-${_interval}.${_backup_num}-restore-fpsync-`date +%Y%m%d-%H%M`.log
  echo "upload restore fpsync logs to S3, status: $?"
  echo "-- $(date -u +%FT%T) -- upload efs restore rsync logs to S3 bucket"
  aws s3 cp /tmp/efs-restore-rsync.log s3://${_s3bucket}/efs-restore-logs/${_folder_label}-${_interval}.${_backup_num}-restore-rsync-`date +%Y%m%d-%H%M`.log
  echo "upload restore rsync logs to S3, status: $?"

  #
  # calculating restored data and reporting to backend metric
  # parameters : [_nofs, _nfst, _tfs, _ttfs]
  #
  _nofs=$(cat /tmp/efs-restore.log | grep 'Number of files' | awk '{nofs += $7} END {print nofs}')
  echo "Number of files: ${_nofs}"

  _nfst=$(cat /tmp/efs-restore.log | grep 'Number of files transferred' | awk '{nfst += $8} END {print nfst}')
  echo "Number of files transferred: ${_nfst}"

  _tfs=$(cat /tmp/efs-restore.log | grep 'Total file size' | awk '{tfs += $7} END {print tfs}')
  echo "Total file size: ${_tfs}"

  _ttfs=$(cat /tmp/efs-restore.log | grep 'Total transferred file size' | awk '{ttfs += $8} END {print ttfs}')
  echo "Total transferred file size: ${_ttfs}"

  # timestamps for (fpsync) and (rsync) file operations
  _fpsync_start=$(cat /var/log/cloud-init-output.log | grep 'fpsync_start' | cut -d: -f2-)
  echo "fpsync start time: ${_fpsync_start}"
  _fpsync_stop=$(cat /var/log/cloud-init-output.log | grep 'fpsync_stop' | cut -d: -f2-)
  echo "fpsync start time: ${_fpsync_stop}"
  _rsync_start=$(cat /var/log/cloud-init-output.log | grep 'rsync_start' | cut -d: -f2-)
  echo "rsync start: ${_rsync_start}"
  _rsync_stop=$(cat /var/log/cloud-init-output.log | grep 'rsync_stop' | cut -d: -f2-)
  echo "rsync stop: ${_rsync_stop}"


  _rtime=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  _headers="Content-Type: application/json"
  _url="https://metrics.awssolutionsbuilder.com/generic"
  _uuid=$(uuidgen)
  echo "_metric={\"Interval\":\"${_interval}\",\"BackupNum\":\"${_backup_num}\",\"FolderLabel\":\"${_folder_label}\",\"NumberOfFiles\":\"${_nofs}\",\"NumberOfFilesTransferred\":\"${_nfst}\",\"TotalFileSize\":\"${_tfs}\",\"TotalTransferredFileSize\":\"${_ttfs}\",\"RestoreStartTime\":\"${_restore_start_time}\",\"RestoreStopTime\":\"${_restore_stop_time}\",\"InstanceType\":\"${_instance_type}\",\"Region\":\"${_region}\"}"
  _metric="{\"Interval\":\"${_interval}\",\"BackupNum\":\"${_backup_num}\",\"FolderLabel\":\"${_folder_label}\",\"NumberOfFiles\":\"${_nofs}\",\"NumberOfFilesTransferred\":\"${_nfst}\",\"TotalFileSize\":\"${_tfs}\",\"TotalTransferredFileSize\":\"${_ttfs}\",\"RestoreStartTime\":\"${_restore_start_time}\",\"RestoreStopTime\":\"${_restore_stop_time}\",\"InstanceType\":\"${_instance_type}\",\"Region\":\"${_region}\"}"
  curl -H "${_headers}" -X POST -d '{"TimeStamp":'${_rtime}',"UUID":'${_uuid}',"Solution":"SO0031R","Data":'${_metric}'}' ${_url}
  echo "-- $(date -u +%FT%T) -- post metric status: $?"

  #
  # notify customer with restore status
  # parameters : [_sns_topic, _source_efs, _backup_efs, _interval, _backup_num, _folder_label, _src_prefix, _s3bucket]
  #
  if [ "${restoreStatus}" == "0" ]; then
    echo "-- $(date -u +%FT%T) -- notify customer of success"
    aws sns publish --region ${_region} \
    --topic-arn ${_sns_topic} \
    --message '{
     SourceEFS:'${_source_efs}',
     BackupEFS:'${_backup_efs}',
     Interval:'${_interval}',
     BackupNum:'${_backup_num}',
     FolderLabel:'${_folder_label}',
     SourcePrefix:'${_src_prefix}',
     LogBucket:'${_s3bucket}',
     RestoreStartTime:'${_restore_start_time}',
     RestoreStopTime:'${_restore_stop_time}',
     RestoreStatus:Success
    }'
  else
    echo "-- $(date -u +%FT%T) -- notify customer of failure"
    aws sns publish --region ${_region} \
    --topic-arn ${_sns_topic} \
    --message '{
     SourceEFS:'${_source_efs}',
     BackupEFS:'${_backup_efs}',
     Interval:'${_interval}',
     BackupNum:'${_backup_num}',
     FolderLabel:'${_folder_label}',
     SourcePrefix:'${_src_prefix}',
     LogBucket:'${_s3bucket}',
     RestoreStartTime:'${_restore_start_time}',
     RestoreStopTime:'${_restore_stop_time}',
     RestoreStatus:Fail
    }'
  fi
  echo "send notification to customer, status: $?"
fi

#
# uploading cloud init logs to s3
# parameters : [_s3bucket, _folder_label]
#
aws s3 cp /var/log/cloud-init-output.log s3://${_s3bucket}/ec2-logs/${_folder_label}-${_interval}.${_backup_num}-restore-`date +%Y%m%d-%H%M`.log
echo "-- $(date -u +%FT%T) -- upload ec2 cloud init logs to S3, status: $?"

#
# changing auto scaling capacity
# parameters : [_asg_name, _instance_id, _region]
#
_asg_name=$(aws ec2 describe-tags --region ${_region} --filters "Name=resource-id,Values=${_instance_id}" --query 'Tags[?Key==`aws:autoscaling:groupName`]'.Value --output text)
aws autoscaling set-desired-capacity --region ${_region} --auto-scaling-group-name ${_asg_name} --desired-capacity 0
echo "-- $(date -u +%FT%T) -- autoscaling desired capacity changed, status: $?"
