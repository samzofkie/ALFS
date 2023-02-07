set -e
./configure --prefix=/temp-tools \
  --localstatedir=/var/lib/locate \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess)
make
make DESTDIR=$LFS install
