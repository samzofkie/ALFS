set -e
./configure --prefix=/usr/local \
  --without-guile \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess)
make
make DESTDIR=$LFS install
