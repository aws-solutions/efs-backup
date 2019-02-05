#!/bin/bash
#========================================================================
#
# ec2 ssm script
# stops fpsync process
# uploads logs to S3
# updates status on DynamoDB
# completes lifecycle hook
#
#========================================================================
# author: aws-solutions-builder@

_az=$(curl http://169.254.169.254/latest/meta-data/placement/availability-zone/)
_region=${_az::-1}
_instance_id=$(curl http://169.254.169.254/latest/meta-data/instance-id)
_hook_result="CONTINUE"

#
# uploading cloud-init and fpsync log to s3 before stopping fpsync process
# parameters : [_s3bucket, _folder_label]
#
echo "-- $(date -u +%FT%T) -- uploading cloud init logs"
_ec2log=$(date +%Y%m%d-%H%M)
aws s3 cp /var/log/cloud-init-output.log s3://${_s3bucket}/ec2-logs/${_folder_label}-backup-$_ec2log.log
echo "-- $(date -u +%FT%T) -- upload ec2 cloud init logs to S3, status: $?"
_log_location=https://s3.amazonaws.com/${_s3bucket}/ec2-logs/${_folder_label}-backup-$_ec2log.log

# find if efs mounted successfully
_err_61=$(cat /var/log/cloud-init-output.log | grep 'efs_mount_ip_not_found' | cut -d: -f4)
_err_62=$(cat /var/log/cloud-init-output.log | grep 'efs_not_mounted' | cut -d: -f4)

if [ "$_err_61" != "efs_mount_ip_not_found" ] && [ "$_err_62" != "efs_not_mounted" ] ; then

  echo "-- $(date -u +%FT%T) -- uploading backup (fpsync) logs"
  aws s3 cp /tmp/efs-backup.log s3://${_s3bucket}/efs-backup-logs/${_folder_label}-backup-fpsync-`date +%Y%m%d-%H%M`.log
  echo "-- $(date -u +%FT%T) -- upload backup fpsync logs to S3 status: $?"

  # uploading backup (rsync delete) log to s3
  echo "-- $(date -u +%FT%T) -- uploading backup (rsync delete) logs"
  aws s3 cp /tmp/efs-backup-rsync.log s3://${_s3bucket}/efs-backup-logs/${_folder_label}-backup-rsync-delete-`date +%Y%m%d-%H%M`.log
  echo "-- $(date -u +%FT%T) -- upload rsync delete logs to S3 status: $?"

  #
  # kill fpsync process with SIGINT, wait until background processes complete
  # parameters : [_fpsync_pid]
  #
  _fpsync_pid=$(head -1 /tmp/efs-fpsync.log | awk '{print $4}' | awk -F '-' '{print $2}')
  echo "-- $(date -u +%FT%T) -- fpsync foreground process-id: $_fpsync_pid"

  sudo kill -SIGTERM $_fpsync_pid
  echo "-- $(date -u +%FT%T) -- kill with SIGTERM, status: $?"

  if sudo test -e /tmp/efs-fpsync.log; then
    echo "-- $(date -u +%FT%T) -- /tmp/efs-fpsync.log exists"
    echo "-- $(date -u +%FT%T) -- uploading fpsync output logs"
    aws s3 cp /tmp/efs-fpsync.log s3://${_s3bucket}/efs-backup-logs/${_folder_label}-fpsync-output-`date +%Y%m%d-%H%M`.log
    echo "-- $(date -u +%FT%T) -- upload fpsync output logs to S3 status: $?"
  else
    echo "-- $(date -u +%FT%T) -- /tmp/efs-fpsync.log file does not exist"
    # this means cp -al did not complete or fpsync process did not initiate
    _finish_time=$(date -u +%FT%T)
    echo "-- $(date -u +%FT%T) -- workflow finish time: $_finish_time"
    echo "-- $(date -u +%FT%T) -- backup unsuccessful (id: ${_backup_id})"
    aws dynamodb update-item --table-name ${_ddb_table_name} --key '{"BackupId":{"S":"'${_backup_id}'"}}' --update-expression "SET BackupStatus = :q, BackupStopTime = :t, EC2Logs = :log" --expression-attribute-values '{":q": {"S":"fpsync failed"}, ":t": {"S":"'$_finish_time'"}, ":log": {"S":"'$_log_location'"}}' --region $_region
    # udpate lifecycle hook and exit ssm script
    echo "-- $(date -u +%FT%T) -- updating lifecycle hook"
    aws autoscaling complete-lifecycle-action --lifecycle-hook-name ${_lifecycle_hookname} --auto-scaling-group-name ${_autoscaling_grp_name} --lifecycle-action-result $_hook_result --instance-id $_instance_id --region $_region
    echo "-- $(date -u +%FT%T) -- lifecycle hook update status: $?"
    exit $?
  fi

  #
  # updating dynamo db with backup meta-data
  # parameters : [_nofs, _nfst, _tfs, _ttfs]
  #
  _nofs=$(cat /tmp/efs-backup.log | grep 'Number of files' | awk '{nofs += $7} END {print nofs}')
  if [[ -z $_nofs ]] ; then
    _nofs=0
  fi
  echo "-- $(date -u +%FT%T) -- Number of files: $_nofs"

  _nfst=$(cat /tmp/efs-backup.log | grep 'Number of files transferred' | awk '{nfst += $8} END {print nfst}')
  if [[ -z $_nfst ]] ; then
    _nfst=0
  fi
  echo "-- $(date -u +%FT%T) -- Number of files transferred: $_nfst"

  _tfs=$(cat /tmp/efs-backup.log | grep 'Total file size' | awk '{tfs += $7} END {print tfs}')
  if [[ -z $_tfs ]] ; then
    _tfs=0
  fi
  echo "-- $(date -u +%FT%T) -- Total file size: $_tfs"

  _ttfs=$(cat /tmp/efs-backup.log | grep 'Total transferred file size' | awk '{ttfs += $8} END {print ttfs}')
  if [[ -z $_ttfs ]] ; then
    _ttfs=0
  fi
  echo "-- $(date -u +%FT%T) -- Total transferred file size: $_ttfs"

  # timestamps for (rm -rf) and (hardlink) file operations
  _rm_start=$(cat /var/log/cloud-init-output.log | grep 'remove_snapshot_start' | cut -d: -f2-)
  _rm_stop=$(cat /var/log/cloud-init-output.log | grep 'remove_snapshot_stop' | cut -d: -f2-)
  _hl_start=$(cat /var/log/cloud-init-output.log | grep 'create_snapshot_start' | cut -d: -f2-)
  _hl_stop=$(cat /var/log/cloud-init-output.log | grep 'create_snapshot_stop' | cut -d: -f2-)

  #
  # getting burst credit balance from Source EFS
  # parameters : [_source_efs]
  #
  _mtime1=$(date --date '30 minutes ago' +%FT%T)
  _mtime2=$(date -u +%FT%T)
  _src_efs_credit_balance=$(aws cloudwatch get-metric-statistics --namespace AWS/EFS --region $_region --metric-name BurstCreditBalance --period 300 --statistics Average --dimensions Name=FileSystemId,Value=${_source_efs} --start-time $_mtime1 --end-time $_mtime2 --query Datapoints[0].['Average'] --output text)
  echo "-- $(date -u +%FT%T) -- source efs BurstCreditBalance after backup: $_src_efs_credit_balance"
  if [[ -z $_src_efs_credit_balance ]] ; then
    _src_efs_credit_balance=0
  fi

  # getting fpsync and rsync status
  fpsyncStatus=$(cat /var/log/cloud-init-output.log | grep 'fpsyncStatus' | cut -d: -f2-)
  echo "fpsyncStatus: $fpsyncStatus"
  rsyncDeleteStatus=$(cat /var/log/cloud-init-output.log | grep 'rsyncDeleteStatus' | cut -d: -f2-)
  echo "rsync delete status: $rsyncDeleteStatus"

  _finish_time=$(date -u +%FT%T)
  echo "-- $(date -u +%FT%T) -- backup finish time: $_finish_time"

  # update Dynamo DB Table with backup status
  if [ "$fpsyncStatus" == "0" ] && [ "$rsyncDeleteStatus" == "0" ] ; then
    echo "-- $(date -u +%FT%T) -- backup completed successfully (id: ${_backup_id})"
    _rsync_delete_start=$(cat /var/log/cloud-init-output.log | grep 'rsync_delete_start' | cut -d: -f2-)
    _rsync_delete_stop=$(cat /var/log/cloud-init-output.log | grep 'rsync_delete_stop' | cut -d: -f2-)
    aws dynamodb update-item --table-name ${_ddb_table_name} --key '{"BackupId":{"S":"'${_backup_id}'"}}' --update-expression "SET BackupStatus = :q, NumberOfFiles = :n1, NumberOfFilesTransferred = :n2, TotalFileSize = :f1, TotalTransferredFileSize = :f2, BackupStopTime = :t, RemoveSnapshotStartTime = :rm1, RemoveSnapshotStopTime = :rm2, CreateHardlinksStartTime = :hl1, CreateHardlinksStopTime = :hl2, RsyncDeleteStartTime = :rd1, RsyncDeleteStopTime = :rd2, SourceBurstCreditBalancePostBackup = :cb1, EC2Logs = :log" --expression-attribute-values '{":q": {"S":"Success"}, ":n1": {"N":"'$_nofs'"}, ":n2": {"N":"'$_nfst'"}, ":f1": {"N":"'$_tfs'"}, ":f2": {"N":"'$_ttfs'"}, ":t": {"S":"'$_finish_time'"}, ":rm1": {"S":"'$_rm_start'"}, ":rm2": {"S":"'$_rm_stop'"}, ":hl1": {"S":"'$_hl_start'"}, ":hl2": {"S":"'$_hl_stop'"}, ":rd1": {"S":"'$_rsync_delete_start'"}, ":rd2": {"S":"'$_rsync_delete_stop'"}, ":cb1": {"N":"'$_src_efs_credit_balance'"}, ":log": {"S":"'$_log_location'"}}' --region $_region
    echo "-- $(date -u +%FT%T) -- dynamo db update status: $?"
  elif [ "$fpsyncStatus" == "0" ] && [ "$rsyncDeleteStatus" != "0" ] ; then
    echo "-- $(date -u +%FT%T) -- rsync delete incomplete (id: ${_backup_id})"
    aws dynamodb update-item --table-name ${_ddb_table_name} --key '{"BackupId":{"S":"'${_backup_id}'"}}' --update-expression "SET BackupStatus = :q, NumberOfFiles = :n1, NumberOfFilesTransferred = :n2, TotalFileSize = :f1, TotalTransferredFileSize = :f2, BackupStopTime = :t, RemoveSnapshotStartTime = :rm1, RemoveSnapshotStopTime = :rm2, CreateHardlinksStartTime = :hl1, CreateHardlinksStopTime = :hl2, SourceBurstCreditBalancePostBackup = :cb1, EC2Logs = :log" --expression-attribute-values '{":q": {"S":"Rsync Delete Incomplete"}, ":n1": {"N":"'$_nofs'"}, ":n2": {"N":"'$_nfst'"}, ":f1": {"N":"'$_tfs'"}, ":f2": {"N":"'$_ttfs'"}, ":t": {"S":"'$_finish_time'"}, ":rm1": {"S":"'$_rm_start'"}, ":rm2": {"S":"'$_rm_stop'"}, ":hl1": {"S":"'$_hl_start'"}, ":hl2": {"S":"'$_hl_stop'"}, ":cb1": {"N":"'$_src_efs_credit_balance'"}, ":log": {"S":"'$_log_location'"}}' --region $_region
    echo "-- $(date -u +%FT%T) -- dynamo db update status: $?"
  else
    echo "-- $(date -u +%FT%T) -- backup incomplete (id: ${_backup_id})"
    aws dynamodb update-item --table-name ${_ddb_table_name} --key '{"BackupId":{"S":"'${_backup_id}'"}}' --update-expression "SET BackupStatus = :q, NumberOfFiles = :n1, NumberOfFilesTransferred = :n2, TotalFileSize = :f1, TotalTransferredFileSize = :f2, BackupStopTime = :t, RemoveSnapshotStartTime = :rm1, RemoveSnapshotStopTime = :rm2, CreateHardlinksStartTime = :hl1, CreateHardlinksStopTime = :hl2, SourceBurstCreditBalancePostBackup = :cb1, EC2Logs = :log" --expression-attribute-values '{":q": {"S":"Incomplete"}, ":n1": {"N":"'$_nofs'"}, ":n2": {"N":"'$_nfst'"}, ":f1": {"N":"'$_tfs'"}, ":f2": {"N":"'$_ttfs'"}, ":t": {"S":"'$_finish_time'"}, ":rm1": {"S":"'$_rm_start'"}, ":rm2": {"S":"'$_rm_stop'"}, ":hl1": {"S":"'$_hl_start'"}, ":hl2": {"S":"'$_hl_stop'"}, ":cb1": {"N":"'$_src_efs_credit_balance'"}, ":log": {"S":"'$_log_location'"}}' --region $_region
    echo "-- $(date -u +%FT%T) -- dynamo db update status: $?"
  fi

fi

# update Dynamo DB Table with backup status
if [ "$_err_61" == "efs_mount_ip_not_found" ] || [ "$_err_62" == "efs_not_mounted" ] ; then
  _finish_time=$(date -u +%FT%T)
  echo "-- $(date -u +%FT%T) -- workflow finish time: $_finish_time"
  echo "-- $(date -u +%FT%T) -- backup unsuccessful (id: ${_backup_id})"
  aws dynamodb update-item --table-name ${_ddb_table_name} --key '{"BackupId":{"S":"'${_backup_id}'"}}' --update-expression "SET BackupStatus = :q, BackupStopTime = :t, EC2Logs = :log" --expression-attribute-values '{":q": {"S":"Unsuccessful"}, ":t": {"S":"'$_finish_time'"}, ":log": {"S":"'$_log_location'"}}' --region $_region
fi

#
# update lifecycle hook with completion
# parameters : [_lifecycle_hookname, _autoscaling_grp_name, _hook_result, _instance_id, _region]
#
echo "-- $(date -u +%FT%T) -- updating lifecycle hook"
aws autoscaling complete-lifecycle-action --lifecycle-hook-name ${_lifecycle_hookname} --auto-scaling-group-name ${_autoscaling_grp_name} --lifecycle-action-result $_hook_result --instance-id $_instance_id --region $_region
echo "-- $(date -u +%FT%T) -- lifecycle hook update status: $?"
