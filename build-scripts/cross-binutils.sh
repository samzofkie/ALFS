set -e
mkdir -v build
cd build
../configure --prefix=$LFS/cross-tools \
  --with-sysroot=$LFS \
  --target=$LFS_TGT \
  --disable-nls \
  --enable-gprofng=no \
  --disable-werror
make
make install
for tool in `ls $LFS/cross-tools/$LFS_TGT/bin`
do 
  ln $LFS/cross-tools/$LFS_TGT/bin/$tool $LFS/cross-tools/bin/$tool
done
cd ..
rm -rf build
