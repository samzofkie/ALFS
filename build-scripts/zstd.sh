set -e
patch -Np1 -i ../zstd-1.5.2-upstream_fixes-1.patch
make prefix=/usr
make check
make prefix=/usr install
rm -v /usr/lib/libzstd.a
