set -e
./configure --prefix=/temp-tools \
  --host=$LFS_TGT \
  --build=$(build-aux/config.guess) \
  --enable-install-program=hostname \
  --enable-no-install-program=kill,uptime
make 
make DESTDIR=$LFS install

mv -v $LFS/temp-tools/bin/chroot $LFS/usr/sbin
mkdir -pv $LFS/usr/share/man/man8
mv -v $LFS/temp-tools/share/man/man1/chroot.1 $LFS/usr/share/man/man8/chroot.8
sed -i 's/"1"/"8"/' $LFS/usr/share/man/man8/chroot.8
