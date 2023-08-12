import os, shutil, subprocess, sys, re

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


# Takes 8 hours!
class Gcc(Package):
    def _inner_build(self):
        gcc_change_default_64_bit_dir()
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                "../configure --prefix=/usr LD=ld --enable-languages=c,c++ "
                "--enable-default-pie --enable-default-ssp --disable-multilib "
                "--disable-bootstrap --with-system-zlib ",
                "make"
            ]
        )
        
        utils.chown_tree(".", "tester")        
        self._run_as_tester("make -k check")
        
        report = subprocess.run("../contrib/test_summary".split(),
                                   check=True, env=self.env,
                                   capture_output=True).stdout.decode()
        utils.write_file("/gcc-report", [f"{line}\n" 
                                         for line in report.split("\n")])
        
        self._run("make install")
 
        triplet = subprocess.run("gcc -dumpmachine".split(), check=True, env=self.env,
                                 capture_output=True).stdout.decode().strip()
        for suffix in ["", "-fixed"]:
            for root, dirs, files in os.walk(f"/usr/lib/gcc/{triplet}/12.2.0/include{suffix}"):
                for file in files:
                    shutil.chown(f"{root}/{file}", user="root", group="root")
        
        utils.ensure_symlink("../bin/cpp", "/usr/lib/cpp")
        utils.ensure_symlink(f"../../libexec/gcc/{triplet}/12.2.0/liblto_plugin.so",
                             f"/usr/lib/bfd-plugins")

        utils.write_file("dummy.c", "int main(){}")
        cc_output = subprocess.run("cc dummy.c -v -Wl,--verbose".split(),
                                   env=self.env, check=True,
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.STDOUT).stdout.decode()
        
        utils.write_file("dummy.log", [f"{line}\n" for line in
                                       cc_output.split("\n")])
        assert (
            "[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]"
            in subprocess.run("readelf -l a.out".split(), env=self.env,
                              check=True, capture_output=True).stdout.decode()
        )

        dummy_log = utils.read_file("dummy.log")

        assert len(re.findall(r'/usr/lib/gcc.*/S?crt[1in].*succeeded',
                              "".join(dummy_log))) >= 3
        
        begin_index = dummy_log.index("#include <...> search starts here:\n") + 1
        include_paths = [path.strip() for path in 
                         dummy_log[begin_index:begin_index+4]]
        for path in [f"/usr/lib/gcc/{triplet}/12.2.0/include",
                     "/usr/local/include",
                     f"/usr/lib/gcc/{triplet}/12.2.0/include-fixed",
                     "/usr/include"]:
            assert path in include_paths

        linker_paths = re.findall(r'SEARCH.*/usr/lib',
                                  "".join(dummy_log))[0].split("; ")
        linker_paths = [path.split('"')[1] for path in linker_paths]
        for path in [f"/usr/{triplet}/lib64",
                     "/usr/local/lib64",
                     "/lib64",
                     "/usr/lib64",
                     f"/usr/{triplet}/lib",
                     "/usr/local/lib",
                     "/lib",
                     "/usr/lib"]:
            assert path in linker_paths

        assert "attempt to open /usr/lib/libc.so.6 succeeded\n" in dummy_log
        assert ("found ld-linux-x86-64.so.2 at /usr/lib/ld-linux-x86-64.so.2\n"
                in dummy_log)
        
        utils.ensure_dir("/usr/share/gdb/auto-load/usr/lib")
        for file in os.listdir("/usr/lib"):
            if file[-6:] == "gdb.py":
                shutil.move(f"/usr/lib/{file}", 
                            "/usr/share/gdb/auto-load/usr/lib")


class PkgConfig(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "pkg-config"

    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --with-internal-glib "
                "--disable-host-tool --docdir=/usr/share/doc/pkg-config-0.29.2",
                "make",
                "make check",
                "make install"
            ]
        )


