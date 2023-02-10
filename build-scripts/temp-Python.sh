set -e
./configure --prefix=/usr/local \
  --enable-shared \
  --without-ensurepip
make
make install
