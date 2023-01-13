import os
from utils import exec_commands_with_failure, try_make_build_dir, find_source_dir, exec_commands_with_failure_and_logging

def build_cross_binutils():
    src_dir_path = find_source_dir("binutils")
    log_file_path = os.environ["LFS"] + "/binutils"
    os.chdir(src_dir_path)
    try_make_build_dir(src_dir_path + "/build") 
    build_commands = [ ("../configure --prefix={}/tools "
              "--with-sysroot={} "
              "--target={} "
              "--disable-nls "
              "--enable-gprofng=no "
              "--disable-werror").format(os.environ["LFS"], 
                                         os.environ["LFS"], 
                                         os.environ["LFS_TGT"]),
              "make", "make install" ]
    exec_commands_with_failure_and_logging(build_commands, log_file_path)
    triplet_tool_dir = os.environ["LFS"] + "/tools/" + \
            os.environ["LFS_TGT"] + "/bin/"
    tool_bin = os.environ["LFS"] + "/tools/bin/"
    for tool in os.listdir(triplet_tool_dir):
        os.system("ln {} {}".format(triplet_tool_dir + tool,
                                    tool_bin + tool))

def build_cross_gcc():
    src_dir_path = find_source_dir("gcc")
    os.chdir(src_dir_path)
    os.system("./contrib/download_prerequisites")
    os.system("sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64")
    try_make_build_dir(src_dir_path + "/../gcc-build") 
    build_commands = [(src_dir_path + "/configure --target={} "
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
    exec_commands_with_failure_and_logging(build_commands, os.environ["LFS"] + "/gcc")
    os.chdir(src_dir_path)
    os.system("cat gcc/limitx.h gcc/glimits.h gcc/limity.h > \
`dirname $($LFS_TGT-gcc -print-libgcc-file-name)`/install-tools/include/limits.h")
    os.chdir(os.environ["LFS"] + "/srcs/")
    os.system("rm -rf gcc-build")

def extract_linux_api_headers():
    src_dir_path = find_source_dir("linux")
    os.chdir(src_dir_path)
    exec_commands_with_failure_and_logging(["make mrproper", "make headers",
            "find usr/include -type f ! -name '*.h' -delete",
            "cp -rv usr/include {}/usr".format(os.environ["LFS"])], os.environ["LFS"] + "/linux_headers")

def build_glibc():
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
            "/tools/libexec/gcc/{}/12.2.0/install-tools/mkheaders".format(os.environ["LFS_TGT"]))

def build_libstdcpp():
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