class Ncurses(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --mandir=/usr/share/man "
                "--with-shared --without-debug --without-normal "
                "--with-cxx-shared --enable-pc-files --enable-widec "
                "--with-pkg-config-libdir=/usr/lib/pkgconfig ",
                "make",
                "make install"
            ]
        )
        for name in ["curses", "form", "panel", "menu"]:
            utils.ensure_removal(f"/usr/lib/lib{name}.so")
            utils.write_file(f"/usr/lib/lib{name}.so", [f"INPUT(-l{name}w)"])
            utils.ensure_symlink(f"{name}w.pc", f"/usr/lib/pkgconfig/{name}.pc")
        utils.ensure_removal("/usr/lib/libcursesw.so")
        utils.write_file(f"/usr/lib/libcursesw.so", [f"INPUT(-lncursesw)"])
        
        utils.ensure_removal(f"/usr/lib/libcurses.so")
        utils.ensure_symlink(f"libncurses.so", "/usr/lib/libcurses.so")
        
        utils.ensure_dir("/usr/share/doc/ncurses-6.4")
        shutil.copytree("doc", "/usr/share/doc/ncurses-6.4", dirs_exist_ok=True)


class Sed(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make html",
            ]
        )
        utils.chown_tree(".", "tester")
        self._run_as_tester("make check")
        self._run_commands(
            [
                "make install",
                "install -d -m755 /usr/share/doc/sed-4.9",
                "install -m644 doc/sed.html /usr/share/doc/sed-4.9",
            ]
        )


class Psmisc(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make install"
            ]
        )


class Gettext(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/gettext-0.21.1 ",
                "make",
                #"make check",
                "make install"
            ]
        )
        os.chmod("/usr/lib/preloadable_libintl.so", 0o755)


class Bison(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --docdir=/usr/share/doc/bison-3.8.2",
                "make",
                "make check",
                "make install",
            ]
        )


class Grep(Package):
    def _inner_build(self):
        utils.modify(
            "src/egrep.sh",
            lambda line, _: line.replace("echo", "#echo")
        )
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                #"make check",
                "make install",
            ]
        )


class Bash(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --without-bash-malloc "
                "--with-installed-readline --docdir=/usr/share/doc/bash-5.2.15",
                "make",
            ]
        )
        utils.chown_tree(".", "tester")
        self._run_as_tester("make tests")
        self._run("make install")


class Libtool(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr ",
                "make",
                #"make -k check",
                "make install",
            ]
        )
        utils.ensure_removal("/usr/lib/libltdl.a")


class Gdbm(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--enable-libgdbm-compat",
                "make",
                "make check",
                "make install",
            ]
        )


class Gperf(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --docdir=/usr/share/doc/gperf-3.1",
                "make",
                "make -j1 check",
                "make install",
            ]
        )


class Expat(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/expat-2.5.0",
                "make",
                "make check",
                "make install",
            ]
        )
        for file in os.listdir("doc"):
            if file[-5:] == ".html" or file[-4:] == ".css":
                self._run(f"install -v -m644 doc/{file} /usr/share/doc/expat-2.5.0")


class Inetutils(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --bindir=/usr/bin "
                "--localstatedir=/var --disable-logger --disable-whois "
                "--disable-rcp --disable-rexec --disable-rlogin --disable-rsh "
                "--disable-servers ",
                "make",
                #"make check",
                "make install"
            ]
        )
        if not os.path.exists("/usr/sbin/ifconfig"):
            shutil.move("/usr/bin/ifconfig", "/usr/sbin/ifconfig")


class Less(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --sysconfdir=/etc",
                "make",
                "make install"
            ]
        )


