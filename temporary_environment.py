import os, shutil, subprocess

from package import PreChrootPackage, Package
import utils


class CrossBinutils(PreChrootPackage):
    tarball_url = "https://sourceware.org/pub/binutils/releases/binutils-2.40.tar.xz"
    
    def _inner_build(self):
        self.create_and_enter_build_dir()
        utils.run_commands(
            [
                f"../configure --prefix={self.root_dir()}/tools "
                f"--with-sysroot={self.root_dir()} "
                f"--target={self.lfs_triplet} --disable-nls --enable-gprofng=no "
                "--disable-werror",
                "make",
                "make install",
            ]
        )


class CrossGcc(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/gcc/gcc-12.2.0/gcc-12.2.0.tar.xz"
    
    def _inner_build(self):
        self._common_gcc_before()
        self.create_and_enter_build_dir()
        utils.run_commands(
            [
                f"../configure --target={self.lfs_triplet} "
                f"--prefix={self.root_dir()}/tools "
                f"--with-glibc-version=2.37 --with-sysroot={self.root_dir()} "
                "--with-newlib --without-headers --enable-default-pie "
                "--enable-default-ssp "
                "--disable-nls --disable-shared --disable-multilib --disable-threads "
                "--disable-libatomic --disable-libgomp --disable-libquadmath "
                "--disable-libssp --disable-libvtv --disable-libstdcxx "
                "--enable-languages=c,c++",
                "make",
                "make install",
            ]
        )

        os.chdir("..")
        lines = []
        for file in ["gcc/limitx.h", "gcc/glimits.h", "gcc/limity.h"]:
            lines += utils.read_file(file)
        completed = subprocess.run(
            f"{self.lfs_triplet}-gcc -print-libgcc-file-name".split(" "),
            capture_output=True,
            check=True,
        )
        dirname = completed.stdout.decode().rsplit("/", 1)[0]
        utils.write_file(f"{dirname}/install-tools/include/limits.h", lines)


class LinuxHeaders(PreChrootPackage):
    tarball_url = "https://www.kernel.org/pub/linux/kernel/v6.x/linux-6.1.11.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(["make mrproper", "make headers"])
        for root, dirs, files in os.walk("usr/include"):
            for file in files:
                if file[-2:] != ".h":
                    utils.ensure_removal(f"{root}/{file}")
        utils.ensure_dir(f"{self.root_dir()}/usr/include")
        shutil.copytree(
            "usr/include", f"{self.root_dir()}/usr/include", dirs_exist_ok=True
        )


class CrossGlibc(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/glibc/glibc-2.37.tar.xz"
    patch_url = "https://www.linuxfromscratch.org/patches/lfs/11.3/glibc-2.37-fhs-1.patch"
    
    def _inner_build(self):
        utils.ensure_dir(f"{self.root_dir()}/lib64")
        utils.ensure_symlink(
            "../usr/lib/ld-linux-x86-64.so.2",
            f"{self.root_dir()}/lib64/ld-linux-x86-64.so.2",
        )
        utils.ensure_symlink(
            "../usr/lib/ld-linux-x86-64.so.2",
            f"{self.root_dir()}/lib64/ld-lsb-x86-64.so.3",
        )
        self.apply_patch()
        utils.ensure_dir("build")
        utils.write_file("build/configparms", ["rootsbindir=/usr/sbin"])

        self.create_and_enter_build_dir()
        utils.run_commands(
            [
                f"../configure --prefix=/usr --host={self.lfs_triplet} "
                f"--build={self.host_triplet} --enable-kernel=3.2 "
                f"--with-headers={self.root_dir()}/usr/include "
                "libc_cv_slibdir=/usr/lib",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )

        utils.write_file("main.c", "int main(){}")
        utils.run(f"{self.lfs_triplet}-gcc -xc main.c")
        completed_process = subprocess.run(
            "readelf -l a.out".split(" "), check=True, capture_output=True
        )
        assert (
            "[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]"
            in completed_process.stdout.decode()
        )
        utils.run(
            f"{self.root_dir()}/tools/libexec/gcc/{self.lfs_triplet}/12.2.0/"
            "install-tools/mkheaders"
        )


class CrossLibstdcpp(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/gcc/gcc-12.2.0/gcc-12.2.0.tar.xz"

    def _inner_build(self):
        self.create_and_enter_build_dir()
        utils.run_commands(
            [
                f"../libstdc++-v3/configure --host={self.lfs_triplet} "
                f"--build={self.host_triplet} --prefix=/usr --disable-multilib "
                "--disable-nls --disable-libstdcxx-pch "
                f"--with-gxx-include-dir=/tools/{self.lfs_triplet}/include/c++/12.2.0",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )
        for name in ["stdc++", "stdc++fs", "supc++"]:
            utils.ensure_removal(f"{self.root_dir()}/usr/lib/lib{name}.la")


cross_toolchain = [
    CrossBinutils,
    CrossGcc,
    LinuxHeaders,
    CrossGlibc,
    CrossLibstdcpp,
]


class TempM4(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/m4/m4-1.4.19.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f"--build={self.host_triplet} ",
                "make",
                f"make DESTDIR={self.root_dir()}",
            ]
        )


class TempNcurses(PreChrootPackage):
    tarball_url = "https://invisible-mirror.net/archives/ncurses/ncurses-6.4.tar.gz"
    
    def _inner_build(self):
        utils.modify("configure", lambda line, _: line.replace("mawk", ""))
        self.create_and_enter_build_dir()
        utils.run_commands(["../configure", "make -C include", "make -C progs tic"])
        os.chdir("..")
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f"--build={self.host_triplet} --mandir=/usr/share/man "
                "--with-manpage-format=normal --with-shared --without-normal "
                "--with-cxx-shared --without-debug --without-ada "
                "--disable-stripping --enable-widec",
                "make",
                f"make DESTDIR={self.root_dir()} "
                f"TIC_PATH={self.root_dir()}/ncurses-6.4/build/progs/tic install",
            ]
        )

        utils.write_file(
            f"{self.root_dir()}/usr/lib/libncurses.so", ["INPUT(-lncursesw)"]
        )


class TempBash(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/bash/bash-5.2.15.tar.gz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet} --without-bash-malloc ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )
        utils.ensure_symlink("bash", f"{self.root_dir()}/usr/bin/sh")


class TempCoreutils(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/coreutils/coreutils-9.1.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet} "
                "--enable-install-program=hostname "
                "--enable-no-install-program=kill,uptime ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )

        shutil.move(f"{self.root_dir()}/usr/bin/chroot", f"{self.root_dir()}/usr/sbin")
        utils.ensure_dir(f"{self.root_dir()}/usr/share/man/man8")
        shutil.move(
            f"{self.root_dir()}/usr/share/man/man1/chroot.1",
            f"{self.root_dir()}/usr/share/man/man8/chroot.8",
        )
        utils.modify(
            f"{self.root_dir()}/usr/share/man/man8/chroot.8",
            lambda line, _: line.replace('"1"', '"8"'),
        )


class TempDiffutils(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/diffutils/diffutils-3.9.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempFile(PreChrootPackage):
    tarball_url = "https://astron.com/pub/file/file-5.44.tar.gz"
    
    def _inner_build(self):
        self.create_and_enter_build_dir()
        utils.run(
            "../configure --disable-bzlib --disable-libseccomp --disable-xzlib "
            "--disable-zlib"
        )
        utils.run("make")
        os.chdir("..")

        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet}",
                f"make FILE_COMPILE={self.root_dir()}/file-5.44/build/src/file",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )

        utils.ensure_removal(f"{self.root_dir()}/usr/lib/libmagic.la")


