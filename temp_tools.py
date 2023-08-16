import os, shutil, subprocess

from package import PreChrootPackage, Package
import utils


class TempM4(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host_build] + self.make_destdir)


class TempNcurses(PreChrootPackage):
    def _inner_build(self):
        utils.modify("configure", lambda line, _: line.replace("mawk", ""))
        self._create_and_enter_build_dir()
        self._run_commands(["../configure", "make -C include", "make -C progs tic"])
        os.chdir("..")
        self._run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f"--build={self.host_triplet} --mandir=/usr/share/man "
                "--with-manpage-format=normal --with-shared --without-normal "
                "--with-cxx-shared --without-debug --without-ada "
                "--disable-stripping --enable-widec",
                "make",
                f"make DESTDIR={self.root_dir} "
                f"TIC_PATH={self.root_dir}/ncurses-6.4/build/progs/tic install",
            ]
        )

        utils.write_file(
            f"{self.root_dir}/usr/lib/libncurses.so", ["INPUT(-lncursesw)"]
        )


class TempBash(PreChrootPackage):
    def _inner_build(self):
        self._run_commands(
            [self.config_prefix_host_build + " --without-bash-malloc"]
            + self.make_destdir
        )
        utils.ensure_symlink("bash", f"{self.root_dir}/usr/bin/sh")


class TempCoreutils(PreChrootPackage):
    def _inner_build(self):
        self._run_commands(
            [
                self.config_prefix_host_build + " --enable-install-program=hostname "
                "--enable-no-install-program=kill,uptime"
            ]
            + self.make_destdir
        )

        shutil.move(f"{self.root_dir}/usr/bin/chroot", f"{self.root_dir}/usr/sbin")
        utils.ensure_dir(f"{self.root_dir}/usr/share/man/man8")
        shutil.move(
            f"{self.root_dir}/usr/share/man/man1/chroot.1",
            f"{self.root_dir}/usr/share/man/man8/chroot.8",
        )
        utils.modify(
            f"{self.root_dir}/usr/share/man/man8/chroot.8",
            lambda line, _: line.replace('"1"', '"8"'),
        )


class TempDiffutils(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host] + self.make_destdir)


class TempFile(PreChrootPackage):
    def _inner_build(self):
        self._create_and_enter_build_dir()
        self._run(
            "../configure --disable-bzlib --disable-libseccomp --disable-xzlib "
            "--disable-zlib"
        )
        self._run("make")
        os.chdir("..")

        self._run_commands(
            [
                self.config_prefix_host_build,
                f"make FILE_COMPILE={self.root_dir}/file-5.44/build/src/file",
                f"make DESTDIR={self.root_dir} install",
            ]
        )

        utils.ensure_removal(f"{self.root_dir}/usr/lib/libmagic.la")


class TempFindutils(PreChrootPackage):
    def _inner_build(self):
        self._run_commands(
            [self.config_prefix_host_build + " --localstatedir=/var/lib/locate"]
            + self.make_destdir
        )


class TempGawk(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host_build] + self.make_destdir)


class TempGrep(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host] + self.make_destdir)


class TempGzip(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host] + self.make_destdir)


class TempMake(PreChrootPackage):
    def _inner_build(self):
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

        self._run_commands(
            [self.config_prefix_host_build + " --without-guile"] + self.make_destdir
        )


class TempPatch(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host_build] + self.make_destdir)


class TempSed(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host] + self.make_destdir)


class TempTar(PreChrootPackage):
    def _inner_build(self):
        self._run_commands([self.config_prefix_host_build] + self.make_destdir)


class TempXz(PreChrootPackage):
    def _inner_build(self):
        self._run_commands(
            [
                self.config_prefix_host_build
                + " --disable-static --docdir=/usr/share/doc/xz-5.4.1"
            ]
            + self.make_destdir
        )
        utils.ensure_removal(f"{self.root_dir}/usr/lib/liblzma.la")


