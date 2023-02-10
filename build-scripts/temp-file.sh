#!/bin/bash
set -e
mkdir -v build
pushd build
../configure --disable-bzlib \
  --disable-libseccomp \
  --disable-xzlib \
  --disable-zlib
make
popd
./configure --prefix=/usr/local --host=$LFS_TGT --build=$(./config.guess)
make FILE_COMPILE=$(pwd)/build/src/file
make DESTDIR=$LFS install
rm -v $LFS/usr/local/lib/libmagic.la
