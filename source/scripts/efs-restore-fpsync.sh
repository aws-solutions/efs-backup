#!/bin/bash

# input arguments
source=$1 #source_ip:/prefix
backup=$2 #backup_ip:/
interval=$3
backupNum=$4
efsid=$5
s3bucket=$6

# prepare system for fpsync
echo "-- $(date -u +%FT%T) -- sudo yum -y update"
sudo yum -y update
echo "-- $(date -u +%FT%T) -- sudo yum -y install nfs-utils"
sudo yum -y install nfs-utils

echo "-- $(date -u +%FT%T) -- sudo yum -y groupinstall 'Development Tools'"
sudo yum -y groupinstall "Development Tools"
echo "-- $(date -u +%FT%T) -- wget https://s3.amazonaws.com/%TEMPLATE_BUCKET_NAME%/efs-backup/latest/fpart.zip"
wget https://s3.amazonaws.com/%TEMPLATE_BUCKET_NAME%/efs-backup/latest/fpart.zip
unzip fpart.zip
cd fpart-fpart-0.9.3/
autoreconf -i
./configure
make
sudo make install

# Adding PATH
PATH=$PATH:/usr/local/bin


echo '-- $(date -u +%FT%T) -- sudo mkdir /mnt/source'
sudo mkdir /mnt/source
echo '-- $(date -u +%FT%T) -- sudo mkdir /mnt/backups'
sudo mkdir /mnt/backups
echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $source /mnt/source"
sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $source /mnt/source
echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $backup /mnt/backups"
sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $backup /mnt/backups

if [ ! sudo test -d /mnt/backups/$efsid/$interval.$backupNum/ ]; then
  echo "EFS Backup $efsid/$interval.$backupNum does not exist!"
  exit 1
fi

# ECU Count per instance
# c4.large = 8
# c4.xlarge = 16
# c4.2xlarge = 31
# c4.4xlarge = 62

_instance_type=$(curl http://169.254.169.254/latest/meta-data/instance-type/)

if [ "$_instance_type" == "c4.large" ]; then
    _thread_count=8
elif [ "$_instance_type" == "c4.xlarge" ]; then
    _thread_count=16
elif [ "$_instance_type" == "c4.2xlarge" ]; then
    _thread_count=31
elif [ "$_instance_type" == "c4.4xlarge" ]; then
    _thread_count=62
elif [ "$_instance_type" == "r4.large" ]; then
    _thread_count=7
elif [ "$_instance_type" == "r4.xlarge" ]; then
    _thread_count=13
elif [ "$_instance_type" == "m3.medium" ]; then
    _thread_count=3
else _thread_count=4
fi

# running fpsync in reverse direction to restore
echo "fpsync_start:$(date -u +%FT%T)"
echo "-- $(date -u +%FT%T) -- sudo \"PATH=$PATH\" /usr/local/bin/fpsync -n $_thread_count -v -o \"-a --stats --numeric-ids --log-file=/tmp/efs-restore.log\" /mnt/backups/$efsid/$interval.$backupNum/ /mnt/source/"
sudo "PATH=$PATH" /usr/local/bin/fpsync -n $_thread_count -v -o "-a --stats --numeric-ids --log-file=/tmp/efs-restore.log" /mnt/backups/$efsid/$interval.$backupNum/ /mnt/source/
fpsyncStatus=$?
echo "fpsync_stop:$(date -u +%FT%T)"

echo "rsync_start:$(date -u +%FT%T)"
echo "-- $(date -u +%FT%T) -- sudo rsync -r --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-restore-rsync.log /mnt/backups/$efsid/$interval.$backupNum/ /mnt/source/"
sudo rsync -r --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-restore-rsync.log /mnt/backups/$efsid/$interval.$backupNum/ /mnt/source/

echo "rsync_stop:$(date -u +%FT%T)"

exit $fpsyncStatus
