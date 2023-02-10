set -e
echo '#define SYS_VIMRC_FILE "/etc/vimrc"' >> src/feature.h
./configure --prefix=/usr
make
make install
ln -sv ../vim/vim90/doc /usr/share/doc/vim-9.0.0228
