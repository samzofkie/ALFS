set -e
./configure --prefix=/usr/local \
  --build=$(support/config.guess) \
  --host=$LFS_TGT \
  --without-bash-malloc
make
make DESTDIR=$LFS install
ln -sv bash usr/local/bin/sh
