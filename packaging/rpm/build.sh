#!/usr/bin/bash

START_DIR=$(pwd)

# Find and change to the build script dir so the rest of our
# commands can use relative paths
BUILD_SCRIPT_FILE=$(realpath $0)
BUILD_SCRIPT_PATH=$(dirname $BUILD_SCRIPT_FILE=)
cd $BUILD_SCRIPT_PATH

red="\033[1;31m"
white="\033[1;37m"
reset="\033[0m"

# Extract the version number from the dool script
export VERSION=`perl -nE 'if (/__version__ = .*?([\.\d]+)/) { print $1; } ' ../../dool`

if [[ -z $VERSION ]]
then
	echo "Unable to extract version number from 'dool'"
	exit 5
fi

# Change the version number in the spec file
perl -pi -e "s/Version:.*/Version: $VERSION/" dool.spec

echo "Building version $VERSION";
sleep 1

# Build a tar archive of the current HEAD with the correct version number
cd ../../
git archive --format=tar --prefix=dool-$VERSION/ HEAD | gzip > /tmp/dool-$VERSION.tar.gz
mkdir -p ~/rpmbuild/SOURCES/
cp -a /tmp/dool-$VERSION.tar.gz ~/rpmbuild/SOURCES/
cd -

# Build the actual RPM
rpmbuild --target noarch -bb dool.spec

# Check if the build was a success
if [[ $? -eq 0 ]]
then
	echo -e $white
	echo -e "\n* RPM Build successful:$reset\n"
	mv ~/rpmbuild/RPMS/noarch/dool-$VERSION-1.noarch.rpm /var/tmp/
	ls --color -lsah /var/tmp/dool-$VERSION-1.noarch.rpm
else
	echo -e $red
	echo "Error building RPM... exit code $?"
fi

echo -e $reset

cd $START_DIR
