#!/bin/bash
# use this script for merging all modules to a single file
#

main_file_name=media_download.py

mkdir -p release
utils/build.py ./$main_file_name release/$main_file_name
chmod u+x release/$main_file_name