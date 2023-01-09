import os
from utils import exec_commands_with_failure

def build_temp_m4():
    os.chdir(os.environ["LFS"] + "/srcs" + "/m4-1.4.19")
    exec_commands_with_failure([("./configure --prefix=/usr "
                                  "--host={} "
                                  "--build=$(build-aux/config.guess)".format(os.environ["LFS_TGT"])),
                                 "make", "make DESTDIR={} install".format(os.environ["LFS"]) ])

def build_temp_ncurses(): 
    os.chdir(os.environ["LFS"] + "/srcs" + "/ncurses-6.3")
    os.system("sed -i s/mawk// configure")
    os.system("mkdir build")
    os.system("pushd build")
    os.system("../configure")
    os.system("make -C include")
    os.system("make -C progs tic")
    os.system("popd")
    exec_commands_with_failure([("./configure --prefix=/usr "
                                 "--host={} --build=$(./config.guess) "
                                 "--mandir=/usr/share/man "
                                 "--with-manpage-format=normal "
                                 "--with-shared --without-normal "
                                 "--with-cxx-shared --without-debug "
                                 "--without-ada --disable-stripping "
                                 "--enable-widec".format(os.environ["LFS_TGT"])),
            "make", "make DESTDIR={} TIC_PATH=$(pwd)/build/progs/tic install".format(os.environ["LFS"]) ])
    os.system('echo "INPUT(-lncursesw)" > {}/usr/lib/libncurses.so'.format(os.environ["LFS"]))

def build_temp_bash():
    os.chdir(os.environ["LFS"] + "/srcs/bash-5.1.16")
    exec_commands_with_failure([("./configure --prefix=/usr "
                                 "--build=$(support/config.guess) --host={} "
                                 "--without-bash-malloc").format(os.environ["LFS_TGT"]),
                                "make", "make DESTDIR={} install".format(os.environ["LFS"]) ])
    os.system("ln -sv bash {}/bin/sh".format(os.environ["LFS"]))
