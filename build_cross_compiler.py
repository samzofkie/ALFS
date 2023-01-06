import os

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
    os.chdir(os.environ["LFS"] + "/srcs/gcc-12.2.0")
    os.system("cat gcc/limitx.h gcc/glimits.h gcc/limity.h > \
`dirname $($LFS_TGT-gcc -print-libgcc-file-name)`/install-tools/include/limits.h")


def extract_linux_api_headers():
    os.chdir(os.environ["LFS"] + "/srcs/linux-5.19.2")
    commands = ["make mrproper", "make headers",
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
    os.system(os.environ["LFS"] + \
            "/tools/libexec/gcc/{}/12.2.0/install-tools/mkheaders".format(os.environ["LFS_TGT"]))

def build_libstdcpp():
    os.chdir(os.environ["LFS"] + "/srcs")
    try:
        os.mkdir("gcc-build")
    except FileExistsError:
        os.system("rm -rf gcc-build")
        os.mkdir("gcc-build")
    os.chdir("gcc-build")
    build_commands = [ ("../gcc-12.2.0/libstdc++-v3/configure "
                        "--host={} "
                        "--build=$(../gcc-12.2.0/config.guess) "
                        "--prefix=/usr "
                        "--disable-multilib --disable-nls "
                        "--disable-libstdcxx-pch "
                        "--with-gxx-include-dir=/tools/{}/"
                        "include/c++/12.2.0".format(os.environ["LFS_TGT"],
                                                    os.environ["LFS_TGT"])),
                        "make", "make DESTDIR={} install".format(os.environ["LFS"]) ]
    exec_commands_with_failure(build_commands)
    for fname in ["stdc++", "stdc++fs", "supc++"]:
        os.system("rm -v {}/usr/lib/lib{}.la".format(os.environ["LFS"], fname))