class Perl(Package):
    def _inner_build(self):
        self.env["BUILD_ZLIB"] = "False"
        self.env["BUILD_BZIP2"] = "0"
        config_command = (
            "sh Configure -des -Dprefix=/usr -Dvendorprefix=/usr "
            "-Dprivlib=/usr/lib/perl5/5.36/core_perl "
            "-Darchlib=/usr/lib/perl5/5.36/core_perl "
            "-Dsitelib=/usr/lib/perl5/5.36/site_perl "
            "-Dsitearch=/usr/lib/perl5/5.36/site_perl "
            "-Dvendorlib=/usr/lib/perl5/5.36/vendor_perl "
            "-Dvendorarch=/usr/lib/perl5/5.36/vendor_perl "
            "-Dman1dir=/usr/share/man/man1 "
            "-Dman3dir=/usr/share/man/man3 "
            '-Dpager="/usr/bin/less-isR" '
            "-Duseshrplib -Dusethreads ").split()
        config_command[-3] = '-Dpager="/usr/bin/less -isR"'
        subprocess.run(config_command, env=self.env, check=True)
        self._run_commands(
            [
                "make",
                #"make test",
                "make install",
            ]
        ) 
        del self.env["BUILD_ZLIB"]
        del self.env["BUILD_BZIP2"]


class XmlParser(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "XML-Parser"

    def _inner_build(self):
        self._run_commands(
            [
                "perl Makefile.PL",
                "make",
                "make test",
                "make install"
            ]
        )


class Intltool(Package):
    def _inner_build(self):
        utils.modify(
            "intltool-update.in",
            lambda line, _: line.replace("\${", "\$\{")
        )
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
                "install -v -Dm644 doc/I18N-HOWTO /usr/share/doc/intltool-0.51.0/I18N-HOWTO"
            ]
        )


class Autoconf(Package):
    def _inner_build(self):
        shutil.copy("tests/local.at", "tests/local.at.orig")
        utils.modify(
            "tests/local.at",
            lambda line, _: line.replace(
                "|START_TIME|", "|SHLVL|START_TIME|"
                ).replace(
                    "/^BASH_ARGV=/ d\n",
                    "/^BASH_ARGV=/ d\n        /^SHLVL=/ d\n"
                )
        )
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
            ]
        )


class Automake(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr "
                "--docdir=/usr/share/doc/automake-1.16.5",
                "make",
                #"make -j4 check",
                "make install"
            ]
        )


class Openssl(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./config --prefix=/usr --openssldir=/etc/ssl --libdir=lib "
                "shared zlib-dynamic ",
                "make",
                "make test",
            ]
        )
        utils.modify(
            "Makefile",
            lambda line, _: line.replace("libcrypto.a libssl.a", "") 
                if "INSTALL_LIBS" in line else line
        )
        self._run("make MANSUFFIX=ssl install")
        os.rename("/usr/share/doc/openssl", "/usr/share/doc/openssl-3.0.8")
        shutil.copytree("doc", "/usr/share/doc/openssl-3.0.8",
                        dirs_exist_ok=True)


class Kmod(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --sysconfdir=/etc --with-openssl "
                "--with-xz --with-zstd --with-zlib",
                "make",
                "make install"
            ]
        )
        for target in ["depmod", "insmod", "modinfo", "modprobe", "rmmod"]:
            utils.ensure_symlink("../bin/kmod", f"/usr/sbin/{target}")
        utils.ensure_symlink("kmod", "/usr/bin/lsmod")


class Elfutils(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-debuginfod "
                "--enable-libdebuginfod=dummy",
                "make",
                #"make check",
                "make -C libelf install",
                "install -vm644 config/libelf.pc /usr/lib/pkgconfig",
            ]
        )
        utils.ensure_removal("/usr/lib/libelf.a")


class Libffi(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static "
                "--with-gcc-arch=native",
                "make",
                "make check",
                "make install",
            ]
        )


class Python(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "Python"

    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --enable-shared --with-system-expat "
                "--with-system-ffi --enable-optimizations",
                "make",
                "make install",
                "install -v -dm755 /usr/share/doc/python-3.11.2/html",
                "tar --strip-components=1 --no-same-owner --no-same-permissions "
                "-C /usr/share/doc/python-3.11.2/html -xvf "
                "/sources/python-3.11.2-docs-html.tar.bz2",
            ]
        )


