import os
from utils import (
    try_make_build_dir, 
    find_source_dir, 
    read_in_bash_script,
    exec_commands_with_failure_and_logging,
    vanilla_build,
    get_version_num)


build_cross_binutils = vanilla_build("cross_binutils", "build")    

def build_cross_gcc():
    src_dir_path = find_source_dir("gcc")
    os.chdir(src_dir_path)
    log_file = os.environ["LFS"] + "/build-logs/cross_gcc"
    exec_commands_with_failure_and_logging(["./contrib/download_prerequisites",
                "sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64"],
                                           log_file)
    build_dir = os.environ["LFS"] + "/srcs/gcc-build"
    try_make_build_dir(build_dir)
    os.chdir(build_dir)
    commands = read_in_bash_script(os.environ["HOME"] + "/build-scripts/cross-gcc.sh")
    # Biggest reason this can't be vanilla build- I'd rather not have it be dependent
    # on version number.
    commands[0] = src_dir_path + '/' +commands[0]
    exec_commands_with_failure_and_logging(commands, log_file)
    os.chdir(src_dir_path)
    os.system("cat gcc/limitx.h gcc/glimits.h gcc/limity.h > \
        `dirname $($LFS_TGT-gcc -print-libgcc-file-name)`/install-tools/include/limits.h")
    os.system("rm -rf {}/srcs/gcc-build".format(os.environ["LFS"])

def build_linux_api_headers():
    src_dir_path = find_source_dir("linux")
    os.chdir(src_dir_path)
    exec_commands_with_failure_and_logging(["make mrproper", "make headers",
            "find usr/include -type f ! -name '*.h' -delete",
            "cp -rv usr/include {}/usr".format(os.environ["LFS"])], 
                                           os.environ["LFS"] + "/build-logs/linux_api_headers")

"""def build_cross_glibc():
    src_dir_path = find_source_dir("glibc")
    os.chdir(src_dir_path)
    os.system("ln -sfv ../lib/ld-linux-x86-64.so.2 " + \
            os.environ["LFS"] + "/lib64")
    os.system("ln -sfv ../lib/ld-linux-x86-64.so.2 " + \
            os.environ["LFS"] + "/lib64/ld-lsb-x86-64.so.3")
    os.system("patch -Np1 -i ../glibc-2.36-fhs-1.patch")
    try_make_build_dir(src_dir_path + "/build")
    os.system('echo "rootsbindir=/usr/sbin" > configparms')
    build_commands = [("../configure --prefix=/usr "
               "--host={} --build=$(../scripts/config.guess) "
               "--enable-kernel-3.2 "
               "--with-headers={}/usr/include "
               "libc_cv_slibdir=/usr/lib").format(os.environ["LFS_TGT"],
                                                  os.environ["LFS"]),
               "make", "make DESTDIR={} install".format(os.environ["LFS"])]
    exec_commands_with_failure_and_logging(build_commands, os.environ["LFS"] + "/glibc")
    os.system("sed '/RTLDLIST=/s@/usr@@g' -i $LFS/usr/bin/ldd".format(os.environ["LFS"]))
    os.system(os.environ["LFS"] + \
            "/tools/libexec/gcc/{}/12.2.0/install-tools/mkheaders".format(os.environ["LFS_TGT"]))"""

def build_cross_glibc():
    src_dir = find_source_dir("glibc")
    glibc_version_n = get_version_num("glibc")
    os.chdir(src_dir)
    os.system("patch -Np1 -i ../glibc-{}-fhs-1.patch".format(glibc_version_n))
    vanilla_build("cross_glibc", "build")()
    gcc_version_n = get_version_num("gcc")
    os.system(os.environ["LFS"] + \
        "/tools/libexec/gcc/{}/{}/install-tools/mkheaders".format(os.environ["LFS_TGT"], gcc_version_n))
   

def build_cross_libstdcpp():
    src_dir_path = find_source_dir("gcc")
    try_make_build_dir(os.environ["LFS"] + "/srcs/gcc-build")
    build_commands = [ (src_dir_path + "/libstdc++-v3/configure "
                        "--host={} "
                        "--build=$(../gcc-12.2.0/config.guess) "
                        "--prefix=/usr "
                        "--disable-multilib --disable-nls "
                        "--disable-libstdcxx-pch "
                        "--with-gxx-include-dir=/tools/{}/"
                        "include/c++/12.2.0".format(os.environ["LFS_TGT"],
                                                    os.environ["LFS_TGT"])),
                        "make", "make DESTDIR={} install".format(os.environ["LFS"]) ]
    exec_commands_with_failure_and_logging(build_commands, os.environ["LFS"] + "/libstdcpp")
    for fname in ["stdc++", "stdc++fs", "supc++"]:
        os.system("rm -v {}/usr/lib/lib{}.la".format(os.environ["LFS"], fname))

