set -e
sed -i 's/extras//' Makefile.in
./configure --prefix=/temp-tools \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess)
make
make DESTDIR=$LFS install