class TempFindutils(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/findutils/findutils-4.9.0.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet} --localstatedir=/var/lib/locate ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )


class TempGawk(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/gawk/gawk-5.2.1.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet} ",
                "make",
                f"make DESTDIR{self.root_dir()} install",
            ] 
        )


class TempGrep(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/grep/grep-3.8.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempGzip(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/gzip/gzip-1.12.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempMake(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/make/make-4.4.tar.gz"
    
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

        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f"--build={self.host_triplet} --without-guile ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempPatch(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/patch/patch-2.7.6.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet}",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempSed(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/sed/sed-4.9.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempTar(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/tar/tar-1.34.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet}",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ] 
        )


class TempXz(PreChrootPackage):
    tarball_url = "https://tukaani.org/xz/xz-5.4.1.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet} --disable-static "
                "--docdir=/usr/share/doc/xz-5.4.1",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )
        utils.ensure_removal(f"{self.root_dir()}/usr/lib/liblzma.la")


class TempBinutils(PreChrootPackage):
    tarball_url = "https://sourceware.org/pub/binutils/releases/binutils-2.40.tar.xz"
    
    def _inner_build(self):
        utils.modify(
            "ltmain.sh",
            lambda line, i: line.replace("$add_dir", "") if i == 6008 else line,
        )

        self.create_and_enter_build_dir()
        utils.run_commands(
            [
                f"./configure --prefix=/usr --host={self.lfs_triplet} "
                f" --build={self.host_triplet} --disable-nls --enable-shared "
                "--enable-gprofng=no --disable-werror --enable-64-bit-bfd ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )

        for name in ["bfd", "ctf", "ctf-nobfd", "opcodes"]:
            for extension in [".a", ".la"]:
                utils.ensure_removal(f"{self.root_dir()}/usr/lib/lib{name}{extension}")


class TempGcc(PreChrootPackage):
    tarball_url = "https://ftp.gnu.org/gnu/gcc/gcc-12.2.0/gcc-12.2.0.tar.xz"
    
    def _inner_build(self):
        self._common_gcc_before()
        for section in ["libgcc", "libstdc++-v3/include"]:
            utils.modify(
                f"{section}/Makefile.in",
                lambda line, _: line.replace("@thread_header@", "gthr-posix.h"),
            )

        self.create_and_enter_build_dir()
        utils.run_commands(
            [
                f"../configure --build={self.host_triplet} "
                f"--host={self.lfs_triplet} --target={self.lfs_triplet} "
                f"LDFLAGS_FOR_TARGET=-L{self.root_dir()}/gcc-12.2.0/build/{self.lfs_triplet}/libgcc "
                f"--prefix=/usr --with-build-sysroot={self.root_dir()} "
                "--enable-default-pie --enable-default-ssp --disable-nls "
                "--disable-multilib --disable-libatomic --disable-libgomp "
                "--disable-libquadmath --disable-libssp --disable-libvtv "
                "--enable-languages=c,c++ ",
                "make",
                f"make DESTDIR={self.root_dir()} install",
            ]
        )

        utils.ensure_symlink("gcc", f"{self.root_dir()}/usr/bin/cc")


temporary_tools = [
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


class TempGettext(Package):
    tarball_url = "https://ftp.gnu.org/gnu/gettext/gettext-0.21.1.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(["./configure --disable-shared", "make"])
        for prog in ["msgfmt", "msgmerge", "xgettext"]:
            shutil.copy(f"gettext-tools/src/{prog}", "/usr/bin")


class TempBison(Package):
    tarball_url = "https://ftp.gnu.org/gnu/bison/bison-3.8.2.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                "./configure --prefix=/usr --docdir=/usr/share/doc/bison-3.8.2",
                "make",
                "make install",
            ]
        )


class TempPerl(Package):
    tarball_url = "https://www.cpan.org/src/5.0/perl-5.36.0.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
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
    tarball_url = "https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
            [
                "./configure --prefix=/usr --enable-shared --without-ensurepip",
                "make",
                "make install",
            ]
        )


class TempTexinfo(Package):
    tarball_url = "https://ftp.gnu.org/gnu/texinfo/texinfo-7.0.2.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(["./configure --prefix=/usr", "make", "make install"])


class TempUtilLinux(Package):
    tarball_url = "https://www.kernel.org/pub/linux/utils/util-linux/v2.38/util-linux-2.38.1.tar.xz"
    
    def _inner_build(self):
        utils.run_commands(
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


chroot_temporary_tools = [
    TempGettext, 
    TempBison, 
    TempPerl, 
    TempPython, 
    TempTexinfo,
    TempUtilLinux
]
