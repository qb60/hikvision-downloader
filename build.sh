#!/bin/bash
# use this script for merging all modules to a single file
#
mkdir -p release
utils/build.py ./video_download.py release/video_download.py
chmod u+x release/video_download.py