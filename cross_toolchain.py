import shutil
import os
import subprocess
from setup import ROOT_DIR, LFS_TGT, ENV_VARS, HOST_TRIPLET
from build import build, get_tarball_and_package_names, run


def _build_cross_binutils():
    cc = (f"../configure --prefix={ROOT_DIR}/tools "
        f"--with-sysroot={ROOT_DIR} --target={LFS_TGT} "
        "--disable-nls --enable-gprofng=no --disable-werror")
    build("cross-binutils", configure_command = cc)


def _cross_gcc_before():
    for dep in ["mpfr", "gmp", "mpc"]:
        tarball_name, package_name = get_tarball_and_package_names(dep)
        run(f"tar -xvf {ROOT_DIR}/sources/{tarball_name}")
        run(f"mv {package_name} {dep}")

    shutil.copyfile("gcc/config/i386/t-linux64", 
                    "gcc/config/i386/t-linux64.orig")
    with open("gcc/config/i386/t-linux64", "r") as f:
        lines = f.readlines()
    for line in lines:
        if "m64=" in line:
            line = line.replace("lib64", "lib")
    with open("gcc/config/i386/t-linux64", "w") as f:
        f.writelines(lines)


def _cross_gcc_after():
    os.chdir("..")
    lines = []
    for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
        with open(file, "r") as f:
            lines += f.readlines()
    completed = subprocess.run(
        f"{LFS_TGT}-gcc -print-libgcc-file-name".split(" "),
        capture_output=True, env=ENV_VARS)
    dirname = completed.stdout.decode().rsplit("/",1)[0]
    with open (dirname + "/install-tools/include/limits.h", "w") as f:
        f.writelines(lines)


def _build_cross_gcc():
    cc = (f"../configure --target={LFS_TGT} --prefix={ROOT_DIR}/tools "
        f"--with-glibc-version=2.37 --with-sysroot={ROOT_DIR} --with-newlib "
        "--without-headers --enable-default-pie --enable-default-ssp "
        "--disable-nls --disable-shared --disable-multilib --disable-threads "
        "--disable-libatomic --disable-libgomp --disable-libquadmath "
        "--disable-libssp --disable-libvtv --disable-libstdcxx "
        "--enable-languages=c,c++")
    build("cross-gcc", before_build = _cross_gcc_before, configure_command = cc, 
          after_build = _cross_gcc_after)


def _copy_linux_headers():
    destination = ROOT_DIR
    files = ["usr/include"]
    while files:
        curr = files.pop()
        if os.path.isdir(curr):
            files += [curr + "/" + f for f in os.listdir(curr)]
            os.mkdir(destination + "/" + curr)
        elif curr[-2:] == ".h":
            shutil.copy(curr, destination + "/" + curr)


def _linux_headers_before():
    run("make mrproper")
    run("make headers")
    _copy_linux_headers()


def _build_linux_headers():
    build("linux-headers", search_term = "linux-6", 
          before_build = _linux_headers_before, build_dir = False)


def _cross_glibc_before():
    os.symlink("../usr/lib/ld-linux-x86-64.so.2", ROOT_DIR +
               "/lib64/ld-linux-x86-64.so.2")
    os.symlink("../usr/lib/ld-linux-x86-64.so.2", ROOT_DIR + 
               "/lib64/ld-lsb-x86-64.so.3")
    _, package_name = get_tarball_and_package_names("glibc")
    run(f"patch -Np1 -i {ROOT_DIR}/sources/{package_name}-fhs-1.patch")
    
    if not os.path.exists("build"):
        os.mkdir("build")
    with open("build/configparms", "w") as f:
        f.write("rootsbindir=/usr/sbin")


def _cross_glibc_after():
    with open("main.c", "w") as f:
        f.write("int main(){}")
    run(f"{LFS_TGT}-gcc -xc main.c")
    completed_process = subprocess.run("readelf -l a.out".split(" "),
                                       env=ENV_VARS, check=True,
                                       capture_output=True)
    assert ( "[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]" 
            in completed_process.stdout.decode() )
    run(f"{ROOT_DIR}/tools/libexec/gcc/{LFS_TGT}/12.2.0/install-tools/mkheaders") 


def _build_cross_glibc():
    cc = (f"../configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET} "
        f"--enable-kernel=3.2 --with-headers={ROOT_DIR}/usr/include "
        "libc_cv_slibdir=/usr/lib")
    cl_args = {"make install": {"DESTDIR": ROOT_DIR}}
    build("cross-glibc", before_build = _cross_glibc_before, 
          configure_command = cc, build_cl_args = cl_args, 
          after_build = _cross_glibc_after)


def _cross_libstdcpp_after():
    for prefix in ["stdc++", "stdc++fs", "supc++"]:
        archive = ROOT_DIR + "/usr/lib/lib" + prefix + ".la"
        if os.path.exists(archive):
            os.remove(archive)


def build_cross_libstdcpp():
    cc = (f"../libstdc++-v3/configure --host={LFS_TGT} --build={HOST_TRIPLET} "
        "--prefix=/usr --disable-multilib --disable-nls "
        "--disable-libstdcxx-pch "
        f"--with-gxx-include-dir=/tools/{LFS_TGT}/include/c++/12.2.0")
    cl_args = {"make install": {"DESTDIR": ROOT_DIR}}
    build("cross-libstdc++", search_term = "gcc", configure_command = cc,
          build_cl_args = cl_args, after_build = _cross_libstdcpp_after())


def build_cross_toolchain():
    _build_cross_binutils()
    _build_cross_gcc()
    _build_linux_headers()
    _build_cross_glibc()
    _build_cross_libstdcpp()
