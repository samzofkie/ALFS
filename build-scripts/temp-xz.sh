set -e
./configure --prefix=/usr/local \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess) \
  --disable-static \
  --docdir=/usr/local/share/doc/xz-5.2.6
make
make DESTDIR=$LFS install
rm -v $LFS/usr/local/lib/liblzma.la
