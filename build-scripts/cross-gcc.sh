set -e
./contrib/download_prerequisites
sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64

SRC_DIR=$(pwd)
mkdir -v ../gcc-build
cd ../gcc-build

$SRC_DIR/configure \
  --target=$LFS_TGT \
  --prefix=$LFS/cross-tools \
  --with-glibc-version=2.36 \
  --with-sysroot=$LFS \
  --with-newlib \
  --without-headers \
  --disable-nls \
  --disable-shared \
  --disable-multilib \
  --disable-decimal-float \
  --disable-threads \
  --disable-libatomic \
  --disable-libgomp \
  --disable-libquadmath \
  --disable-libssp \
  --disable-libvtv \
  --disable-libstdcxx \
  --enable-languages=c,c++
make
make install

cd $SRC_DIR
rm -rf ../gcc-build
cat gcc/limitx.h gcc/glimits.h gcc/limity.h > \
  `dirname $($LFS_TGT-gcc -print-libgcc-file-name)`/install-tools/include/limits.h
