set -e
./configure --prefix=/temp-tools --host=$LFS_TGT
make
make DESTDIR=$LFS install
