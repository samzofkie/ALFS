set -e
./configure --prefix=/temp-tools \
  --enable-shared \
  --without-ensurepip
make
make install
