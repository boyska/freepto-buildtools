#!/usr/bin/env bash
### given a directory, it will build the image inside, then put it under $WWW

WWW=/var/www/dev
BASEDIR=${1%/} #strip slash
LOCALE=${2:-it_IT.UTF-8}
TIMEZONE=${3:-Europe/Rome}
KEYMAP=${4:-it}
VARIANT=${5:-${LOCALE::2}}
DATEFMT='%y%m%d_%H.%M'
if [ -r /etc/http_proxy ]; then
	export http_proxy="$(cat /etc/http_proxy)"
else
	export http_proxy="http://localhost:3142/"
fi
echo "vado di proxy $http_proxy"
HEAD=""
imgname=""

# CHECK DISK SPACE
DISKLIMIT=80
diskusage=`df -H "$WWW"| tail -n1 | awk '{ print $5 }' | cut -d'%' -f1`
if [ "$diskusage" -gt "$DISKLIMIT" ]; then
        echo "[ABORT] There isn't enough disk space."
	echo "Disk usage: ${diskusage}% - Disk limit: ${DISKLIMIT}%"
	exit 1
fi


if [[ $# -lt 1 ]]; then
	echo "you must fill config\n $0 path locale timezone keymap"
	exit 1
fi
if ! [[ -d $1/.git ]]; then
	echo "repository does not exist, create it manually"
	exit 1
fi
cd $BASEDIR

test -d $BASEDIR || exit 1

export GIT_WORK_TREE=$BASEDIR
export GIT_DIR=$GIT_WORK_TREE/.git

HEAD=$(git rev-parse HEAD | head -c 6)
builddate=$(date +$DATEFMT)
commitdesc=$(git describe --tags --long)
imgdesc="${builddate}_$commitdesc-$VARIANT"
imgname="${WWW%/}/$(basename $BASEDIR)/${imgdesc}/${imgdesc}.img"
mkdir -p "${WWW%/}/$(basename $BASEDIR)/${imgdesc}"
echo "Target name will be $imgname"

if [[ -n "$(find ${WWW%/}/ -name "*_$HEAD-$VARIANT.img" -print -quit)" ]]; then
	echo "an image for $HEAD already exists: "
	ls -l ${WWW%/}/*_$HEAD-$VARIANT.img
	exit 1
else
	echo "ok, building $HEAD"
fi

set -e

mkdir -p /var/tmp/build
avail_mega=$(df -BM /var/tmp/build | awk '{ print $4 }' | tail -n1 | sed 's/[^0-9]//g')
if [ "$avail_mega" -lt 5000 ]; then
	echo "Too few disk space: $avail_mega MB, aborting" >&2
	exit 5
fi
workdir=$(mktemp -d /var/tmp/build/build_$(basename $BASEDIR).XXXXX)
rsync -r --links $BASEDIR/ $workdir/

cleanup()
{
	troubledir="/var/build/trouble"
	mkdir -p "$troubledir"
	if [ -d "$workdir" ]
	then
		echo "Something unexpected happened; you can find everything in $troubledir "
		mv $workdir "$troubledir"
		echo "Debug build in $troubledir/$(basename $workdir)"
	fi
}
trap cleanup EXIT

cd $workdir/
echo -n "sono in "
pwd

lb clean

mkdir -p /var/log/build
if [[ -x freepto-config.sh ]]; then
	if ! ./freepto-config.sh -l $LOCALE -z $TIMEZONE -k $KEYMAP 2>&1 | tee -a /var/log/build/$(basename $BASEDIR).log; then
		echo "errori nel config"
		cd ~
		#rm -rf $workdir
		exit 2
	fi
fi

if ! lb build 2>&1 | tee -a /var/log/build/$(basename $BASEDIR).log; then
	echo "errori nel build"
	cd ~
	#rm -rf $workdir
	exit 3
fi

if ! [ -f binary.img ];
then
	echo "binary not found"
	cd ~
	exit 4
fi


### "Extra" files
mv binary.contents ${imgname}.contents.txt
mv chroot.packages.live ${imgname}.packages.txt
git log -n 20 --decorate=short --stat > ${imgname}.history.txt
cat config/freepto config/freepto.local > ${imgname}.config.txt
mv build.log ${imgname}.log.txt
if [[ -r pkgs.log ]]; then
	mv pkgs.log ${imgname}.pkgs_log.txt
fi

### Image itself
mv binary.img $imgname
vboxmanage convertdd  ${imgname} ${imgname%.img}.vdi
sha512sum ${imgname} > ${imgname}.sha512sum.txt

cd ~
rm -rf $workdir

# remove old image on /var/www and /var/tmp/build/build*
find $WWW/ -type f -name "$(basename $BASEDIR)-*" -mtime +3 -delete
find /var/tmp/build/build* -type f -mtime +1 -delete



# vim: set ft=sh:
