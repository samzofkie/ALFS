#!/usr/bin/env python3

import os
import urllib.request
import sys


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
        for i in ["bin", "lib", "sbin"]:
            os.system("ln -s usr/{} {}/{}".format(i, os.environ["LFS"], i))
    except FileExistsError:
        pass
    print("directory structure is created in " + os.environ["LFS"])

def red_print(s):
    print("\33[31m" + s + "\33[0m")

def read_tarball_urls():
    os.chdir(os.environ["HOME"])
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

LFS = os.environ["LFS"]
LFS_TGT = os.environ["LFS_TGT"]

from utils import vanilla_build

class Target:
    def __init__(self, name, binary, build_func=None):
        self.name = name
        self.binary = LFS + binary
        self.build_func = build_func
        if self.build_func == None:
            self.build_func = vanilla_build(name.replace(' ', '_'))

    def build(self):
        if not os.path.exists(self.binary):
            self.build_func()
        else:
            print(self.name + " already built")

from build_funcs import *

targets = [
    Target("cross binutils",    "/tools/bin/" + LFS_TGT + "-ld"),
    Target("cross gcc",         "/tools/bin/" + LFS_TGT +"-gcc"),
    Target("linux api headers", "/usr/include/linux", 
                                vanilla_build("linux_api_headers", "linux")),
    Target("cross glibc",       "/usr/lib/libc.so", build_cross_glibc),
    Target("cross libstdcpp",   "/usr/lib/libstdc++.so",
                                vanilla_build("cross_libstdcpp", "gcc")),

    Target("temp m4",           "/usr/bin/m4"),
    Target("temp ncurses",      "/usr/lib/libncurses.so"),
    Target("temp bash",         "/usr/bin/bash"),
    Target("temp coreutils",    "/usr/bin/ls"),
    Target("temp diffutils",    "/usr/bin/diff"),
    Target("temp file",         "/usr/bin/file"),
    Target("temp findutils",    "/usr/bin/find"),
    Target("temp gawk",         "/usr/bin/gawk"),
    Target("temp grep",         "/usr/bin/grep"),
    Target("temp gzip",         "/usr/bin/gzip"),
    Target("temp make",         "/usr/bin/make"),
    Target("temp patch",        "/usr/bin/patch"),
    Target("temp sed",          "/usr/bin/sed"),
    Target("temp tar",          "/usr/bin/tar"),
    Target("temp xz",           "/usr/bin/xz")
]

for target in targets:
    target.build()

build_w_snapshots(vanilla_build("temp_binutils"))
build_w_snapshots(vanilla_build("temp_gcc"))


def lfs_dir_snapshot():
    os.chdir(os.environ["LFS"])
    snapshot = os.popen("find -path './srcs' -prune -o -print").read().split('\n')
    return set(snapshot)

def build_w_snapshots(build_func):
    snap1 = lfs_dir_snapshot()
    build_func()
    snap2 = lfs_dir_snapshot()
    snap_f_path = os.environ["LFS"] + "/" + build_func.__name__ + "_new_files"
    with open(snap_f_path, 'w') as f:
        f.write('\n'.join(snap2 - snap1))
