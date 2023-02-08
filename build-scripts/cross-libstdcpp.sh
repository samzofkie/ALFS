set -e
mkdir -v build
cd build
../libstdc++-v3/configure \
  --host=$LFS_TGT \
  --build=$(../config.guess) \
  --prefix=/cross-tools \
  --disable-multilib \
  --disable-nls \
  --disable-libstdcxx-pch \
  --with-gxx-include-dir=/cross-tools/$LFS_TGT/include/c++/12.2.0
make
make DESTDIR=$LFS install
rm -v $LFS/cross-tools/lib/libstdc++.la
rm -v $LFS/cross-tools/lib/libstdc++fs.la
rm -v $LFS/cross-tools/lib/libsupc++.la
