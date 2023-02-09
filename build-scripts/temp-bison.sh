set -e
./configure --prefix=/temp-tools \
  --docdir=/usr/share/doc/bison-3.8.2
make
make install
