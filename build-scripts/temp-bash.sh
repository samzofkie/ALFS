set -e
./configure --prefix=/usr/local \
  --build=$(support/config.guess) \
  --host=$LFS_TGT \
  --without-bash-malloc
make
make DESTDIR=$LFS install
ln -sv bash $LFS/bin/sh
