#!/usr/bin/env python3

import os
import urllib.request
import sys

from build_funcs import *
from utils import build_if_file_missing


lfs_dir_structure = [ "etc", "var", "usr", "tools",
                      "lib64", "srcs",
                      "usr/bin", "usr/lib", "usr/sbin",
                      "build-logs" ]

def create_dir_structure():
    try: 
        os.mkdir(os.environ["LFS"])
        os.chdir(os.environ["LFS"])
        for directory in lfs_dir_structure:
            os.mkdir(directory)
    except FileExistsError:
        pass
    print("directory structure is created in " + os.environ["LFS"])

def red_print(s):
    print("\33[31m" + s + "\33[0m")

def read_tarball_urls():
    os.chdir("/home/lfs")
    with open("tarball_urls",'r') as f:
        urls = f.readlines()
    urls = [url.strip('\n') for url in urls]
    return [url for url in urls if url != '']

def download_and_unpack_sources():
    urls = read_tarball_urls()
    os.chdir(os.environ["LFS"] + "/srcs")
    for url in urls:
        package_name = url.split("/")[-1]
        dest = os.environ["LFS"] + "/srcs/" + package_name
        package_name = package_name.split(".tar")[0]
        if package_name in os.listdir():
            continue
        print("downloading {}...".format(package_name))
        try:
            urllib.request.urlretrieve(url, dest)
        except:
            red_print("  failed to download {}!".format(package_name))
            continue
        if ".tar" not in dest:
            continue
        if "tzdata2022c" in dest:
            os.mkdir(os.environ["LFS"] + "/srcs/tzdata2022c")
            os.chdir(os.environ["LFS"] + "/srcs/tzdata2022c")
        print("unpacking " + package_name + "...")
        os.system("tar -xvf " + dest + " > /dev/null")
        os.system("rm " + dest)
        if "tzdata2022c" in dest:
            os.chdir(os.environ["LFS"] + "/srcs")

#-------- main ----------
try:
    for var in ["LFS", "LFS_TGT"]:
        os.environ[var]
except KeyError:
    print("{} env var not set. bye!".format(var))
    sys.exit(1)


create_dir_structure()
download_and_unpack_sources()

cross_linker_filename = os.environ["LFS"] + "/tools/bin/" + \
        os.environ["LFS_TGT"] + "-ld"
build_if_file_missing(cross_linker_filename, build_cross_binutils,)

cross_compiler_filename = os.environ["LFS"] + "/tools/bin/" + \
        os.environ["LFS_TGT"] + "-gcc"
build_if_file_missing(cross_compiler_filename, build_cross_gcc)

build_if_file_missing(os.environ["LFS"] + "/usr/include/linux", 
                      build_linux_api_headers)

build_if_file_missing(os.environ["LFS"] + "/usr/lib/libc.so",
                      build_glibc)

build_if_file_missing(os.environ["LFS"] + "/usr/lib/libstdc++.so",
                      build_libstdcpp)

build_if_file_missing(os.environ["LFS"] + "/usr/bin/m4", 
                      build_temp_m4)

build_if_file_missing(os.environ["LFS"] + "/usr/lib/libncurses.so",
                      build_temp_ncurses)

build_if_file_missing(os.environ["LFS"] + "/usr/bin/bash",
                      build_temp_bash)

def build_w_snapshots(build_func):
    snap1 = lfs_dir_snapshot()
    build_func()
    snap2 = lfs_dir_snapshot()
    snap_f_path = os.environ["LFS"] + "/" + build_func.__name__ + "_new_files"
    with open(snap_f_path, 'w') as f:
        f.write('\n'.join(snap2 - snap1))

