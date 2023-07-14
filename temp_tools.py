import os
import shutil
from setup import ROOT_DIR, LFS_TGT, HOST_TRIPLET, ENV_VARS
from build import build, create_and_enter_build_dir, run, \
        get_tarball_and_package_names
from cross_toolchain import cross_gcc_before

DESTDIR = {"make install": {
        "DESTDIR": ROOT_DIR
    }}


def _ensure_removal(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def _build_temp_m4():
    cc = f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-m4", build_dir = False, configure_command = cc, 
          build_cl_args = DESTDIR)


def _temp_ncurses_before():
    with open("configure", "r") as f:
        lines = f.readlines()
    lines = [line.replace("mawk", "") for line in lines]
    with open("configure", "w") as f:
        f.writelines(lines)
    create_and_enter_build_dir()
    for command in ["../configure", "make -C include", "make -C progs tic"]:
        run(command)
    os.chdir("..")


def _temp_ncurses_after():
    with open(f"{ROOT_DIR}/usr/lib/libncurses.so", "w") as f:
        f.writelines("INPUT(-lncursesw)")


def _build_temp_ncurses():
    cc = (f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET} "
          "--mandir=/usr/share/man --with-manpage-format=normal --with-shared " 
          "--without-normal --with-cxx-shared --without-debug --without-ada "
          "--disable-stripping --enable-widec")
    _, package_name = get_tarball_and_package_names("ncurses")
    cl_args = DESTDIR.copy()
    cl_args["make install"].update(
            {"TIC_PATH": f"{ROOT_DIR}/{package_name}/build/progs/tic"})
    build("temp-ncurses", before_build = _temp_ncurses_before, 
          build_dir = False, configure_command = cc,
          build_cl_args = cl_args, after_build = _temp_ncurses_after)


def _temp_bash_after():
    os.symlink("bash", f"{ROOT_DIR}/usr/bin/sh") 


def _build_temp_bash():
    cc = (f"./configure --prefix=/usr --build={HOST_TRIPLET} --host={LFS_TGT} "
          "--without-bash-malloc")
    build("temp-bash", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR, after_build = _temp_bash_after)


def _temp_coreutils_after():
    shutil.move(f"{ROOT_DIR}/usr/bin/chroot", f"{ROOT_DIR}/usr/sbin")
    os.makedirs(f"{ROOT_DIR}/usr/share/man/man8")
    shutil.move(f"{ROOT_DIR}/usr/share/man/man1/chroot.1", 
                f"{ROOT_DIR}/usr/share/man/man8/chroot.8")
    with open(f"{ROOT_DIR}/usr/share/man/man8/chroot.8", "r") as f:
        lines = f.readlines()
    for line in lines:
        line.replace("\"1\"","\"8\"")
    with open(f"{ROOT_DIR}/usr/share/man/man8/chroot.8", "w") as f:
        f.writelines(lines)


def _build_temp_coreutils():
    cc = (f"./configure --prefix=/usr --host={LFS_TGT} "
        f"--build={HOST_TRIPLET} --enable-install-program=hostname "
        "--enable-no-install-program=kill,uptime")
    build("temp-coreutils", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR, after_build = _temp_coreutils_after)


