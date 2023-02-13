set +h
umask 022
alias ls="ls --color"
LFS=/root/lfs/
LC_ALL=POSIX
LFS_TGT=$(uname -m)-lfs-linux-gnu
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PATH=$(echo $LFS)cross-tools/bin:$PATH
CONFIG_SITE=$LFS/usr/share/config.site
PS1='\u:\w\$ '
export LFS LC_ALL LFS_TGT PATH CONFIG_SITE PS1