class Wheel(Package):
    def _inner_build(self):
        self.env["PYTHONPATH"] = "src"
        self._run("pip3 wheel -w dist --no-build-isolation --no-deps "
                 f"{os.getcwd()}")
        del self.env["PYTHONPATH"]
        self._run("pip3 install --no-index --find-links=dist wheel")


class Ninja(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "python3 configure.py --bootstrap",
                "./ninja ninja_test",
                "./ninja_test --gtest_filter=-SubprocessTest.SetWithLots",
                "install -vm755 ninja /usr/bin/",
                "install -vDm644 misc/bash-completion "
                "/usr/share/bash-completion/completions/ninja",
                "install -vDm644 misc/zsh-completion  "
                "/usr/share/zsh/site-functions/_ninja",
            ]
        )


class Meson(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "pip3 wheel -w dist --no-build-isolation --no-deps "
                f"{os.getcwd()}",
                "pip3 install --no-index --find-links dist meson",
                "install -vDm644 data/shell-completions/bash/meson "
                "/usr/share/bash-completion/completions/meson",
                "install -vDm644 data/shell-completions/zsh/_meson "
                "/usr/share/zsh/site-functions/_meson",
            ]
        )


class Coreutils(Package):
    def _inner_build(self):
        self.env["FORCE_UNSAFE_CONFIGURE"] = "1" 
        self._run_commands(
            [
                "patch -Np1 -i /sources/coreutils-9.1-i18n-1.patch",
                "autoreconf -fiv",
                "./configure --prefix=/usr "
                "--enable-no-install-program=kill,uptime ",
                "make",
                "make NON_ROOT_USERNAME=tester check-root",
            ]
        )
        del self.env["FORCE_UNSAFE_CONFIGURE"]
        utils.write_file(
            "/etc/group",
            utils.read_file("/etc/group") + ["dummy:x:102:tester"]
        )
        utils.chown_tree(".", "tester")
        self._run_as_tester("make RUN_EXPENSIVE_TESTS=yes check")
        utils.write_file(
            "/etc/group",
            utils.read_file("/etc/group")[:-1]
        )
        self._run("make install")
        os.replace("/usr/bin/chroot", "/usr/sbin/chroot")
        utils.ensure_dir("/usr/share/man/man8")
        os.replace("/usr/share/man/man1/chroot.1",
                    "/usr/share/man/man8/chroot.8")
        utils.modify(
            "/usr/share/man/man8/chroot.8",
            lambda line, _: line.replace('"1"', '"8"')
        )


class Check(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-static",
                "make",
                "make check",
                "make docdir=/usr/share/doc/check-0.15.2 install"
            ]
        )


class Diffutils(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                #"make check",
                "make install"
            ]
        )


class Gawk(Package):
    def _inner_build(self):
        utils.modify(
            "Makefile.in",
            lambda line, _: line.replace("extras", "")
        )
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
            ]
        )
        subprocess.run(["make", "LN='ln -f'", "install"], check=True,
                       env=self.env)
        utils.ensure_dir("/usr/share/doc/gawk-5.2.1")
        shutil.copy("doc/awkforai.txt", "/usr/share/doc/gawk-5.2.1")
        for file in os.listdir("doc"):
            if file[-4:] in [".eps", ".pdf", ".jpg"]:
                shutil.copy(f"doc/{file}", "/usr/share/doc/gawk-5.2.1")


class Findutils(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr --localstatedir=/var/lib/locate",
                "make"
            ]
        )
        utils.chown_tree(".", "tester")
        self._run_as_tester("make check")
        self._run("make install")


class Groff(Package):
    def _inner_build(self):
        self.env["PAGE"] = "letter"
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make install"
            ]
        )
        del self.env["PAGE"]


class Gzip(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                #"make check",
                "make install",
            ]
        )


