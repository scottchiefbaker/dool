#!/usr/bin/bash

START_DIR=$(pwd)
red="\033[1;31m"
white="\033[1;37m"
reset="\033[0m"

# Find and change to the build script dir so the rest of our
# commands can use relative paths
BUILD_SCRIPT_FILE=$(realpath $0)
BUILD_SCRIPT_PATH=$(dirname $BUILD_SCRIPT_FILE=)
cd $BUILD_SCRIPT_PATH

# Extract the dool version from the primary script
DOOL_PATH=$(realpath ../../dool)
VERSION=$(grep '__version__ = ' $DOOL_PATH | sed -E "s/.*'([^']+)'.*/\1/")

if [[ -z $VERSION ]]; then
	echo "Version string not found in $DOOL_PATH script"
	exit
else
	echo "Found dool version $VERSION"
fi

TMP_DIR=/var/tmp/dool-$VERSION
echo "Setting up build environment in $TMP_DIR"
echo

# Set the version string in the control file
sed -i "s/Version: .*/Version: $VERSION/g" control

# Build a temporary build directory and copy files to it appropriately
rm -Rf $TMP_DIR
mkdir $TMP_DIR
mkdir $TMP_DIR/DEBIAN/
cp -a * $TMP_DIR/DEBIAN/
cp -a ../../* $TMP_DIR

cd /var/tmp/

dpkg-deb --build dool-$VERSION

echo -e $white
echo -e "* Debian build successful: $reset"
ls --color --human --size -l /var/tmp/dool-$VERSION.deb

# Change back to the original directory
cd $START_DIR

rm --preserve-root -Rf $TMP_DIR
