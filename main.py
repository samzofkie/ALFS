#!/usr/env python3

import os
import urllib.request
import sys

from build_cross_compiler import *
from cross_compile_temp_tools import *

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

def red_print(s):
    print("\33[31m" + s + "\33[0m")

wget_list_url = "https://mirror.download.it/lfs/pub/lfs/lfs-packages/11.2/wget-list"

def download_and_unpack_sources():
    os.chdir(os.environ["LFS"] + "/srcs")
    if "wget-list" not in os.listdir():
        os.system("wget {}".format(wget_list_url))
    with open("wget-list", "r") as f:
        urls = f.readlines()
    urls = [url.strip('\n') for url in urls]
    for url in urls:
        package_name = url.split("/")[-1]
        dest = os.environ["LFS"] + "/srcs/" + package_name
        package_name = package_name.split(".tar")[0]
        if package_name in os.listdir():
            #print("already have source for " + package_name)
            continue
        print("downloading {}...".format(package_name), end='\r')
        try:
            urllib.request.urlretrieve(url, dest)
        except:
            # '\x1b[1K' is a magic clear line character!
            red_print('\x1b[1K' + "  failed to download {}!".format(package_name))
            continue
        if ".tar" in dest:
            if "tzdata2022c" in dest:
                os.mkdir(os.environ["LFS"] + "/srcs/tzdata2022c")
                os.chdir(os.environ["LFS"] + "/srcs/tzdata2022c")
                print('\x1b[1K' + "unpacking " + package_name, end='\r')
                os.system("tar -xvf " + dest + " > /dev/null")
                os.system("rm " + dest)
                os.chdir(os.environ["LFS"] + "/srcs")
                continue
            print('\x1b[1K' + "unpacking " + package_name, end='\r')
            os.system("tar -xvf " + dest + " > /dev/null")
            os.system("rm " + dest) 

def build_if_file_missing(file, build_func, build_target_name):
    cross_linker_filename = os.environ["LFS"] + "/tools/bin/" + \
            os.environ["LFS_TGT"] + "-ld" 
    if not os.path.exists(file):
        build_func()
    else:
        print(build_target_name + " already built")

def exec_commands_with_failure(commands):
    for command in commands:
        ret = os.system(command)
        if ret != 0:
            print(command + " returned " + str(ret))
            sys.exit(1)

def lfs_dir_snapshot():
    os.chdir(os.environ["LFS"])
    snapshot = os.popen("find -path './srcs' -prune -o -print").read().split('\n')
    return set(snapshot)


try:
    for var in ["LFS", "LFS_TGT"]:
        os.environ[var]
except KeyError:
    print("{} env var not set. bye!".format(var))
    sys.exit(1)

create_dir_structure()
#download_and_unpack_sources()

cross_linker_filename = os.environ["LFS"] + "/tools/bin/" + \
        os.environ["LFS_TGT"] + "-ld"
build_if_file_missing(cross_linker_filename, build_cross_binutils,
                      "cross binutils")
cross_compiler_filename = os.environ["LFS"] + "/tools/bin/" + \
        os.environ["LFS_TGT"] + "-gcc"
build_if_file_missing(cross_compiler_filename, build_cross_gcc,
                      "cross gcc")
build_if_file_missing(os.environ["LFS"] + "/usr/include/linux", 
                      extract_linux_api_headers, "linux api headers")
build_if_file_missing(os.environ["LFS"] + "/usr/lib/libc.so",
                      build_glibc, "glibc")
build_if_file_missing(os.environ["LFS"] + "/usr/lib/libstdc++.so",
                      build_libstdcpp, "libstdc++")