class Iproute(Package):
    def _inner_build(self):
        utils.modify(
            "Makefile",
            lambda line, _: "" if "ARPD" in line else line
        )
        utils.ensure_removal("man/man8/arpd.8")
        self._run_commands(
            [
                "make NETNS_RUN_DIR=/run/netns",
                "make SBINDIR=/usr/sbin install",
            ]
        )
        utils.ensure_dir("/usr/share/doc/iproute2-6.1.0")
        for file in os.listdir():
            if file[:6] == "README" or file == "COPYING":
                shutil.copy(file, "/usr/share/doc/iproute2-6.1.0")


class Kbd(Package):
    def _inner_build(self):
        self._run("patch -Np1 -i /sources/kbd-2.5.1-backspace-1.patch")
        utils.modify(
            "configure",
            lambda line, _: line.replace("yes", "no") 
                if "RESIZECONS_PROGS=" in line else line
        )
        utils.modify(
            "docs/man/man8/Makefile.in",
            lambda line, _: line.replace("resizecons.8 ", "")
        )
        self._run_commands(
            [
                "./configure --prefix=/usr --disable-vlock",
                "make",
                "make check",
                "make install"
            ]
        )
        utils.ensure_dir("/usr/share/doc/kbd-2.5.1")
        shutil.copytree("docs/doc", "/usr/share/doc/kbd-2.5.1",
                        dirs_exist_ok=True)


class Libpipeline(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
            ]
        )


class Make(Package):
    def _inner_build(self):
        utils.modify(
            "src/main.c",
            lambda line, i: "" if i in range(1185,1189) 
                else line.replace("#undef  FATAL_SIG",
                                  "FATAL_SIG (SIGPIPE);\n#undef  FATAL_SIG")
        )
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
            ]
        )


class Patch(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
            ]
        )


class Tar(Package):
    def _inner_build(self):
        self.env["FORCE_UNSAFE_CONFIGURE"] = "1"
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                #"make check",
                "make install",
                "make -C doc install-html docdir=/usr/share/doc/tar-1.34",
            ]
        )
        del self.env["FORCE_UNSAFE_CONFIGURE"]


class Texinfo(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install",
                "make TEXMF=/usr/share/texmf install-tex"
            ]
        )


class Vim(Package):
    def _inner_build(self):
        utils.write_file(
            "src/feature.h", 
            utils.read_file("src/feature.h") + 
            ['\n#define SYS_VIMRC_FILE "/etc/vimrc"']
        )
        self._run_commands(
            [
                "./configure --prefix=/usr",
                "make",
            ]
        )

        utils.chown_tree(".", "tester") 
        self.env["LANG"] = "en_US.UTF-8"
        self._run_as_tester("make -j1 test")
        del self.env["LANG"]
        
        self._run("make install")
        utils.ensure_symlink("../vim/vim90/doc", "/usr/share/doc/vim-9.0.1273")


class Eudev(Package):
    def _inner_build(self):
        utils.modify(
            "src/udev/udev.pc.in",
            lambda line, _: line + "\nudev_dir=${udevdir}" 
                if "udevdir" in line else line
        )
        self._run_commands(
            [
                "./configure --prefix=/usr --bindir=/usr/sbin "
                "--sysconfdir=/etc --enable-manpages --disable-static ",
                "make"
            ]
        )
        utils.ensure_dir("/usr/lib/udev/rules.d")
        utils.ensure_dir("/etc/udev/rules.d")
        self._run_commands(
            [
                "make check",
                "make install",
                "tar -xvf /sources/udev-lfs-20171102.tar.xz",
                "make -f udev-lfs-20171102/Makefile.lfs install",
                "udevadm hwdb --update",
            ]
        )


class ManDb(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "man-db"

    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr "
                "--docdir=/usr/share/doc/man-db-2.11.2 --sysconfdir=/etc "
                "--disable-setuid --enable-cache-owner=bin "
                "--with-browser=/usr/bin/lynx --with-vgrind=/usr/bin/vgrind "
                "--with-grap=/usr/bin/grap --with-systemdtmpfilesdir= "
                "--with-systemdsystemunitdir= ",
                "make",
                "make check",
                "make install",
            ]
        )


