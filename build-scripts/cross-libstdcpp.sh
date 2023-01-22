set -e
mkdir -v build
cd build
../libstdc++-v3/configure \
  --host=$LFS_TGT \
  --build=$(../config.guess) \
  --prefix=/usr \
  --disable-multilib \
  --disable-nls \
  --disable-libstdcxx-pch \
  --with-gxx-include-dir=/tools/$LFS_TGT/include/c++/12.2.0
make
make DESTDIR=$LFS install
rm -v $LFS/usr/lib/libstdc++.la
rm -v $LFS/usr/lib/libstdc++fs.la
rm -v $LFS/usr/lib/libsupc++.la
