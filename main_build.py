import os, shutil, subprocess, sys

from package import Package, gcc_change_default_64_bit_dir
import utils


class ManPages(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "man-pages"

    def _inner_build(self):
        self._run("make prefix=/usr install")


class IanaEtc(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "iana-etc"

    def _inner_build(self):
        shutil.copy("services", "/etc")
        shutil.copy("protocols", "/etc")


class Glibc(Package):
    def _inner_build(self):
        self._run("patch -Np1 -i /sources/glibc-2.37-fhs-1.patch")
        utils.modify(
            "stdio-common/vfprintf-process-arg.c",
            lambda line, i: line.replace("workend - string", "number_length")
            if i == 256
            else line,
        )

        self._create_and_enter_build_dir()

        utils.write_file("configparms", ["rootsbindir=/usr/sbin"])

        self._run_commands(
            [
                "../configure --prefix=/usr --disable-werror "
                "--enable-kernel=3.2 --enable-stack-protector=strong "
                "--with-headers=/usr/include libc_cv_slibdir=/usr/lib ",
                "make",
            ]
        )

        utils.ensure_touch("/etc/ld.so.conf")
        utils.modify(
            "../Makefile",
            lambda line, i: line.replace("$(PERL)", "echo not running")
            if i == 118
            else line,
        )
        self._run("make install")
        utils.modify(
            "/usr/bin/ldd",
            lambda line, i: line.replace("/usr", "/") if i == 28 else line,
        )
        shutil.copy("../nscd/nscd.conf", "/etc")
        os.makedirs("/var/cache/nscd")
        os.makedirs("/usr/lib/locale")

        self._run("make localedata/install-locales")
        subprocess.run("localedef -i POSIX -f UTF-8 C.UTF-8".split(), env=self.env)
        subprocess.run(
            "localedef -i ja_JP -f SHIFT_JIS ja_JP.SJIS".split(), env=self.env
        )
        self._run("tar -xvf /sources/tzdata2022g.tar.gz")
        zoneinfo = "/usr/share/zoneinfo"
        for d in ["posix", "right"]:
            os.makedirs(f"{zoneinfo}/{d}")
        for tz in [
            "etcetera",
            "southamerica",
            "northamerica",
            "europe",
            "africa",
            "antarctica",
            "asia",
            "australasia",
            "backward",
        ]:
            self._run(f"zic -L /dev/null -d {zoneinfo} {tz}")
            self._run(f"zic -L /dev/null -d {zoneinfo}/posix {tz}")
            self._run(f"zic -L leapseconds -d {zoneinfo}/right {tz}")
        for file in ["zone.tab", "zone1970.tab", "iso3166.tab"]:
            shutil.copy(file, zoneinfo)
        self._run(f"zic -d {zoneinfo} -p America/New_York")
        utils.ensure_symlink("/usr/share/zoneinfo/Chicago", "/etc/localtime")
        utils.write_file("/etc/ld.so.conf", ["/usr/local/lib\n", "/opt/lib\n"])


class Zlib(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
            ]
        )
        utils.ensure_removal("/usr/lib/libz.a")


class Bzip2(Package):
    def _inner_build(self):
        self._run("patch -Np1 -i /sources/bzip2-1.0.8-install_docs-1.patch")
        utils.modify(
            "Makefile",
            lambda line, _: line.replace("$(PREFIX)/bin/", "", 1)
            if "ls -s -f $(PREFIX)" in line
            else line,
        )
        utils.modify(
            "Makefile",
            lambda line, _: line.replace("$(PREFIX)/man", "$(PREFIX)/share/man")
            if "$(PREFIX)/man" in line
            else line,
        )

        self._run_commands(
            [
                "make -f Makefile-libbz2_so",
                "make clean",
                "make",
                "make PREFIX=/usr install",
            ]
        )

        shutil.copy("libbz2.so.1.0.8", "/usr/lib")
        utils.ensure_symlink("libbz2.so.1.0.8", "/usr/lib/libbz2.so.1.0")
        utils.ensure_symlink("libbz2.so.1.0.8", "/usr/lib/libbz2.so")
        shutil.copy("bzip2-shared", "/usr/bin/bzip2")
        for binary in ["bzcat", "bunzip2"]:
            utils.ensure_removal(f"/usr/bin/{binary}")
            utils.ensure_symlink("bzip2", f"/usr/bin/{binary}")
        utils.ensure_removal("/usr/lib/libbz2.a")


class Xz(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/xz-5.4.1",
                "make",
                "make check",
                "make install",
            ]
        )


