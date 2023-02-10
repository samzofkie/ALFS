set -e
sed -i 's/extras//' Makefile.in
./configure --prefix=/usr/local \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess)
make
make DESTDIR=$LFS install
