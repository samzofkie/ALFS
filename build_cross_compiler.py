#!/usr/bin/python3

import os
import urllib.request


lfs_dir_structure = [ "etc", "var", "usr", "tools",
                      "lib64",
                      "usr/bin", "usr/lib", "usr/sbin" ]

def create_dir_structure():
    try: 
        os.mkdir(os.environ["LFS"])
        os.chdir(os.environ["LFS"])
        for directory in lfs_dir_structure:
            os.mkdir(directory)
    except FileExistsError:
        pass
    print("created directory structure in " + os.environ["LFS"])

tarball_urls = { "binutils" : "https://ftp.gnu.org/gnu/binutils/binutils-2.39.tar.xz",
                 "gcc" : "https://ftp.gnu.org/gnu/gcc/gcc-12.2.0/gcc-12.2.0.tar.xz",
                 "linux" : "https://www.kernel.org/pub/linux/kernel/v5.x/linux-5.19.2.tar.xz",
                 "glibc" : "https://ftp.gnu.org/gnu/glibc/glibc-2.36.tar.xz" }

def download_and_unpack_sources():
    for name in tarball_urls:
        print("downloading " + tarball_urls[name] + "...")
        tarball_filename = os.environ["LFS"] + "/" + tarball_urls[name].split("/")[-1]
        urllib.request.urlretrieve(tarball_urls[name], tarball_filename)
        print("unpacking " + tarball_filename + "...")
        os.system("tar -xvf " + tarball_filename + " > /dev/null")
        print("removing " + tarball_filename)
        os.system("rm " + tarball_filename)

os.environ["LFS"] = "/home/lfs/lfs"
create_dir_structure()
download_and_unpack_sources()

