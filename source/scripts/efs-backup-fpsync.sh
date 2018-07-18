#!/bin/bash
# Example would be to run this script as follows:
# Once a day; retain last 31 days
# efs-backup.sh $src $dst daily 31 efs-12345
# Once a week; retain 4 weeks of backup
# efs-backup.sh $src $dst weekly 7 efs-12345
# Once a month; retain 3 months of backups
# efs-backup.sh $src $dst monthly 3 efs-12345
#
# Snapshots will look like:
# $dst/$efsid/hourly.0-3; daily.0-30; weekly.0-3; monthly.0-2


# input arguments
source=$1 #source_ip:/prefix
destination=$2 #destination_ip:/
interval=$3
retain=$4
efsid=$5
region=$6
instance_id=$7

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

echo "-- $(date -u +%FT%T) -- sudo mkdir /backup"
sudo mkdir /backup
echo "-- $(date -u +%FT%T) -- sudo mkdir /mnt/backups"
sudo mkdir /mnt/backups

echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $source /backup"
sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $source /backup
mount_src_status=$?
echo "mount status for source efs: ${mount_src_status}"

echo "-- $(date -u +%FT%T) -- sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $destination /mnt/backups"
sudo mount -t nfs -o nfsvers=4.1 -o rsize=1048576 -o wsize=1048576 -o timeo=600 -o retrans=2 -o hard $destination /mnt/backups
mount_backup_status=$?
echo "mount status for backup efs: ${mount_backup_status}"

# if efs mount fails exit workflow
if [ ${mount_src_status} != '0' ] || [ ${mount_backup_status} != '0' ]; then
  echo "-- $(date -u +%FT%T) -- ERROR:efs_not_mounted"
  exit $?
fi

echo "-- $(date -u +%FT%T) -- sudo yum -y install parallel"
sudo yum -y install parallel
echo "-- $(date -u +%FT%T) -- sudo yum -y install --enablerepo=epel tree"
sudo yum -y install --enablerepo=epel tree
echo "-- $(date -u +%FT%T) -- sudo yum -y groupinstall 'Development Tools'"
sudo yum -y groupinstall "Development Tools"
echo "-- $(date -u +%FT%T) -- wget https://s3.amazonaws.com/solutions-features-reference/efs-backup/latest/fpart.zip"
wget https://s3.amazonaws.com/solutions-features-reference/efs-backup/latest/fpart.zip
unzip fpart.zip
cd fpart-fpart-0.9.3/
autoreconf -i
./configure
make
sudo make install

# Adding PATH
PATH=$PATH:/usr/local/bin

_thread_count=$(($(nproc --all) * 16))

# we need to decrement retain because we start counting with 0 and we need to remove the oldest backup
echo "remove_snapshot_start:$(date -u +%FT%T)"
let "retain=$retain-1"
if sudo test -d /mnt/backups/$efsid/$interval.$retain; then
  echo "-- $(date -u +%FT%T) -- sudo tree /mnt/backups/$efsid/$interval.$retain -dfi | parallel --no-notice -j $_thread_count sudo rm {} -r &>/dev/null"
  sudo tree /mnt/backups/$efsid/$interval.$retain -dfi | parallel --will-cite -j $_thread_count sudo rm {} -r &>/dev/null
  echo "-- $(date -u +%FT%T) -- sudo rm /mnt/backups/$efsid/$interval.$retain -r &>/dev/null"
  sudo rm /mnt/backups/$efsid/$interval.$retain -r &>/dev/null
  echo "rm status: $?"
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
  echo "-- $(date -u +%FT%T) --  sudo \"PATH=$PATH\" /usr/local/bin/fpsync -n $_thread_count -o \"-a -v --link-dest=../`basename /mnt/backups/$efsid/$interval.0`\" /mnt/backups/$efsid/$interval.0 /mnt/backups/$efsid/$interval.1"
  sudo "PATH=$PATH" /usr/local/bin/fpsync -n $_thread_count -o "-a -v --link-dest=../`basename /mnt/backups/$efsid/$interval.0`" /mnt/backups/$efsid/$interval.0 /mnt/backups/$efsid/$interval.1
fi
echo "create_snapshot_stop:$(date -u +%FT%T)"

if [ ! -d /mnt/backups/$efsid ]; then
  echo "-- $(date -u +%FT%T) --  sudo mkdir -p /mnt/backups/$efsid"
  sudo mkdir -p /mnt/backups/$efsid
  echo "-- $(date -u +%FT%T) --  sudo chmod 700 /mnt/backups/$efsid"
  sudo chmod 700 /mnt/backups/$efsid
fi

echo "-- $(date -u +%FT%T) --  sudo rm /tmp/efs-backup.log"
sudo rm /tmp/efs-backup.log

# start fpsync process
echo "Stating backup....."
echo "-- $(date -u +%FT%T) --  sudo \"PATH=$PATH\" /usr/local/bin/fpsync -n $_thread_count -o \"-a --stats --numeric-ids --log-file=/tmp/efs-backup.log\" /backup/ /mnt/backups/$efsid/$interval.0/"
sudo "PATH=$PATH" /usr/local/bin/fpsync -n $_thread_count -v -o "-a --stats --numeric-ids --log-file=/tmp/efs-backup.log" /backup/ /mnt/backups/$efsid/$interval.0/ 1>/tmp/efs-fpsync.log
fpsyncStatus=$?
echo "fpsyncStatus:$fpsyncStatus"

# removing files from target efs which are not in source
echo "rsync_delete_start:$(date -u +%FT%T)"
echo "-- $(date -u +%FT%T) -- sudo rsync -r --delete --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-backup-rsync.log  /backup/ /mnt/backups/$efsid/$interval.0/"
sudo rsync -r --delete --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-backup-rsync.log  /backup/ /mnt/backups/$efsid/$interval.0/
rsyncDeleteStatus=$?
echo "rsyncDeleteStatus:$rsyncDeleteStatus"
echo "rsync_delete_stop:$(date -u +%FT%T)"
echo "-- $(date -u +%FT%T) -- sudo touch /mnt/backups/$efsid/$interval.0/"
sudo touch /mnt/backups/$efsid/$interval.0/

exit $fpsyncStatus
