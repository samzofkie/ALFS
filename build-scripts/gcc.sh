set -e
sed -e '/m64=/s/lib64/lib/' \
  -i.orig gcc/config/i386/t-linux64
mkdir -v build
cd build
../configure --prefix=/usr \
  LD=ld \
  --enable-languages=c,c++ \
  --disable-multilib \
  --disable-bootstrap \
  --with-system-zlib
make
make install
ln -sfv ../../libexec/gcc/$(gcc -dumpmachine)/12.2.0/liblto_plugin.so \
  /usr/lib/bfd-plugins/