class TempBinutils(PreChrootPackage):
    def _inner_build(self):
        utils.modify(
            "ltmain.sh",
            lambda line, i: line.replace("$add_dir", "") if i == 6008 else line,
        )

        self._create_and_enter_build_dir()
        self._run_commands(
            [
                f".{self.config_prefix_host_build} --disable-nls --enable-shared "
                "--enable-gprofng=no --disable-werror --enable-64-bit-bfd"
            ]
            + self.make_destdir
        )

        for name in ["bfd", "ctf", "ctf-nobfd", "opcodes"]:
            for extension in [".a", ".la"]:
                utils.ensure_removal(f"{self.root_dir}/usr/lib/lib{name}{extension}")


class TempGcc(PreChrootPackage):
    def _inner_build(self):
        self._common_gcc_before()
        for section in ["libgcc", "libstdc++-v3/include"]:
            utils.modify(
                f"{section}/Makefile.in",
                lambda line, _: line.replace("@thread_header@", "gthr-posix.h"),
            )

        self._create_and_enter_build_dir()
        self._run_commands(
            [
                f"../configure --build={self.host_triplet} "
                f"--host={self.lfs_triplet} --target={self.lfs_triplet} "
                f"LDFLAGS_FOR_TARGET=-L{self.root_dir}/gcc-12.2.0/build/{self.lfs_triplet}/libgcc "
                f"--prefix=/usr --with-build-sysroot={self.root_dir} "
                "--enable-default-pie --enable-default-ssp --disable-nls "
                "--disable-multilib --disable-libatomic --disable-libgomp "
                "--disable-libquadmath --disable-libssp --disable-libvtv "
                "--enable-languages=c,c++"
            ]
            + self.make_destdir
        )

        utils.ensure_symlink("gcc", f"{self.root_dir}/usr/bin/cc")


class TempGettext(Package):
    def _inner_build(self):
        self._run_commands(["./configure --disable-shared", "make"])
        for prog in ["msgfmt", "msgmerge", "xgettext"]:
            shutil.copy(f"gettext-tools/src/{prog}", "/usr/bin")


class TempBison(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --docdir=/usr/share/doc/bison-3.8.2",
                "make",
                "make install",
            ]
        )


class TempPerl(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "sh Configure -des -Dprefix=/usr -Dvendorprefix=/usr "
                "-Dprivlib=/usr/lib/perl5/5.36/core_perl "
                "-Darchlib=/usr/lib/perl5/5.36/core_perl "
                "-Dsitelib=/usr/lib/perl5/5.36/site_perl "
                "-Dsitearch=/usr/lib/perl5/5.36/site_perl "
                "-Dvendorlib=/usr/lib/perl5/5.36/vendor_perl "
                "-Dvendorarch=/usr/lib/perl5/5.36/vendor_perl ",
                "make",
                "make install",
            ]
        )


class TempPython(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "Python"

    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --enable-shared --without-ensurepip",
                "make",
                "make install",
            ]
        )


class TempTexinfo(Package):
    def _inner_build(self):
        self._run_commands(["./configure --prefix=/usr", "make", "make install"])


class TempUtilLinux(Package):
    def __init(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "util-linux"

    def _inner_build(self):
        self._run_commands(
            [
                "./configure ADJTIME_PATH=/var/lib/hwclock/adjtime "
                "--libdir=/usr/lib --docdir=/usr/share/doc/util-linux-2.38.1 "
                "--disable-chfn-chsh --disable-login --disable-nologin "
                "--disable-su --disable-setpriv --disable-runuser "
                "--disable-pylibmount --disable-static --without-python "
                "runstatedir=/run",
                "make",
                "make install",
            ]
        )


temp_tools_packages = [
    TempM4,
    TempNcurses,
    TempBash,
    TempCoreutils,
    TempDiffutils,
    TempFile,
    TempFindutils,
    TempGawk,
    TempGrep,
    TempGzip,
    TempMake,
    TempPatch,
    TempSed,
    TempTar,
    TempXz,
    TempBinutils,
    TempGcc,
]

chroot_temp_tools_packages = [TempGettext, TempBison, TempPerl, TempPython, TempTexinfo]