class Zstd(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "make prefix=/usr",
                "make check",
                "make prefix=/usr install",
            ]
        )
        utils.ensure_removal("/usr/lib/libzstd.a")


class File(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
            ]
        )


class Readline(Package):
    def _inner_build(self):
        utils.modify(
            "Makefile.in",
            lambda line, _: "" if "MV" in line and line[-5:] == ".old\n" else line,
        )
        utils.modify(
            "support/shlib-install",
            lambda line, _: ":\n" if "{OLDSUFF}" in line else line,
        )
        self._run("patch -Np1 -i /sources/readline-8.2-upstream_fix-1.patch")

        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static --with-curses "
                "--docdir=/usr/share/doc/readline-8.2",
                'make SHLIB_LIBS="-lncursesw"',
                'make SHLIB_LIBS="-lncursesw" install',
            ]
        )
        for file in os.listdir("doc"):
            for suffix in ["ps", "pdf", "html", "dvi"]:
                if file[-(len(suffix) + 1) :] == f".{suffix}":
                    self._run(
                        f"install -v -m644 doc/{file} " "/usr/share/doc/readline-8.2"
                    )


class M4(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                # "make check",
                "make install",
            ]
        )


class Bc(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr -G -O3 -r",
                "make",
                "make test",
                "make install",
            ]
        )


class Flex(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --docdir=/usr/share/doc/flex-2.6.4 "
                "--disable-static",
                "make",
                "make check",
                "make install",
            ]
        )
        utils.ensure_symlink("flex", "/usr/bin/lex")


class Tcl(Package):
    def _inner_build(self):
        os.chdir("unix")
        self._run("./configure --prefix=/usr --mandir=/usr/share/man")
        self._run("make")
        utils.modify(
            "tclConfig.sh", lambda line, _: line.replace("/tcl8.6.13/unix", "/usr/lib")
        )
        utils.modify(
            "tclConfig.sh", lambda line, _: line.replace("/tcl8.6.13", "/usr/include")
        )
        for old, new in [
            ("/tcl8.6.13/unix/pkgs/tdbc1.1.5", "/usr/lib/tdbc1.1.5"),
            ("/tcl8.6.13/pkgs/tdbc1.1.5/generic", "/usr/include"),
            ("/tcl8.6.13/pkgs/tdbc1.1.5/library", "/usr/lib/tcl8.6"),
            ("/tcl8.6.13/pkgs/tdbc1.1.5", "/usr/include"),
        ]:
            utils.modify(
                "pkgs/tdbc1.1.5/tdbcConfig.sh", lambda line, _: line.replace(old, new)
            )
        for old, new in [
            ("/tcl8.6.13/unix/pkgs/itcl4.2.3", "/usr/lib/itcl4.2.3"),
            ("/tcl8.6.13/pkgs/itcl4.2.3/generic", "/usr/include"),
            ("tcl8.6.13/pkgs/itcl4.2.3", "/usr/include"),
        ]:
            utils.modify(
                "pkgs/itcl4.2.3/itclConfig.sh", lambda line, _: line.replace(old, new)
            )

        self._run_commands(["make", "make test", "make install"])

        os.chmod("/usr/lib/libtcl8.6.so", 0o755)
        self._run("make install-private-headers")
        utils.ensure_symlink("tclsh8.6", "/usr/bin/tclsh")
        shutil.move("/usr/share/man/man3/Thread.3", "/usr/share/man/man3/Tcl_Thread.3")


class Expect(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --with-tcl=/usr/lib --enable-shared "
                "--mandir=/usr/share/man --with-tclinclude=/usr/include",
                "make",
                "make test",
                "make install",
            ]
        )
        utils.ensure_symlink(
            "expect5.45.4/libexpect5.45.4.so", "/usr/lib/libexpect5.45.4.so"
        )


class Dejagnu(Package):
    def _inner_build(self):
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                "../configure --prefix=/usr",
                "makeinfo --html --no-split -o doc/dejagnu.html " "../doc/dejagnu.texi",
                "makeinfo --plaintext -o doc/dejagnu.txt  ../doc/dejagnu.texi",
                "make install",
                "install -v -dm755 /usr/share/doc/dejagnu-1.6.3",
                "install -v -m644 doc/dejagnu.html doc/dejagnu.txt "
                "/usr/share/doc/dejagnu-1.6.3",
                "make check",
            ]
        )


