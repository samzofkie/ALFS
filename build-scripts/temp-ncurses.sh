#!/bin/bash
set -e 

sed -i s/mawk// configure

mkdir build
pushd build
  ../configure
  make -C include
  make -C progs tic
popd

./configure --prefix=/usr/local \
  --host=$LFS_TGT \
  --build=$(./config.guess) \
  --mandir=/usr/local/share/man \
  --with-manpage-format=normal \
  --with-shared \
  --without-normal \
  --with-cxx-shared \
  --without-debug \
  --without-ada \
  --disable-stripping \
  --enable-widec
make
make DESTDIR=$LFS TIC_PATH=$(pwd)/build/progs/tic install

echo "INPUT(-lncursesw)" > $LFS/usr/local/lib/libncurses.so
