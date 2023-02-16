#!/usr/bin/env python3

import os
import urllib.request
import sys
import subprocess

from utils import vanilla_build, red_print

def check_env_vars():
    try:
        for var in ["LFS", "LFS_TGT", "HOME"]:
            os.environ[var]
    except KeyError:
        print(f"{var} env var not set. bye!")
        sys.exit(1)

def create_dir_structure():
    if not os.path.exists(os.environ["LFS"]):
        os.mkdir(os.environ["LFS"])
    os.chdir(os.environ["LFS"])    
    for directory in [
            "etc", "lib64", "root", "run", "usr", "var",
            "usr/bin", "usr/sbin", "usr/lib",
            "cross-tools", "usr/local",
            "logs", "logs/tracked",
            "srcs",
            "root/build-scripts",
            "dev", "proc", "sys", "tmp"]: 
        if not os.path.exists(os.environ["LFS"] + directory):
            os.mkdir(os.environ["LFS"] + directory)
    for directory in ["bin", "lib", "sbin"]:
        if not os.path.exists(os.environ["LFS"] + directory):
            os.system("ln -s usr/{} {}{}".format(directory, 
                                        os.environ["LFS"], directory))
    os.system(f"cp {os.environ['HOME']}/sys_files/* {os.environ['LFS']}etc/")

def copy_build_scripts_into_lfs_dir():
    ret = os.system(f"cp -r $HOME/build-scripts/* {os.environ['LFS']}root/build-scripts")
    if ret != 0:
        red_print("copying build-scripts failed!")
     
def read_tarball_urls():
    os.chdir(os.environ["HOME"])
    with open("tarball_urls",'r') as f:
        urls = f.readlines()
    urls = [url.strip('\n') for url in urls]
    return [url for url in urls if url != '']

def download_tarballs():
    urls = read_tarball_urls()
    os.chdir(os.environ["LFS"] + "srcs")
    missing = []
    for url in urls:
        package_name = url.split("/")[-1]
        dest = os.environ["LFS"] + "srcs/" + package_name
        if package_name in os.listdir():
            continue
        print("downloading {}...".format(package_name))
        try:
            urllib.request.urlretrieve(url, dest)
        except:
            red_print("failed to download {}!".format(package_name))
            missing.append(package_name)
            continue
    if missing != []:
        red_print("missing " + ' '.join(missing) + '!')

class Target:
    def __init__(self, name, binary, alt_src_dir_name=None):
        self.name = name
        self.binary = os.environ["LFS"] + binary
        self.build_func = vanilla_build(name, alt_src_dir_name)
        
    def build(self): 
        if not os.path.exists(self.binary) or self.binary == os.environ["LFS"]:
            print(f"building {self.name.replace('_',' ')}...")
            self.build_func()

