#!/bin/bash

# input arguments
source=$1 #source_ip:/prefix
backup=$2 #backup_ip:/
interval=$3
backupNum=$4
efsid=$5
subdir=$6
s3bucket=$7

# prepare system for fpsync
echo "-- $(date -u +%FT%T) -- sudo yum -y update"
sudo yum -y update
echo "-- $(date -u +%FT%T) -- sudo yum -y install nfs-utils"
sudo yum -y install nfs-utils
echo "-- $(date -u +%FT%T) -- sudo yum -y groupinstall 'Development Tools'"
sudo yum -y groupinstall "Development Tools"
echo '-- $(date -u +%FT%T) -- wget https://github.com/martymac/fpart/archive/fpart-1.0.0.zip'
wget https://github.com/martymac/fpart/archive/fpart-1.0.0.zip
unzip fpart-1.0.0.zip
cd fpart-fpart-1.0.0/
autoreconf -i
./configure
make
sudo make install

# Adding PATH
PATH=$PATH:/usr/local/bin


_thread_count=$(($(nproc --all) * 16))

# 12/28/2018 - EFS-21432 - EFS mount best practices
echo '-- $(date -u +%FT%T) -- sudo mkdir /mnt/source'
sudo mkdir /mnt/source
echo '-- $(date -u +%FT%T) -- sudo mkdir /mnt/backups'
sudo mkdir /mnt/backups
echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,timeo=600,retrans=2,hard,_netdev,noresvport $source /mnt/source"
sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,timeo=600,retrans=2,hard,_netdev,noresvport $source /mnt/source
echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,timeo=600,retrans=2,hard,_netdev,noresvport $backup /mnt/backups"
sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,timeo=600,retrans=2,hard,_netdev,noresvport $backup /mnt/backups

if [ ! sudo test -d /mnt/backups/$efsid/$interval.$backupNum/ ]; then
  echo "EFS Backup $efsid/$interval.$backupNum does not exist!"
  exit 1
fi

# running fpsync in reverse direction to restore
echo "fpsync_start:$(date -u +%FT%T)"
echo "-- $(date -u +%FT%T) -- sudo \"PATH=$PATH\"  /usr/local/bin/fpsync -n $_thread_count -v -o \"-a --stats --numeric-ids --log-file=/tmp/efs-restore.log\" /mnt/backups/$efsid/$interval.$backupNum$subdir /mnt/source/"
sudo "PATH=$PATH"  /usr/local/bin/fpsync -n $_thread_count -v -o "-a --stats --numeric-ids --log-file=/tmp/efs-restore.log" /mnt/backups/$efsid/$interval.$backupNum$subdir /mnt/source/
fpsyncStatus=$?
echo "fpsync_stop:$(date -u +%FT%T)"

echo "rsync_delete_start:$(date -u +%FT%T)"
echo "-- $(date -u +%FT%T) -- sudo rsync -r --delete --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-restore-rsync.log /mnt/backups/$efsid/$interval.$backupNum$subdir /mnt/source/"
sudo rsync -r --delete --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-restore-rsync.log /mnt/backups/$efsid/$interval.$backupNum$subdir /mnt/source/
echo "rsync_delete_stop:$(date -u +%FT%T)"

exit $fpsyncStatus
