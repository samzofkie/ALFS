set -e
./configure --prefix=/usr/local --host=$LFS_TGT
make
make DESTDIR=$LFS install
