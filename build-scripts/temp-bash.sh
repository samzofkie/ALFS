set -e
./configure --prefix=/usr \
  --build=$(support/config.guess) \
  --host=$LFS_TGT \
  --without-bash-malloc
make
make DESTDIR=$LFS install
ln -sv bash `echo $LFS`bin/sh
