#!/usr/bin/env python3

import os
import urllib.request
import sys

from utils import vanilla_build, red_print, build_w_snapshots

def check_env_vars():
    try:
        for var in ["LFS", "LFS_TGT", "HOME"]:
            os.environ[var]
    except KeyError:
        print(f"{var} env var not set. bye!")
        sys.exit(1)
    print("crucial environment variables are set...")

def create_dir_structure():
    lfs_dir_structure = [ "/etc", "/var", "/usr", "/tools",
                          "/lib64", "/srcs", "/build-logs", 
                          "/build-logs/tracked-files",
                          "/usr/bin", "/usr/lib", "/usr/sbin",
                          "/dev", "/proc", "/sys", "/run" ]
    if not os.path.exists(os.environ["LFS"]):
        os.mkdir(os.environ["LFS"])
    os.chdir(os.environ["LFS"])
    for directory in lfs_dir_structure:
        if not os.path.exists(os.environ["LFS"] + directory):
            os.mkdir(os.environ["LFS"] + directory)
    for directory in ["bin", "lib", "sbin"]:
        if not os.path.exists(os.environ["LFS"] + directory):
            os.system("ln -s usr/{} {}/{}".format(directory, 
                                                     os.environ["LFS"], directory))
    print("directory structure is created in " + os.environ["LFS"] + "...")

def read_tarball_urls():
    os.chdir(os.environ["HOME"])
    with open("tarball_urls",'r') as f:
        urls = f.readlines()
    urls = [url.strip('\n') for url in urls]
    return [url for url in urls if url != '']

def download_and_unpack_sources():
    urls = read_tarball_urls()
    os.chdir(os.environ["LFS"] + "/srcs")
    missing = []
    for url in urls:
        package_name = url.split("/")[-1]
        dest = os.environ["LFS"] + "/srcs/" + package_name
        package_name = package_name.split(".tar")[0]
        if package_name in os.listdir():
            continue
        #print("downloading {}...".format(package_name))
        try:
            urllib.request.urlretrieve(url, dest)
        except:
            red_print("failed to download {}!".format(package_name))
            missing.append(package_name)
            continue
        if ".tar" not in dest:
            continue
        if "tzdata2022c" in dest:
            os.mkdir(os.environ["LFS"] + "/srcs/tzdata2022c")
            os.chdir(os.environ["LFS"] + "/srcs/tzdata2022c")
        #print("unpacking " + package_name + "...")
        os.system("tar -xvf " + dest + " > /dev/null")
        os.system("rm " + dest)
        if "tzdata2022c" in dest:
            os.chdir(os.environ["LFS"] + "/srcs")
    if missing == []:
        print("sources are all downloaded and unpacked...")
    else:
        red_print("missing " + ' '.join(missing) + '!')

class Target:
    def __init__(self, name, binary, alt_src_dir_name=None):
        self.name = name
        self.binary = os.environ["LFS"] + binary
        self.build_func = vanilla_build(name, alt_src_dir_name)
        
    def build(self):
        name = self.name.replace('_',' ')
        if not os.path.exists(self.binary):
            print(f"building {name}...")
            self.build_func()
        else:
            print(f"{name} already built...")

def enter_chroot():
    if not os.path.exists(f"{os.environ['LFS']}/root/build-scripts"):
        ret = os.system(f"cp -r {os.environ['HOME']}/build-scripts {os.environ['LFS']}/root")
        if ret != 0:
            red_print("cp-ing build-scripts into $LFS/root failed for some reason!")
    os.chdir(os.environ["LFS"])
    os.chroot(os.environ["LFS"])
    os.environ = {"HOME" : "/root",
                  "TERM" : os.environ["TERM"],
                  "PATH" : "/usr/bin:/usr/sbin",
                  "LFS" : '/'}


if __name__ == "__main__":
   
    check_env_vars()
    create_dir_structure()
    download_and_unpack_sources()
 
    for target in [
        Target("cross_binutils",    f"/tools/bin/{os.environ['LFS_TGT']}-ld"),
        Target("cross_gcc",         f"/tools/bin/{os.environ['LFS_TGT']}-gcc"),
        Target("linux_api_headers", "/usr/include/linux", "linux"),
        Target("cross_glibc",       "/usr/lib/libc.so"),
        Target("cross_libstdcpp",   "/usr/lib/libstdc++.so", "gcc"),

        Target("temp_m4",           "/usr/bin/m4"),
        Target("temp_ncurses",      "/usr/lib/libncurses.so"),
        Target("temp_bash",         "/usr/bin/bash"),
        Target("temp_coreutils",    "/usr/bin/ls"),
        Target("temp_diffutils",    "/usr/bin/diff"),
        Target("temp_file",         "/usr/bin/file"),
        Target("temp_findutils",    "/usr/bin/find"),
        Target("temp_gawk",         "/usr/bin/gawk"),
        Target("temp_grep",         "/usr/bin/grep"),
        Target("temp_gzip",         "/usr/bin/gzip"),
        Target("temp_make",         "/usr/bin/make"),
        Target("temp_patch",        "/usr/bin/patch"),
        Target("temp_sed",          "/usr/bin/sed"),
        Target("temp_tar",          "/usr/bin/tar"),
        Target("temp_xz",           "/usr/bin/xz"),
        Target("temp_binutils",     "/usr/bin/ld"),
        Target("temp_gcc",          "/usr/bin/gcc")
    ]:
        target.build()
 
    enter_chroot()
       
    for target in ["chroot_gettext", "chroot_bison", "chroot_perl",
                   "chroot_Python", "chroot_texinfo", "chroot_util-linux"]:
        build_w_snapshots(vanilla_build(target))

    """for target in [
        Target("chroot_gettext",    ""),
        Target("chroot_bison",      ""),
        Target("chroot_perl",       ""),
        Target("chroot_Python",     ""),
        Target("chroot_texinfo",    ""),
        Target("chroot_util-linux", "")
    ]:
        target.build()"""

