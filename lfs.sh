#!/usr/bin/env -S -i bash

export LFS="/lfs"
cd $LFS
ls
mkdir sources && cd sources
./download-tarballs.sh&

echo yo
