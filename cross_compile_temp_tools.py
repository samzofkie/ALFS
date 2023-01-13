import os
from utils import find_source_dir, exec_commands_with_failure, exec_commands_with_failure_and_logging

def build_temp_m4():
    src_dir_path = find_source_dir("m4")
    log_file_path = os.environ["LFS"] + "/m4"
    os.chdir(src_dir_path)
    exec_commands_with_failure_and_logging([("./configure --prefix=/usr "
                                  "--host={} "
                                  "--build=$(build-aux/config.guess)".format(os.environ["LFS_TGT"])),
                                 "make", "make DESTDIR={} install".format(os.environ["LFS"])], log_file_path)

def build_temp_ncurses():
    src_dir_path = find_source_dir("ncurses")
    log_file_path = os.environ["LFS"] + "/ncurses"
    os.chdir(src_dir_path)
    os.system("sed -i s/mawk// configure")
    os.system("mkdir build")
    os.system("pushd build")
    os.system("../configure")
    os.system("make -C include")
    os.system("make -C progs tic")
    os.system("popd")
    exec_commands_with_failure_and_logging([("./configure --prefix=/usr "
                                 "--host={} --build=$(./config.guess) "
                                 "--mandir=/usr/share/man "
                                 "--with-manpage-format=normal "
                                 "--with-shared --without-normal "
                                 "--with-cxx-shared --without-debug "
                                 "--without-ada --disable-stripping "
                                 "--enable-widec".format(os.environ["LFS_TGT"])),
            "make", "make DESTDIR={} TIC_PATH=$(pwd)/build/progs/tic install".format(os.environ["LFS"])], log_file_path)
    os.system('echo "INPUT(-lncursesw)" > {}/usr/lib/libncurses.so'.format(os.environ["LFS"]))

def build_temp_bash():
    src_dir_path = find_source_dir("bash")
    log_file_path = os.environ["LFS"] + "/bash"
    os.chdir(src_dir_path)
    exec_commands_with_failure_and_logging([("./configure --prefix=/usr "
                                 "--build=$(support/config.guess) --host={} "
                                 "--without-bash-malloc").format(os.environ["LFS_TGT"]),
                                "make", "make DESTDIR={} install".format(os.environ["LFS"])], log_file_path)
    os.system("ln -sv bash {}/bin/sh".format(os.environ["LFS"]))
