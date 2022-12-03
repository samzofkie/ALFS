#!/usr/bin/env -S -i bash

wget https://mirror.download.it/lfs/pub/lfs/lfs-packages/11.2/wget-list
wget --input-file=wget-list --continue
rm wget-list
echo done downloading
