set -e
./configure --prefix=/usr/local \
  --localstatedir=/var/lib/locate \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess)
make
make DESTDIR=$LFS install
