set -e
./configure --prefix=/temp-tools \
  --without-guile \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess)
make
make DESTDIR=$LFS install
