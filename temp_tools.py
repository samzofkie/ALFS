import os, shutil, subprocess
from phase import PreChrootPhase


class TempToolsBuild(PreChrootPhase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)

        prefix_host = f"./configure --prefix=/usr --host={self.lfs_triplet}"
        prefix_host_build = prefix_host + f" --build={self.host_triplet}"
        make_destdir = ["make", f"make DESTDIR={self.root_dir} install"]

        def _add(self, target_name, build_commands):
            self.targets[target_name] = {"build_commands": build_commands}

        _add(self, "temp_m4", [prefix_host_build] + make_destdir)
        self.targets["temp_ncurses"] = {
            "build_commands": [
                (
                    f"./configure --prefix=/usr --host={self.lfs_triplet} "
                    f"--build={self.host_triplet} --mandir=/usr/share/man "
                    "--with-manpage-format=normal --with-shared --without-normal "
                    "--with-cxx-shared --without-debug --without-ada "
                    "--disable-stripping --enable-widec"
                ),
                "make",
                (
                    f"make DESTDIR={self.root_dir} "
                    f"TIC_PATH={self.root_dir}/ncurses-6.4/build/progs/tic install"
                ),
            ]
        }
        _add(
            self,
            "temp_bash",
            [prefix_host_build + " --without-bash-malloc"] + make_destdir,
        )
        _add(
            self,
            "temp_coreutils",
            [
                prefix_host_build
                + (
                    " --enable-install-program=hostname "
                    "--enable-no-install-program=kill,uptime"
                )
            ]
            + make_destdir,
        )
        _add(self, "temp_diffutils", [prefix_host] + make_destdir)
        _add(
            self,
            "temp_file",
            [
                prefix_host_build,
                f"make FILE_COMPILE={self.root_dir}/file-5.44/build/src/file",
                f"make DESTDIR={self.root_dir} install",
            ],
        )
        _add(
            self,
            "temp_findutils",
            [prefix_host_build + "--localstatedir=/var/lib/locate"] + make_destdir,
        )
        _add(self, "temp_gawk", [prefix_host_build] + make_destdir)
        _add(self, "temp_grep", [prefix_host] + make_destdir)
        _add(self, "temp_gzip", [prefix_host] + make_destdir)
        _add(self, "temp_make", [prefix_host_build + " --without-guile"] + make_destdir)
        _add(self, "temp_patch", [prefix_host_build] + make_destdir)
        _add(self, "temp_sed", [prefix_host] + make_destdir)
        _add(self, "temp_tar", [prefix_host_build] + make_destdir)
        _add(
            self,
            "temp_xz",
            [prefix_host_build + " --disable-static --docdir=/usr/share/doc/xz-5.4.1"]
            + make_destdir,
        )
        self.targets["temp_binutils"] = {
            "build_commands": [
                "."
                + prefix_host_build
                + (
                    " --disable-nls "
                    "--enable-shared --enable-gprofng=no --disable-werror "
                    "--enable-64-bit-bfd"
                )
            ]
            + make_destdir,
            "build_dir": True,
        }
        self.targets["temp_gcc"] = {
            "build_commands": [
                (
                    f"../configure --build={self.host_triplet} "
                    f"--host={self.lfs_triplet} --target={self.lfs_triplet} "
                    f"LDFLAGS_FOR_TARGET=-L{self.root_dir}/gcc-12.2.0/build/{self.lfs_triplet}/libgcc "
                    f"--prefix=/usr --with-build-sysroot={self.root_dir} "
                    "--enable-default-pie --enable-default-ssp --disable-nls "
                    "--disable-multilib --disable-libatomic --disable-libgomp "
                    "--disable-libquadmath --disable-libssp --disable-libvtv "
                    "--enable-languages=c,c++"
                )
            ]
            + make_destdir,
            "build_dir": True,
        }

    @staticmethod
    def _ensure_removal(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

    def _temp_ncurses_before(self):
        with open("configure", "r") as f:
            lines = f.readlines()
        lines = [line.replace("mawk", "") for line in lines]
        with open("configure", "w") as f:
            f.writelines(lines)
        self._create_and_enter_build_dir()
        for command in ["../configure", "make -C include", "make -C progs tic"]:
            self._run(command)
        os.chdir("..")

    def _temp_ncurses_after(self):
        with open(f"{self.root_dir}/usr/lib/libncurses.so", "w") as f:
            f.writelines("INPUT(-lncursesw)")

    def _temp_bash_after(self):
        os.symlink("bash", f"{self.root_dir}/usr/bin/sh")

    def _temp_coreutils_after(self):
        shutil.move(f"{self.root_dir}/usr/bin/chroot", f"{self.root_dir}/usr/sbin")
        os.makedirs(f"{self.root_dir}/usr/share/man/man8")
        shutil.move(
            f"{self.root_dir}/usr/share/man/man1/chroot.1",
            f"{self.root_dir}/usr/share/man/man8/chroot.8",
        )
        with open(f"{self.root_dir}/usr/share/man/man8/chroot.8", "r") as f:
            lines = f.readlines()
        for line in lines:
            line.replace('"1"', '"8"')
        with open(f"{self.root_dir}/usr/share/man/man8/chroot.8", "w") as f:
            f.writelines(lines)

    def _temp_file_before(self):
        self._create_and_enter_build_dir()
        self._run(
            "../configure --disable-bzlib --disable-libseccomp --disable-xzlib "
            "--disable-zlib"
        )
        self._run("make")
        os.chdir("..")

    def _temp_file_after(self):
        self._ensure_removal(f"{self.root_dir}/usr/lib/libmagic.la")

    def _temp_make_before(self):
        with open("src/main.c", "r") as f:
            file = f.read()
        bad_chunk_start = file.find("#ifdef SIGPIPE")
        bad_chunk_end = (
            bad_chunk_start + file[bad_chunk_start:].find("#endif\n") + len("#endif\n")
        )
        bad_chunk = file[bad_chunk_start:bad_chunk_end]
        file = file.replace(bad_chunk, "")
        with open("src/main.c", "w") as f:
            f.write(file)

    def _temp_xz_after(self):
        self._ensure_removal(f"{self.root_dir}/usr/lib/liblzma.la")

    def _temp_binutils_before(self):
        with open("ltmain.sh", "r") as f:
            lines = f.readlines()
        lines[6008] = lines[6008].replace("$add_dir", "")
        with open("ltmain.sh", "w") as f:
            f.writelines(lines)

    def _temp_binutils_after(self):
        for name in ["bfd", "ctf", "ctf-nobfd", "opcodes"]:
            for extension in [".a", ".la"]:
                self._ensure_removal(f"{self.root_dir}/usr/lib/lib{name}{extension}")

    def _temp_gcc_before(self):
        self._common_gcc_before()

        for section in ["libgcc", "libstdc++-v3/include"]:
            with open(f"{section}/Makefile.in", "r") as f:
                file = f.read()
            file.replace("@thread_header@", "gthr-posix.h")
            with open(f"{section}/Makefile.in", "w") as f:
                f.write(file)

    def _temp_gcc_after(self):
        os.symlink("gcc", f"{self.root_dir}/usr/bin/cc")
