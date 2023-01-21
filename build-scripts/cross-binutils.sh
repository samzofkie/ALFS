set -e
mkdir -v build
cd build
../configure --prefix=$LFS/tools \
  --with-sysroot=$LFS \
  --target=$LFS_TGT \
  --disable-nls \
  --enable-gprofng=no \
  --disable-werror
make
make install
for tool in `ls $LFS/tools/$LFS_TGT/bin`
do 
  ln $LFS/tools/$LFS_TGT/bin/$tool $LFS/tools/bin/$tool
done
rm -rf build
