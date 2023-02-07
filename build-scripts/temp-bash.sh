set -e
./configure --prefix=/temp-tools \
  --build=$(support/config.guess) \
  --host=$LFS_TGT \
  --without-bash-malloc
make
make DESTDIR=$LFS install
ln -sv bash $LFS/bin/sh