class Binutils(Package):
    def _inner_build(self):
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                "../configure --prefix=/usr --sysconfdir=/etc --enable-gold "
                "--enable-ld=default --enable-plugins --enable-shared "
                "--disable-werror --enable-64-bit-bfd --with-system-zlib",
                "make tooldir=/usr",
            ]
        )

        subprocess.run("make -k check".split(), env=self.env)
        errors = {}
        for root, dirs, files in os.walk("."):
            for file in files:
                if file[-4:] == ".log":
                    failed_tests = [
                        line
                        for line in utils.read_file(f"{root}/{file}")
                        if line[:5] == "FAIL:"
                    ]
                    if failed_tests:
                        errors[f"{root}/{file}"] = failed_tests
        if len(errors) > 1:
            sys.exit(f"More than one logfile reported errors: {errors}")
        test_suite_errs = errors.get("./gold/testsuite/test-suite.log")
        if test_suite_errs:
            if len(test_suite_errs) > 12:
                sys.exit(
                    "More than the anticipated 12 errors in "
                    "gold/testsuite/test-suite.log"
                )

        self._run("make tooldir=/usr install")

        for name in ["bfd", "ctf", "ctf-nobfd", "sframe", "opcodes"]:
            utils.ensure_removal(f"/usr/lib/lib{name}.a")
        utils.ensure_removal("/usr/share/man/man1/gprofng.1")
        for file in os.listdir("/usr/share/man/man1"):
            if file[:3] == "gp-" and file[-2:] == ".1":
                utils.ensure_removal(f"/usr/share/man/man1/{file}")


class Gmp(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --enable-cxx --disable-static "
                "--docdir=/usr/share/doc/gmp-6.2.1",
                "make",
                "make html",
                "make check",
                "make install",
                "make install-html",
            ]
        )


class Mpfr(Package):
    def _inner_build(self):
        utils.modify(
            "tests/tsprintf.c",
            lambda line, _: line.replace("+01,234,567", "+1,234,567   ").replace(
                "13.10Pd", "13Pd"
            ),
        )
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--enable-thread-safe --docdir=/usr/share/doc/mpfr-4.2.0",
                "make",
                "make html",
                "make check",
                "make install",
                "make install-html",
            ]
        )


class Mpc(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/mpc-1.3.1"
                "make",
                "make html",
                "make check",
                "make install",
                "make install-html",
            ]
        )


class Attr(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static  --sysconfdir=/etc "
                "--docdir=/usr/share/doc/attr-2.5.1",
                "make",
                "make check",
                "make install",
            ]
        )


class Acl(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/acl-2.3.1",
                "make",
                "make install",
            ]
        )


class Libcap(Package):
    def _inner_build(self):
        utils.modify(
            "libcap/Makefile",
            lambda line, _: "" if "install -m" in line and "$(STA" in line else line,
        )
        self._run_commands(
            [
                "make prefix=/usr lib=lib",
                "make test",
                "make prefix=/usr lib=lib install",
            ]
        )


class Shadow(Package):
    def _inner_build(self):
        utils.modify(
            "src/Makefile.in", lambda line, _: line.replace("groups$(EXEEXT)", "")
        )
        makefiles = []
        for root, _, files in os.walk("man"):
            if "Makefile.in" in files:
                makefiles.append(f"{root}/Makefile.in")
        for makefile in makefiles:
            utils.modify(
                makefile,
                lambda line, _: line.replace("groups.1 ", " ")
                .replace("getspnam.3 ", " ")
                .replace("passwd.5 ", " "),
            )
        utils.modify(
            "etc/login.defs",
            lambda line, _: line.replace("#", "").replace("\n", "00\n")
            if "#SHA_CRYPT" in line
            else line,
        )
        for old, new in [
            ("#ENCRYPT_METHOD DES", "ENCRYPT_METHOD SHA512"),
            ("/var/spool/mail", "/var/mail"),
            ("/sbin", ""),
            ("/bin", ""),
        ]:
            utils.modify("etc/login.defs", lambda line, _: line.replace(old, new))
        utils.ensure_touch("/usr/bin/passwd")

        self._run_commands(
            [
                "./configure --sysconfdir=/etc --disable-static "
                "--with-group-name-max-length=32",
                "make",
                "make exec_prefix=/usr install",
                "make -C man install-man",
                "pwconv",
                "grpconv",
            ]
        )


main_build_packages = [
    ManPages,
    IanaEtc,
    Glibc,
    Zlib,
    Bzip2,
    Xz,
    Zstd,
    File,
    Readline,
    M4,
    Bc,
    Flex,
    Tcl,
    Expect,
    Dejagnu,
    Binutils,
    Gmp,
    Mpfr,
    Mpc,
    Attr,
    Acl,
    Libcap,
    Shadow,
]

