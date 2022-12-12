#!/usr/bin/python3

import os
import urllib.request

lfs = "/home/lfs/lfs"

lfs_dir_structure = [ "etc", "var", "usr", "tools",
                      "lib64",
                      "usr/bin", "usr/lib", "usr/sbin" ]

def create_dir_structure():
    try: 
        os.mkdir(lfs)
        os.chdir(lfs)
        for directory in lfs_dir_structure:
            os.mkdir(directory)
    except FileExistsError:
        pass

tarball_urls = { "binutils" : "https://ftp.gnu.org/gnu/binutils/binutils-2.39.tar.xz",
                 "gcc" : "https://ftp.gnu.org/gnu/gcc/gcc-12.2.0/gcc-12.2.0.tar.xz",
                 "linux" : "https://www.kernel.org/pub/linux/kernel/v5.x/linux-5.19.2.tar.xz",
                 "glibc" : "https://ftp.gnu.org/gnu/glibc/glibc-2.36.tar.xz" }


os.environ["LFS"]="/home/lfs/lfs"
create_dir_structure()
os.chdir(lfs)

for name in tarball_urls:
    print("downloading " + tarball_urls[name])
    tarball_file_name = "/home/lfs/lfs/" + tarball_urls[name].split("/")[-1]
    urllib.request.urlretrieve(tarball_urls[name], tarball_file_name )