def _build_temp_diffutils():
    cc = f"./configure --prefix=/usr --host={LFS_TGT}"
    build("temp-diffutils", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _temp_file_before():
    create_and_enter_build_dir()
    run("../configure --disable-bzlib --disable-libseccomp --disable-xzlib"
        "--disable-zlib")
    run("make")
    os.chdir("..")


def _temp_file_after():
    _ensure_removal(f"{ROOT_DIR}/usr/lib/libmagic.la")


def _build_temp_file():
    cc = f"./configure --prefix=/usr --build={HOST_TRIPLET} --host={LFS_TGT}" 
    _, package_name = get_tarball_and_package_names("file")
    cl_args = DESTDIR.copy()
    cl_args["make"] = {"PATH":
                       f"{ROOT_DIR}/{package_name}/build/src:{ENV_VARS['PATH']}"}
    build("temp-file", before_build = _temp_file_before, build_dir = False,
          configure_command = cc, build_cl_args = cl_args, 
          after_build = _temp_file_after)


def _build_temp_findutils():
    cc = ("./configure --prefix=/usr --localstatedir=/var/lib/locate "
         f"--host={LFS_TGT} --build={HOST_TRIPLET}")
    build("temp-findutils", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _build_temp_gawk():
    cc = f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-gawk", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _build_temp_grep():
    cc = f"./configure --prefix=/usr --host={LFS_TGT}"
    build("temp-grep", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _build_temp_gzip():
    cc = f"./configure --prefix=/usr --host={LFS_TGT}"
    build("temp-gzip", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _temp_make_before():
    with open("src/main.c", "r") as f:
        file = f.read()
    bad_chunk_start = file.find("#ifdef SIGPIPE")
    bad_chunk_end = (bad_chunk_start + file[bad_chunk_start:].find("#endif\n") +
        len("#endif\n"))
    bad_chunk = file[bad_chunk_start:bad_chunk_end]
    file = file.replace(bad_chunk, "")
    with open("src/main.c", "w") as f:
        f.write(file)


def _build_temp_make():
    cc = (f"./configure --prefix=/usr --without-guile --host={LFS_TGT} "
        f"--build={HOST_TRIPLET}")
    build("temp-make", before_build = _temp_make_before, build_dir = False,
          configure_command = cc, build_cl_args = DESTDIR)


def _build_temp_patch():
    cc = f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-patch", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _build_temp_sed():
    cc = f"./configure --prefix=/usr --host={LFS_TGT}"
    build("temp-sed", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _build_temp_tar():
    cc = f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-tar", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR)


def _temp_xz_after():
    _ensure_removal(f"{ROOT_DIR}/usr/lib/liblzma.la")


def _build_temp_xz():
    cc = (f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET} "
          "--disable-static --docdir=/usr/share/doc/xz-5.4.1")
    build("temp-xz", build_dir = False, configure_command = cc,
          build_cl_args = DESTDIR, after_build = _temp_xz_after)


def _temp_binutils_before():
    with open("ltmain.sh", "r") as f:
        lines = f.readlines()
    lines[6008] = lines[6008].replace("$add_dir", "")
    with open("ltmain.sh", "w") as f:
        f.writelines(lines)


def _temp_binutils_after():
    for name in ["bfd", "ctf", "ctf-nobfd", "opcodes"]:
        for extension in [".a", ".la"]:
            _ensure_removal(f"{ROOT_DIR}/usr/lib/lib{name}{extension}")


def _build_temp_binutils():
    cc = (f"../configure --prefix=/usr --build={HOST_TRIPLET} --host={LFS_TGT} "
          "--disable-nls --enable-shared --enable-gprofng=no --disable-werror "
          "--enable-64-bit-bfd")
    build("temp-binutils", before_build = _temp_binutils_before,
          configure_command = cc, build_cl_args = DESTDIR, 
          after_build = _temp_binutils_after)


def _temp_gcc_before():
    cross_gcc_before()
    for section in ["libgcc", "libstdc++-v3/include"]:
        with open(f"{section}/Makefile.in", "r") as f:
            file = f.read()
        file.replace("@thread_header@", "gthr-posix.h")
        with open(f"{section}/Makefile.in", "w") as f:
            f.write(file)


def _temp_gcc_after():
    os.symlink("gcc", f"{ROOT_DIR}/usr/bin/cc") 


def _build_temp_gcc(): 
    cc = (f"../configure --build={HOST_TRIPLET} --host={LFS_TGT} "
          f"--target={LFS_TGT} --prefix=/usr --with-build-sysroot={ROOT_DIR} "
          "--enable-default-pie --enable-default-ssp --disable-nls "
          "--disable-multilib --disable-libatomic --disable-libgomp "
          "--disable-libquadmath --disable-libssp --disable-libvtv "
          "--enable-languages=c,c++")
    cl_args = DESTDIR.copy()
    cl_args.update({"LDFLAGS_FOR_TARGET": f"{os.getcwd()}/{LFS_TGT}/libgcc"})
    build("temp-gcc", before_build = _temp_gcc_before,
          configure_command = cc, build_cl_args = cl_args, 
          after_build = _temp_gcc_after) 


def build_temp_tools():
    _build_temp_m4()
    _build_temp_ncurses()
    _build_temp_bash()
    _build_temp_coreutils()
    _build_temp_diffutils()
    _build_temp_file()
    _build_temp_findutils()
    _build_temp_gawk()
    _build_temp_grep()
    _build_temp_gzip()
    _build_temp_make()
    _build_temp_patch()
    _build_temp_sed()
    _build_temp_tar()
    _build_temp_xz()
    _build_temp_binutils()
    _build_temp_gcc()

