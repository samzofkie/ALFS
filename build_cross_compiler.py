#!/usr/bin/python3

import os
import urllib.request


lfs_dir_structure = [ "etc", "var", "usr", "tools",
                      "lib64", "srcs",
                      "usr/bin", "usr/lib", "usr/sbin" ]

def create_dir_structure():
    try: 
        os.mkdir(os.environ["LFS"])
        os.chdir(os.environ["LFS"])
        for directory in lfs_dir_structure:
            os.mkdir(directory)
    except FileExistsError:
        pass
    print("directory structure is created in " + os.environ["LFS"])

tarball_urls = { "binutils" : "https://ftp.gnu.org/gnu/binutils/binutils-2.39.tar.xz",
                 "gcc" : "https://ftp.gnu.org/gnu/gcc/gcc-12.2.0/gcc-12.2.0.tar.xz",
                 "linux" : "https://www.kernel.org/pub/linux/kernel/v5.x/linux-5.19.2.tar.xz",
                 "glibc" : "https://ftp.gnu.org/gnu/glibc/glibc-2.36.tar.xz" }

def download_and_unpack_sources():
    os.chdir(os.environ["LFS"] + "/srcs")
    for name in tarball_urls:
        tarball_filename = os.environ["LFS"] + "/" + tarball_urls[name].split("/")[-1]
        package_name = tarball_filename.split(".tar.xz")[0].split("/")[-1]
        if (package_name in os.listdir()):
            print("already have source for " + package_name)
            continue
        print("downloading " + tarball_urls[name] + "...")
        urllib.request.urlretrieve(tarball_urls[name], tarball_filename)
        print("unpacking " + tarball_filename + "...")
        os.system("tar -xvf " + tarball_filename + " > /dev/null")
        print("removing " + tarball_filename)
        os.system("rm " + tarball_filename)

def build_cross_binutils():
    os.chdir(os.environ["LFS"] + "/srcs/" + "/binutils-2.39")
    try:
        os.mkdir("build")
    except FileExistsError:
        os.system("rm -rf build")
        os.mkdir("build")
    os.chdir("./build")
    os.system( ("../configure --prefix={}/tools "
              "--with-sysroot={} "
              "--target={} "
              "--disable-nlfs "
              "--enable-gprofng=no "
              "--disable-werror").format(os.environ["LFS"], os.environ["LFS"], os.environ["LFS_TGT"]))
    os.system("make")
    os.system("make install")

os.environ["LFS"] = "/home/lfs/lfs"
os.environ["LFS_TGT"] = os.popen("uname -m").read().split("\n")[0] + "-lfs-linux-gnu"

create_dir_structure()
download_and_unpack_sources()
build_cross_binutils()

