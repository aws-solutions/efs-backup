#!/bin/bash
# Example would be to run this script as follows:
# Every 6 hours; retain last 4 backups
# efs-backup.sh $src $dst hourly 4 efs-12345
# Once a day; retain last 31 days
# efs-backup.sh $src $dst daily 31 efs-12345
# Once a week; retain 4 weeks of backup
# efs-backup.sh $src $dst weekly 7 efs-12345
# Once a month; retain 3 months of backups
# efs-backup.sh $src $dst monthly 3 efs-12345
#
# Snapshots will look like:
# $dst/$efsid/hourly.0-3; daily.0-30; weekly.0-3; monthly.0-2

set -e # Exit on error

# input arguments
source=$1 #source_ip:/prefix
destination=$2 #destination_ip:/
interval=$3
retain=$4
efsid=$5

echo "## input from user ##"
echo "source: ${source}"
echo "destination: ${destination}"
echo "interval: ${interval}"
echo "retain: ${retain}"
echo "efsid: ${efsid}"

# prepare system for fpsync
echo "-- $(date -u +%FT%T) -- sudo yum -y update"
sudo yum -y update
echo "-- $(date -u +%FT%T) -- sudo yum -y install nfs-utils"
sudo yum -y install nfs-utils

echo "-- $(date -u +%FT%T) -- sudo yum -y groupinstall 'Development Tools'"
sudo yum -y groupinstall "Development Tools"
echo "-- $(date -u +%FT%T) -- wget https://s3.amazonaws.com/solutions-reference/efs-backup/latest/fpart.zip"
wget https://s3.amazonaws.com/solutions-reference/efs-backup/latest/fpart.zip
unzip fpart.zip
cd fpart-fpart-0.9.3/
autoreconf -i
./configure
make
sudo make install

# Adding PATH
PATH=$PATH:/usr/local/bin

echo "-- $(date -u +%FT%T) -- sudo mkdir /backup"
sudo mkdir /backup
echo "-- $(date -u +%FT%T) -- sudo mkdir /mnt/backups"
sudo mkdir /mnt/backups
echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $source /backup"
sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $source /backup
echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $destination /mnt/backups"
sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $destination /mnt/backups

# we need to decrement retain because we start counting with 0 and we need to remove the oldest backup
echo "remove_snapshot_start:$(date -u +%FT%T)"
let "retain=$retain-1"
if sudo test -d /mnt/backups/$efsid/$interval.$retain; then
  echo "-- $(date -u +%FT%T) -- sudo rm -rf /mnt/backups/$efsid/$interval.$retain"
  sudo rm -rf /mnt/backups/$efsid/$interval.$retain
fi
echo "remove_snapshot_stop:$(date -u +%FT%T)"

# rotate all previous backups (except the first one), up one level
for x in `seq $retain -1 2`; do
  if sudo test -d /mnt/backups/$efsid/$interval.$[$x-1]; then
    echo "-- $(date -u +%FT%T) -- sudo mv /mnt/backups/$efsid/$interval.$[$x-1] /mnt/backups/$efsid/$interval.$x"
    sudo mv /mnt/backups/$efsid/$interval.$[$x-1] /mnt/backups/$efsid/$interval.$x
  fi
done

echo "create_snapshot_start:$(date -u +%FT%T)"
# copy first backup with hard links, then replace first backup with new backup
if sudo test -d /mnt/backups/$efsid/$interval.0 ; then
  echo "-- $(date -u +%FT%T) --  sudo cp -al /mnt/backups/$efsid/$interval.0 /mnt/backups/$efsid/$interval.1"
  sudo cp -al /mnt/backups/$efsid/$interval.0 /mnt/backups/$efsid/$interval.1
fi
echo "create_snapshot_stop:$(date -u +%FT%T)"

if [ ! -d /mnt/backups/$efsid ]; then
  echo "-- $(date -u +%FT%T) --  sudo mkdir -p /mnt/backups/$efsid"
  sudo mkdir -p /mnt/backups/$efsid
  echo "-- $(date -u +%FT%T) --  sudo chmod 700 /mnt/backups/$efsid"
  sudo chmod 700 /mnt/backups/$efsid
fi

echo "-- $(date -u +%FT%T) --  sudo rm /tmp/efs-backup.log"
sudo rm -f /tmp/efs-backup.log

# ECU Count per instance
# c4.large = 8
# c4.xlarge = 16
# r4.large = 7
# r4.xlarge = 13
# m3.medium = 3

_instance_type=$(curl http://169.254.169.254/latest/meta-data/instance-type/)

if [ "$_instance_type" == "c4.large" ]; then
    _thread_count=8
elif [ "$_instance_type" == "c4.xlarge" ]; then
    _thread_count=16
elif [ "$_instance_type" == "r4.large" ]; then
    _thread_count=7
elif [ "$_instance_type" == "r4.xlarge" ]; then
    _thread_count=13
elif [ "$_instance_type" == "m3.medium" ]; then
    _thread_count=3
else _thread_count=4
fi

# start fpsync process
echo "Stating backup....."
echo "-- $(date -u +%FT%T) --  sudo \"PATH=$PATH\" /usr/local/bin/fpsync -n $_thread_count -o \"-a --stats --numeric-ids --log-file=/tmp/efs-backup.log\" /backup/ /mnt/backups/$efsid/$interval.0/"
sudo "PATH=$PATH" /usr/local/bin/fpsync -n $_thread_count -v -o "-a --stats --numeric-ids --log-file=/tmp/efs-backup.log" /backup/ /mnt/backups/$efsid/$interval.0/ 1>/tmp/efs-fpsync.log
fpsyncStatus=$?
echo "-- $(date -u +%FT%T) --  fpsync exit code was: [$fpsyncStatus]"