# Mount virtual kernel filesystems
def mount_vkfs():
    mount_info = subprocess.run("mount", stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    mount_info = str(mount_info)[2:].split('\\n')
    mount_info = [line for line in mount_info 
                  if os.environ["LFS"] in line]
    if mount_info != []:
        return
    for command in [ "mount -v --bind /dev {}dev",
                     "mount -v --bind /dev/pts {}dev/pts",
                     "mount -vt proc proc {}proc",
                     "mount -vt sysfs sysfs {}sys",
                     "mount -vt tmpfs tmpfs {}run" ]:
        if os.system(command.format(os.environ["LFS"])) != 0:
            red_print(command.format(os.environ["LFS"]) + " failed!")

def enter_chroot():
    mount_vkfs()
    os.chdir(os.environ["LFS"])
    os.chroot(os.environ["LFS"]) 
    for k in os.environ:
        if k != "TERM":
            del os.environ[k]
    os.environ["HOME"] = "/root"
    os.environ["PATH"] = "/usr/bin:/usr/sbin:/usr/local/bin"
    os.environ["LFS"] = '/'
    os.environ["LD_LIBRARY_PATH"] = "/usr/local/lib"
    os.system("install -d -m 1777 /tmp /var/tmp")


if __name__ == "__main__":
   
    check_env_vars()
    create_dir_structure() 
    copy_build_scripts_into_lfs_dir()
    download_tarballs()

    for target in [
        Target("cross_binutils",    "cross-tools/bin/ld"),
        Target("cross_gcc",         "cross-tools/bin/x86_64-lfs-linux-gnu-gcc"),
        Target("linux_api_headers", "usr/include/linux", "linux"),
        Target("cross_glibc",       "usr/lib/libc.so"),
        Target("cross_libstdcpp",   "usr/lib/libstdc++.so", "gcc") ]:
        target.build()
 
    for target in [
        Target("temp_m4",           "usr/bin/m4"),
        Target("temp_ncurses",      "usr/lib/libncurses.so"),
        Target("temp_bash",         "usr/bin/bash"),
        Target("temp_coreutils",    "usr/bin/env"),
        Target("temp_diffutils",    "usr/bin/diff"),
        Target("temp_file",         "usr/bin/file"),
        Target("temp_findutils",    "usr/bin/find"),
        Target("temp_gawk",         "usr/bin/gawk"),
        Target("temp_grep",         "usr/bin/grep"),
        Target("temp_gzip",         "usr/bin/gzip"),
        Target("temp_make",         "usr/bin/make"),
        Target("temp_patch",        "usr/bin/patch"),
        Target("temp_sed",          "usr/bin/sed"),
        Target("temp_tar",          "usr/bin/tar"),
        Target("temp_xz",           "usr/bin/xz"),
        Target("temp_binutils",     "usr/bin/ld"),
        Target("temp_gcc",          "usr/bin/gcc") ]:
        target.build()

    enter_chroot()
 
    for target in [
        Target("temp_gettext",    "usr/bin/xgettext"),
        Target("temp_bison",      "usr/bin/bison"),
        Target("temp_perl",       "usr/bin/perl"),
        Target("temp_Python",     "usr/bin/python3.10"),
        Target("temp_texinfo",    "usr/bin/info"),
        Target("temp_util-linux", "usr/bin/dmesg") ]:
        target.build()
    
    # For the moment, the targets with only a '#' by them mark
    # a package that built just fine but that there are no new files
    # for because all the newly built files replace temp tools built
    # by the cross compiler.
    for target in [
        Target("man-pages",         "usr/share/man/man1"),
        Target("iana-etc",          "etc/protocols"),
        Target("glibc",             "etc/ld.so.conf"), #experimental
        Target("zlib",              "usr/libz.so"),
        Target("bzip2",             "usr/bin/bzip2"),
        Target("xz",                "usr/lib/lzma.so"),
        Target("zstd",              "usr/bin/zstd"),
        Target("file",              "usr/lib/libmagic.la"),
        Target("readline",          "usr/lib/libreadline.so"),
        Target("m4",                "usr/bin/bc"), #
        Target("bc",                "usr/bin/bc"),
        Target("flex",              "usr/bin/flex"),
        Target("tcl",               "usr/bin/tclsh8.6"),
        Target("expect",            "usr/bin/expect"),
        Target("dejagnu",           "usr/bin/dejagnu"),
        Target("binutils",          ""),
        Target("gmp",               "usr/lib/libgmp.so"),
        Target("mpfr",              "usr/lib/libmpfr.so"),
        Target("mpc",               "usr/lib/libmpc.so"),
        Target("attr",              "usr/bin/attr"),
        Target("acl",               "usr/bin/libacl.so"),
        Target("libcap",            "usr/bin/libcap.so"),
        Target("shadow",            "usr/bin/passwd"),
        Target("gcc",               "usr/bin/x86_64-pc-linux-gnu-gcc"),
        Target("pkg-config",        "usr/bin/pkg-config"),
        Target("sed",               ""), #
        Target("psmisc",            "usr/bin/pstree"),
        Target("gettext",           ""),
        Target("bison",             ""), #
        Target("grep",              ""), #
        Target("bash",              ""), #
        Target("libtool",           ""),
        Target("gdbm",              "usr/lib/libgdbm.so"),
        Target("gperf",             "usr/bin/gperf"),
        Target("expat",             "usr/bin/libexpat.so"),
        Target("inetutils",         "usr/bin/ping"),
        Target("less",              "usr/bin/less"),
        Target("perl",              ""),
        Target("XML-Parser",        ""), #?
        Target("intltool",          "usr/bin/intltoolize"),
        Target("autoconf",          "usr/bin/autoconf"),
        Target("automake",          "usr/bin/automake"),
        Target("openssl",           "usr/bin/libssl.so"),
        Target("kmod",              "usr/lib/libkmod.so"),
        Target("elfutils",          "usr/lib/libelf.so"),
        Target("libffi",            "usr/lib/libffi.so"),
        Target("Python",            "usr/bin/pip3"),
        Target("ninja",             "usr/bin/ninja"),
        Target("coreutils",         ""),
        Target("check",             "usr/lib/libcheck.so"),
        Target("diffutils",         ""), #
        Target("gawk",              ""),
        Target("findutils",         ""),
        Target("groff",             "usr/bin/groff"),
        Target("grub",              "usr/bin/grub-mkimage"),
        Target("gzip",              ""), #
        Target("iproute",           "usr/sbin/ip"),
        Target("kbd",               "usr/bin/kbdinfo"),
        Target("libpipeline",       "usr/lib/libpipeline.so"),
        Target("make",              ""), #
        Target("patch",             ""), #
        Target("tar",               ""),
        Target("texinfo",           ""),
        Target("vim",               "vim"),
        Target("eudev",             ""),
        Target("man-db",            "usr/bin/man"),
        Target("procps-ng",         "usr/bin/ps"),
        Target("util-linux",        "usr/sbin/mkfs.cramfs"), #
        Target("e2fsprogs",         "usr/sbin/mkfs.ext4"),
        Target("sysklogd",          "usr/sbin/syslogd"),
        Target("sysvinit",          "usr/sbin/init")
        ]:
        target.build()
