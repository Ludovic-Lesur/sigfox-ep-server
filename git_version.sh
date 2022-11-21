#!/bin/bash

sscanf() {
	local str="$1"
	local format="$2"
	[[ "$str" =~ $format ]]
}

# Create file.
touch version.py

# Get current date.
date=`date -R`

# Execute git commands.
git_version=`git describe --long --always`
diff=`git diff`

# Extract fields
sscanf $git_version "SW(.+).(.+)-(.+)-g(.+)"

# Manage dirty flag.
dirty_flag=0
if [[ $diff ]]; then
	dirty_flag=1
fi

echo "#" > version.py
echo "# version.py" >> version.py
echo "#" >> version.py
echo "# Auto-generated on: $date" >> version.py
echo "# Author: Ludo" >> version.py
echo "#" >> version.py
echo "" >> version.py
echo "GIT_VERSION =       	\"$git_version\"" >> version.py
echo "GIT_MAJOR_VERSION = 	${BASH_REMATCH[1]}" >> version.py
echo "GIT_MINOR_VERSION =	${BASH_REMATCH[2]}" >> version.py
echo "GIT_COMMIT_INDEX =	${BASH_REMATCH[3]}" >> version.py
echo "GIT_COMMIT_ID =    	0x${BASH_REMATCH[4]}" >> version.py
echo "GIT_DIRTY_FLAG =   	$dirty_flag" >> version.py
echo "" >> version.py

chmod 777 version.py
