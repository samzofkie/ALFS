#!/bin/sh
set -e
patch -Np1 -i ../glibc-2.36-fhs-1.patch
mkdir -v build
cd build
echo "rootsbindir=/usr/sbin" > configparms
../configure --prefix=/usr \
  --disable-werror \
  --enable-kernel=3.2 \
  --enable-stack-protector=strong \
  --with-headers=/usr/include \
  libc_cv_slibdir=/usr/lib
make
set +e
make check
set -e
touch /etc/ld.so.conf
sed '/test-installation/s@$(PERL)@echo not running@' -i ../Makefile
make install
sed '/RTLDLIST=/s@/usr@@g' -i /usr/bin/ldd
