set -e
./configure --prefix=/temp-tools \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess) \
  --disable-static \
  --docdir=/temp-tools/share/doc/xz-5.2.6
make
make DESTDIR=$LFS install
rm -v $LFS/temp-tools/lib/liblzma.la
