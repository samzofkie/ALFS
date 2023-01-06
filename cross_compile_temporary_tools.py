import os

def build_temp_m4():
    exec_commmands_with_failure([("./configure --prefix=/usr "
                                  "--host={} "
                                  "--build=$(build-aux/config.guess)".config(os.environ["LFS_TGT"])),
                                 "make", "make DESTDIR={} install".format(os.environ["LFS"]) ])

def build_ncurses_():
    pass
