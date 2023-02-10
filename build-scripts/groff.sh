set -e
PAGE=letter ./configure --prefix=/usr
make -j1
make install
