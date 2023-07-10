import os
import shutil
from setup import LFS_TGT, HOST_TRIPLET
from build import build, create_and_enter_build_dir, run, \
        get_tarball_and_package_names


def _build_temp_m4():
    cc = f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-m4", build_dir = False, configure_command = cc, 
          destdir = ROOT_DIR)


def _temp_ncurses_before():
    with open("configure", "r") as f:
        lines = f.readlines()
    lines = [line.replace("mawk", "") for line in lines]
    with open("configure", "w") as f:
        f.writelines(lines)
    create_and_enter_build_dir()
    for command in ["./configure", "make -C include", "make -C progs tic"]:
        run(command)
    os.chdir("..")


def _temp_ncurses_after():
    with open(f"{ROOT_DIR}/usr/lib/libncurses.so", "r") as f:
        lines = f.readlines()
    lines.append("INPUT(-lncursesw)")
    with open(f"{ROOT_DIR}/usr/lib/libncurses.so", "w") as f:
        f.writelines(lines)


def _build_temp_ncurses():
    cc = (f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET} "
          "--mandir=/usr/share/man --with-manpage-format=normal --with-shared " 
          "--without-normal --with-cxx-shared --without-debug --without-ada "
          "--disable-stripping --enable-widec")
    _, package_name = get_tarball_and_package_names("ncurses")
    cl_flags = f"{ROOT_DIR} TIC_PATH={ROOT_DIR}/{package_name}/build/progs/tic"
    build("temp-ncurses", before_build = _temp_ncurses_before, 
          build_dir = False, configure_command = cc,
          destdir = cl_flags, after_build = _temp_ncurses_after)


def _temp_bash_after():
    os.symlink("bash", f"{ROOT_DIR}/usr/bin/sh") 


def _build_temp_bash():
    cc = (f"./configure --prefix=/usr --build={HOST_TRIPLET} --host={LFS_TGT} "
          "--without-bash-malloc")
    build("temp-bash", build_dir = False, configure_command = cc,
          destdir = ROOT_DIR, after_build = _temp_bash_after)


def _temp_coreutils_after():
    shutil.move(f"{ROOT_DIR}/usr/bin/chroot", f"{ROOT_DIR}/usr/sbin")
    os.mkdir(f"{ROOT_DIR}/usr/share/man/man8", parents=True)
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
        "--build=${HOST_TRIPLET} --enable-install-program=hostname "
        "--enable-no-install-program=kill,uptime")
    build("temp-coreutils", build_dir = False, configure_command = cc,
          destdir = ROOT_DIR, after_build = _temp_coreutils_after)


def _build_temp_diffutils():
    cc = f"./configure --prefix=/usr --host={LFS_TGT}"
    build("temp-diffutils", build_dir = False, configure_command = cc,
          destdir = ROOT_DIR)


def _temp_file_before():
    create_and_enter_build_dir()
    run("./configure --disable-bzlib --disable-libseccomp --disable-xzlib"
        "--disable-zlib")
    run("make")
    os.chdir("..")


def _temp_file_after():
    run(f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}")
    _, package_name = get_tarball_and_package_names("file")
    run(f"make FILE_COMPILE={ROOT_DIR}/{package_name}/build/src/file")
    run(f"make DESTDIR={ROOT_DIR} install")
    is os.path.exists(f"{ROOT_DIR}/usr/lib/libmagic.la"):
        os.remove(f"{ROOT_DIR}/usr/lib/libmagic.la")


def _build_temp_file():
    build("temp-file", before_build = _temp_file_before, build_dir = False,
          configure_command = "", after_build = _temp_after_build)


def _build_temp_findutils():
    cc = "./configure --prefix=/usr --localstatedir=/var/lib/locate "
         f"--host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-findutils", build_dir = False, configure_command = cc,
          destdir = ROOT_DIR)


def _build_temp_gawk():
    cc = f"./configure --prefix=/usr --host={LFS_TGT} --build={HOST_TRIPLET}"
    build("temp-gawk", build_dir = False, configure_command = cc,
          destdir = ROOT_DIR)


def _build_temp_grep():
    cc = f"./configure --prefix=/usr --host={LFS_TGT}"
    build("temp-grep", build_dir = False, configure_command = cc,
          destdir = ROOT_DIR)


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


