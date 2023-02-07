#!/usr/bin/env python3

import os
import urllib.request
import sys
import subprocess
import signal

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
            "cross-tools", "temp-tools",
            "logs", "logs/tracked",
            "srcs",
            "root/build-scripts",
            "dev", "proc", "sys", "tmp"]: 
        if not os.path.exists(os.environ["LFS"] + directory):
            os.mkdir(os.environ["LFS"] + directory)
    for directory in ["bin", "lib", "sbin"]:
        if not os.path.exists(os.environ["LFS"] + directory):
            os.system("ln -s usr/{} {}/{}".format(directory, 
                                        os.environ["LFS"], directory))

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
            print(f"building {self.name.replace('_',' '}...")
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
    os.chdir(os.environ["LFS"])
    os.chroot(os.environ["LFS"])
    os.environ = {"HOME" : "/root",
                  "TERM" : os.environ["TERM"],
                  "PATH" : "/usr/bin:/usr/sbin:/temp-tools",
                  "LFS" : '/'}
    

if __name__ == "__main__":
   
    check_env_vars()
    create_dir_structure() 
    copy_build_scripts_into_lfs_dir()
    download_tarballs()

    for target in [
        Target("cross_binutils",    ""),
        Target("cross_gcc",         ""),
        Target("linux_api_headers", "", "linux"),
        Target("cross_glibc",       ""),
        Target("cross_libstdcpp",   "", "gcc"),

        Target("temp_m4",           ""),
        Target("temp_ncurses",      ""),
        Target("temp_bash",         ""),
        Target("temp_coreutils",    ""),
        Target("temp_diffutils",    ""),
        Target("temp_file",         ""),
        Target("temp_findutils",    ""),
        Target("temp_gawk",         ""),
        Target("temp_grep",         ""),
        Target("temp_gzip",         ""),
        Target("temp_make",         ""),
        Target("temp_patch",        ""),
        Target("temp_sed",          ""),
        Target("temp_tar",          ""),
        Target("temp_xz",           ""),
        Target("temp_binutils",     ""),
        Target("temp_gcc",          "") ]:
        target.build()

    sys.exit(0)

    mount_vkfs()
    if not os.path.exists(os.environ["LFS"] + "etc/group"):
        os.system(f"cp {os.environ['HOME']}/sys_files/* {os.environ['LFS']}etc/")
    if not os.path.exists("/tmp"):
        os.system("install -d -m 1777 /tmp /var/tmp")
    enter_chroot()

    for target in [
        Target("chroot_gettext",    "/usr/bin/msgfmt"),
        Target("chroot_bison",      "/usr/bin/bison"),
        Target("chroot_perl",       "/usr/bin/perl"),
        Target("chroot_Python",     "/usr/bin/python3.10"),
        Target("chroot_texinfo",    "/usr/bin/info"),
        Target("chroot_util-linux", "/usr/bin/dmesg") ]:
        target.build()
  
    for target in [
        Target("man-pages",         "/usr/share/man/man7/man.7"),
        Target("iana-etc",          "/etc/services"),
        Target("glibc",             "/usr/lib/libz.so"), # haha
        Target("zlib",              "/usr/lib/libz.so"),
        Target("bzip2",             "/usr/bin/bzip2"),
        Target("xz",                "/usr/lib/liblzma.la"),
        Target("zstd",              "/usr/bin/zstd"),
        Target("file",              "/usr/lib/libmagic.la"),
        Target("readline",          "/usr/lib/libreadline.so"),
        Target("m4",                "/usr/bin/bc"), # ^
        Target("bc",                "/usr/bin/bc"),
        Target("flex",              "/usr/bin/flex"),
        Target("tcl",               "/usr/lib/libtcl8.6.so"),
        Target("expect",            "/usr/bin/expect"),
        Target("dejagnu",           "/usr/bin/dejagnu"),
        Target("binutils",          "/usr/bin/dejagnu"), # ^
        Target("gmp",               "/usr/lib/libgmp.so"),
        Target("mpfr",              "/usr/lib/libmpfr.so"),
        Target("mpc",               "/usr/lib/libmpc.so"),
        Target("attr",              "/usr/bin/attr"),
        Target("acl",               "/usr/lib/libacl.so"),
        Target("libcap",            "/usr/lib/libcap.so"),
        Target("shadow",            "/usr/bin/passwd"),
        Target("gcc",               "/usr/bin/x86_64-pc-linux-gnu-gcc"),
        Target("pkg-config",        "/usr/bin/pkg-config"),
        Target("sed",               "/usr/bin/pkg-config"),
        Target("psmisc",            "/usr/bin/killall"),
        Target("gettext",           "/usr/bin/killall"),
        Target("bison",             "/usr/bin/killall"),
        Target("grep",              "/usr/bin/killall"),
        Target("bash",              "/usr/bin/killall"),
        Target("libtool",           "/usr/bin/killall"),
        Target("gdbm",              "/usr/lib/gdbm.so"),
        Target("gperf",             "/usr/bin/gperf"),
        Target("expat",             "/usr/lib/expat.so"),
        Target("inetutils",         "/usr/bin/ping"),
        Target("less",              "/usr/bin/less"),
        Target("perl",              "/usr/bin/less"),
        Target("XML-Parser",        ""),
        Target("intltool",          ""),
        Target("autoconf",          ""),
        Target("automake",          ""),
        Target("openssl",           "")
        ]:
        target.build()
