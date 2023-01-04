#!/usr/bin/python3

import os
import urllib.request
import sys

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
                 "glibc" : "https://ftp.gnu.org/gnu/glibc/glibc-2.36.tar.xz"}


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
    
    glibc_patch_url = "https://www.linuxfromscratch.org/patches/downloads/glibc/glibc-2.36-fhs-1.patch"
    glibc_patch_filename =  os.environ["LFS"] + "/srcs/" + glibc_patch_url.split("/")[-1]
    if ("glibc-2.36-fhs-1.patch" in os.listdir()):
        print("already have glibc patch")
        return
    print("downloading " + "glibc-2.36-fhs-1.patch...")
    urllib.request.urlretrieve(glibc_patch_url, glibc_patch_filename)


def exec_commands_with_failure(commands):
    for command in commands:
        ret = os.system(command)
        if ret != 0:
            print(command + " returned " + str(ret))
            sys.exit(1)


def build_cross_binutils():
    os.chdir(os.environ["LFS"] + "/srcs" + "/binutils-2.39")
    try:
        os.mkdir("build")
    except FileExistsError:
        os.system("rm -rf build")
        os.mkdir("build")
    os.chdir("./build")

    build_commands = [ ("../configure --prefix={}/tools "
              "--with-sysroot={} "
              "--target={} "
              "--disable-nlfs "
              "--enable-gprofng=no "
              "--disable-werror").format(os.environ["LFS"], os.environ["LFS"], os.environ["LFS_TGT"]),
              "make", "make install" ]
    exec_commands_with_failure(build_commands)


def build_cross_gcc():
    os.chdir(os.environ["LFS"] + "/srcs/gcc-12.2.0")
    os.system("./contrib/download_prerequisites")
    os.system("sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64")
    
    os.chdir(os.environ["LFS"] + "/srcs")
    try:
        os.mkdir("gcc-build")
    except FileExistsError:
        os.system("rm -rf gcc-build")
        os.mkdir("gcc-build")
    os.chdir("gcc-build")

    build_commands = [("../gcc-12.2.0/configure --target={} "
                "--prefix={}/tools "
                "--with-glibc-version=2.36 "
                "--with-sysroot={} "
                "--with-newlib "
                "--without-headers "
                "--disable-nls "
                "--disable-shared "
                "--disable-multilib "
                "--disable-decimal-float "
                "--disable-threads "
                "--disable-libatomic "
                "--disable-libgomp "
                "--disable-libquadmath "
                "--disable-libssp "
                "--disable-libvtv "
                "--disable-libstdcxx "
                "--enable-languages=c,c++").format(os.environ["LFS_TGT"], 
                                                   os.environ["LFS"], 
                                                   os.environ["LFS"]),
                      "make", "make install"]
    exec_commands_with_failure(build_commands)


def extract_linux_api_headers():
    os.chdir(os.environ["LFS"] + "/srcs/linux-5.19.2")
    commands = ["make mrproper", "make headers"
            "find usr/include -type f ! -name '*.h' -delete",
            "cp -rv usr/include {}/usr".format(os.environ["LFS"])]
    exec_commands_with_failure(commands)


def build_glibc():
    os.chdir(os.environ["LFS"] + "/srcs/glibc-2.36")
    
    os.system("ln -sfv ../lib/ld-linux-x86-64.so.2 " + \
            os.environ["LFS"] + "/lib64")
    os.system("ln -sfv ../lib/ld-linux-x86-64.so.2 " + \
            os.environ["LFS"] + "/lib64/ld-lsb-x86-64.so.3")

    os.system("patch -Np1 -i ../glibc-2.36-fhs-1.patch")

    try:
        os.mkdir("build")
    except FileExistsError:
        os.system("rm -rf build")
        os.mkdir("build")
    os.chdir("build")
    os.system('echo "rootsbindir=/usr/sbin" > configparms')
    
    build_commands = [("../configure --prefix=/usr "
               "--host={} --build=$(../scripts/config.guess) "
               "--enable-kernel-3.2 "
               "--with-headers={}/usr/include "
               "libc_cv_slibdir=/usr/lib").format(os.environ["LFS_TGT"],
                                                  os.environ["LFS"]),
               "make", "make DESTDIR={} install".format(os.environ["LFS"])]
    exec_commands_with_failure(build_commands)
 
    os.system("sed '/RTLDLIST=/s@/usr@@g' -i $LFS/usr/bin/ldd".format(os.environ["LFS"]))




os.environ["LFS"] = "/home/lfs/lfs"
os.environ["LFS_TGT"] = os.popen("uname -m").read().split("\n")[0] + "-lfs-linux-gnu"

create_dir_structure()
download_and_unpack_sources()

cross_linker_filename = os.environ["LFS"] + "/tools/bin/" + \
        os.environ["LFS_TGT"] + "-ld" 
if not os.path.exists(cross_linker_filename):
    build_cross_binutils()
else:
    print("cross binutils already built")

cross_compiler_filename = os.environ["LFS"] + "/tools/bin/" + \
        os.environ["LFS_TGT"] + "-gcc"
if not os.path.exists(cross_compiler_filename):
    build_cross_gcc()
else:
    print("cross gcc already built")

linux_headers_dirname = os.environ["LFS"] + "/usr/include/linux"
if not os.path.exists(linux_headers_dirname):
    extract_linux_api_headers()
else:
    print("linux api headers already extracted")