class Procps(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "./configure --prefix=/usr "
                "--docdir=/usr/share/doc/procps-ng-4.0.2 --disable-static "
                "--disable-kill ",
                "make",
                #"make check",
                "make install",
            ]
        )


class UtilLinux(Package):
    def __init__(self, root, ft):
        super().__init__(root, ft)
        self.search_term = "util-linux"

    def _inner_build(self):
        self._run_commands(
            [
                "./configure ADJTIME_PATH=/var/lib/hwclock/adjtime "
                "--bindir=/usr/bin --libdir=/usr/lib --sbindir=/usr/sbin "
                "--disable-chfn-chsh --disable-login --disable-nologin "
                "--disable-su --disable-setpriv --disable-runuser "
                "--disable-pylibmount --disable-static --without-python "
                "--without-systemd --without-systemdsystemunitdir "
                "--docdir=/usr/share/doc/util-linux-2.38.1 ",
                "make"
            ]
        )
        utils.chown_tree(".", "tester")
        self._run_as_tester("make -k check")
        self._run("make install")


class E2fsprog(Package):
    def _inner_build(self):
        self._create_and_enter_build_dir()
        self._run_commands(
            [
                "../configure --prefix=/usr --sysconfdir=/etc "
                "--enable-elf-shlibs --disable-libblkid --disable-libuuid "
                "--disable-uuidd --disable-fsck ",
                "make",
                "make check",
                "make install"
            ]
        )
        for archive in ["libcom_err", "libe2p", "libext2fs", "libss"]:
            utils.ensure_removal(f"/usr/lib/{archive}.a")
        self._run_commands(
            [
                "gunzip -v /usr/share/info/libext2fs.info.gz",
                "install-info --dir-file=/usr/share/info/dir "
                "/usr/share/info/libext2fs.info",
                "makeinfo -o doc/com_err.info ../lib/et/com_err.texinfo",
                "install -v -m644 doc/com_err.info /usr/share/info",
                "install-info --dir-file=/usr/share/info/dir "
                "/usr/share/info/com_err.info"
            ]
        )
        utils.modify(
            "/etc/mke2fs.conf",
            lambda line, _: line.replace("metadata_csum_seed,", "")
        )


class Sysklogd(Package):
    def _inner_build(self):
        utils.modify(
            "ksym_mod.c",
            lambda line, i: line + " " * 16 + "fclose(ksyms);\n"
                if i == 191 else line
        )
        utils.modify(
            "syslogd.c",
            lambda line, _: line.replace("union wait", "int")
        )
        self._run_commands(
            [
                "make",
                "make BINDIR=/sbin install",
            ]
        )


class Sysvinit(Package):
    def _inner_build(self):
        self._run_commands(
            [
                "patch -Np1 -i /sources/sysvinit-3.06-consolidated-1.patch",
                "make",
                "make install",
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
    Gcc,
    PkgConfig,
    Ncurses,
    Sed,
    Psmisc,
    Gettext,
    Bison,
    Grep,
    Bash,
    Libtool,
    Gdbm,
    Gperf,
    Expat,
    Inetutils,
    Less,
    Perl,
    XmlParser,
    Intltool,
    Autoconf,
    Automake,
    Openssl,
    Kmod,
    Elfutils,
    Libffi,
    Python,
    Wheel,
    Ninja,
    Meson,
    Coreutils,
    Check,
    Diffutils,
    Gawk,
    Findutils,
    Groff,
    Gzip,
    Iproute,
    Kbd,
    Libpipeline,
    Make,
    Patch,
    Tar,
    Texinfo,
    Vim,
    Eudev,
    ManDb,
    Procps,
    UtilLinux,
    E2fsprog,
    Sysklogd,
]

