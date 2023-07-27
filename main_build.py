import os, shutil, subprocess
from phase import Phase


class MainBuild(Phase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)
        self.env = {"PATH": "/usr/bin:/usr/sbin", "CC": "gcc"}

        self.targets["man-pages"] = {"build_commands": ["make prefix=/usr install"]}
        self.targets["iana-etc"] = {"build_commands": []}
        self.targets["glibc"] = {
            "build_commands": [
                "../configure --prefix=/usr --disable-werror "
                "--enable-kernel=3.2 --enable-stack-protector=strong "
                "--with-headers=/usr/include libc_cv_slibdir=/usr/lib ",
                "make",
            ],
            "build_dir": True
        }
        self.targets["zlib"] = {
            "build_commands": [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install"
            ]
        }
        self.targets["bzip2"] = {
            "build_commands": [
                "make -f Makefile-libbz2_so",
                "make clean",
                "make",
                "make PREFIX=/usr install"
            ]
        }
        self.targets["xz"] = {
            "build_commands": [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/xz-5.4.1",
                "make",
                "make check",
                "make install"
            ]
        }
        self.targets["zstd"] = {
            "build_commands": [
                "make prefix=/usr",
                "make check",
                "make prefix=/usr install"
            ]
        }
        self.targets["file"] = {
            "build_commands": [
                "./configure --prefix=/usr",
                "make",
                "make check",
                "make install"
            ]
        }
        self.targets["readline"] = {
            "build_commands": [
                "./configure --prefix=/usr --disable-static --with-curses "
                "--docdir=/usr/share/doc/readline-8.2",
                'make SHLIB_LIBS="-lncursesw"',
                'make SHLIB_LIBS="-lncursesw" install'
            ]
        }
        self.targets["m4"] = {
            "build_commands": [
                "./configure --prefix=/usr",
                "make",
                #"make check",
                "make install"
            ]
        }
        self.targets["bc"] = {
            "build_commands": [
                "./configure --prefix=/usr -G -O3 -r",
                "make",
                "make test",
                "make install"
            ]
        }
        self.targets["flex"] = {
            "build_commands": [
                "./configure --prefix=/usr --docdir=/usr/share/doc/flex-2.6.4 "
                "--disable-static",
                "make",
                "make check",
                "make install"
            ]
        }
        self.targets["tcl"] = {
            "build_commands": [
                "make test",
                "make install"
            ]
        }
        self.targets["expect"] = {
            "build_commands": [
                "./configure --prefix=/usr --with-tcl=/usr/lib --enable-shared "
                "--mandir=/usr/share/man --with-tclinclude=/usr/include",
                "make",
                "make test",
                "make install"
            ]
        }
        self.targets["dejagnu"] = {
            "build_commands": [
                "../configure --prefix=/usr",
                "makeinfo --html --no-split -o doc/dejagnu.html "
                "../doc/dejagnu.texi",
                "makeinfo --plaintext -o doc/dejagnu.txt  ../doc/dejagnu.texi",
                "make install",
                "install -v -dm755 /usr/share/doc/dejagnu-1.6.3",
                "install -v -m644 doc/dejagnu.html doc/dejagnu.txt "
                "/usr/share/doc/dejagnu-1.6.3",
                "make check"
            ],
            "build_dir": True
        }
        self.targets["binutils"] = {
            "build_commands": [
                "../configure --prefix=/usr --sysconfdir=/etc --enable-gold "
                "--enable-ld=default --enable-plugins --enable-shared "
                "--disable-werror --enable-64-bit-bfd --with-system-zlib",
                "make tooldir=/usr",
                #"make -k check",
                "make tooldir=/usr install"
            ],
            "build_dir": True
        }
        make_html_check_install = ["make", "make html", "make check", 
            "make install", "make install-html"]
        self.targets["gmp"] = {
            "build_commands": [
                "./configure --prefix=/usr --enable-cxx --disable-static "
                "--docdir=/usr/share/doc/gmp-6.2.1",
            ] + make_html_check_install
        }
        self.targets["mpfr"] = {
            "build_commands": [
                "./configure --prefix=/usr --disable-static "
                "--enable-thread-safe --docdir=/usr/share/doc/mpfr-4.2.0",
            ] + make_html_check_install
        }
        self.targets["mpc"] = {
            "build_commands": [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/mpc-1.3.1"
            ] + make_html_check_install
        }
        self.targets["attr"] = {
            "build_commands": [
                "./configure --prefix=/usr --disable-static  --sysconfdir=/etc "
                "--docdir=/usr/share/doc/attr-2.5.1",
                "make",
                "make check",
                "make install"
            ]
        }
        self.targets["acl"] = {
            "build_commands": [
                "./configure --prefix=/usr --disable-static "
                "--docdir=/usr/share/doc/acl-2.3.1",
                "make",
                "make install"
            ]
        }
        self.targets["libcap"] = {
            "build_commands": [
                "make prefix=/usr lib=lib",
                "make test",
                "make prefix=/usr lib=lib install"
            ]
        }
        self.targets["shadow"] = {
            "build_commands": [
                "./configure --sysconfdir=/etc --disable-static "
                "--with-group-name-max-length=32",
                "make",
                "make exec_prefix=/usr install",
                "make -C man install-man"
            ]
        }

    def _iana_etc_after(self):
        shutil.copy("services", "/etc")
        shutil.copy("protocols", "/etc")

    def _glibc_before(self):
        self._run("patch -Np1 -i /sources/glibc-2.37-fhs-1.patch")
        with open("stdio-common/vfprintf-process-arg.c", "r") as f:
            lines = f.readlines()
        lines[265] = lines[265].replace("workend - string", "number_length")
        with open("stdio-common/vfprintf-process-arg.c", "w") as f:
            f.writelines(lines)
        if not os.path.exists("build"):
            os.mkdir("build")
        with open("build/configparms", "w") as f:
            f.write("rootsbindir=/usr/sbin")

    def _glibc_after(self):
        with open("/etc/ld.so.conf", "w") as f:
            pass
        with open("../Makefile", "r") as f:
            lines = f.readlines()
        lines[118] = lines[118].replace("$(PERL)", "echo not running")
        with open("../Makefile", "w") as f:
            f.writelines(lines)
        self._run("make install")
        with open("/usr/bin/ldd", "r") as f:
            lines = f.readlines()
        lines[28] = lines[28].replace("/usr", "")
        with open("/usr/bin/ldd", "w") as f:
            f.writelines(lines)
        shutil.copy("../nscd/nscd.conf", "/etc")
        os.makedirs("/var/cache/nscd")
        os.makedirs("/usr/lib/locale")
        self._run("make localedata/install-locales")
        subprocess.run("localedef -i POSIX -f UTF-8 C.UTF-8".split(), env=self.env)
        subprocess.run("localedef -i ja_JP -f SHIFT_JIS ja_JP.SJIS".split(), env=self.env)
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
        os.symlink("/usr/share/zoneinfo/Chicago", "/etc/localtime")
        with open("/etc/ld.so.conf", "w") as f:
            f.write("/usr/local/lib\n/opt/lib\n")

    def _zlib_after(self):
        if os.path.exists("/usr/lib/libz.a"):
            os.remove("/usr/lib/libz.a")

    def _bzip2_before(self):
        self._run("patch -Np1 -i /sources/bzip2-1.0.8-install_docs-1.patch")
        with open("Makefile", "r") as f:
            lines = f.readlines()
        for i in range(len(lines)):
            if "ln -s -f $(PREFIX)" in lines[i]:
                lines[i] = lines[i].replace("$(PREFIX)/bin/", "", 1)
            if "$(PREFIX)/man" in lines[i]:
                lines[i] = lines[i].replace("$(PREFIX)/man",
                                            "$(PREFIX)/share/man")
        with open("Makefile", "w") as f:
            f.writelines(lines)

    def _bzip2_after(self):
        shutil.copy("libbz2.so.1.0.8", "/usr/lib")
        os.symlink("libbz2.so.1.0.8", "/usr/lib/libbz2.so.1.0")
        os.symlink("libbz2.so.1.0.8", "/usr/lib/libbz2.so")
        shutil.copy("bzip2-shared", "/usr/bin/bzip2")
        for binary in ["bzcat", "bunzip2"]:
            if os.path.exists(f"/usr/bin/{binary}"):
                os.remove(f"/usr/bin/{binary}")
            os.symlink("bzip2", f"/usr/bin/{binary}")
        os.remove("/usr/lib/libbz2.a")

    def _zstd_after(self):
        if os.path.exists("/usr/lib/libzstd.a"):
            os.remove("/usr/lib/libzstd.a")

    def _readline_before(self):
        with open("Makefile.in", "r") as f:
            lines = f.readlines()
        lines = [line for line in lines if not ("MV" in line and line[-5:] ==
                                                ".old\n")]
        with open("Makefile.in", "w") as f:
            f.writelines(lines)
        with open("support/shlib-install", "r") as f:
            lines = f.readlines()
        for i in range(len(lines)):
            if "{OLDSUFF}" in lines[i]:
                lines[i] = ":\n"
        with open("support/shlib-install", "w") as f:
            f.writelines(lines)
            self._run("patch -Np1 -i /sources/readline-8.2-upstream_fix-1.patch")

    def _readline_after(self):
        for file in os.listdir("doc"):
            for suffix in ["ps", "pdf", "html", "dvi"]:
                if file[-(len(suffix)+1):] == f".{suffix}":
                    self._run(f"install -v -m644 doc/{file} "
                        "/usr/share/doc/readline-8.2")

    def _flex_after(self):
        os.symlink("flex", "/usr/bin/lex")

    def _tcl_before(self):
        os.chdir("unix")
        self._run("./configure --prefix=/usr --mandir=/usr/share/man")
        self._run("make")
        
        with open("tclConfig.sh", "r") as f:
            lines = f.readlines()
        lines = [line.replace("/tcl8.6.13/unix", "/usr/lib") for line in lines]
        lines = [line.replace("/tcl8.6.13", "/usr/include") for line in lines]
        with open("tclConfig.sh", "w") as f:
            f.writelines(lines)

        with open("pkgs/tdbc1.1.5/tdbcConfig.sh", "r") as f:
            lines = f.readlines()
        lines = [line.replace("/tcl8.6.13/unix/pkgs/tdbc1.1.5",
                              "/usr/lib/tdbc1.1.5") for line in lines]
        lines = [line.replace("/tcl8.6.13/pkgs/tdbc1.1.5/generic", 
                              "/usr/include") for line in lines]
        lines = [line.replace("/tcl8.6.13/pkgs/tdbc1.1.5/library",
                              "/usr/lib/tcl8.6") for line in lines]
        lines = [line.replace("/tcl8.6.13/pkgs/tdbc1.1.5",
                              "/usr/include") for line in lines]
        with open("pkgs/tdbc1.1.5/tdbcConfig.sh", "w") as f:
            f.writelines(lines)

        with open("pkgs/itcl4.2.3/itclConfig.sh", "r") as f:
            lines = f.readlines()
        lines = [line.replace("/tcl8.6.13/unix/pkgs/itcl4.2.3",
                              "/usr/lib/itcl4.2.3") for line in lines]
        lines = [line.replace("/tcl8.6.13/pkgs/itcl4.2.3/generic",
                              "/usr/include") for line in lines]
        lines = [line.replace("tcl8.6.13/pkgs/itcl4.2.3", 
                              "/usr/include") for line in lines]
        with open("pkgs/itcl4.2.3/itclConfig.sh", "w") as f:
            f.writelines(lines)
    
    def _tcl_after(self):
        os.chmod("/usr/lib/libtcl8.6.so", 0o755)
        self._run("make install-private-headers")
        if not os.path.islink("/usr/bin/tclsh"):
            os.symlink("tclsh8.6", "/usr/bin/tclsh")
        shutil.move("/usr/share/man/man3/Thread.3",
            "/usr/share/man/man3/Tcl_Thread.3")

    def _expect_after(self):
        if not os.path.exists("/usr/lib/libexpect5.45.4.so"):
            os.symlink("expect5.45.4/libexpect5.45.4.so", "/usr/lib")

    def _binutils_after(self):
        for name in ["bfd", "ctf", "ctf-nobfd", "sframe", "opcodes"]:
            os.remove(f"/usr/lib/lib{name}.a")
        os.remove("/usr/share/man/man1/gprofng.1")
        for file in os.listdir("/usr/share/man/man1"):
            if file[:3] == "gp-" and file[-2:] == ".1":
                os.remove(f"/usr/share/man/man1/{file}")

    def _mpfr_before(self):
        with open("test/tsprintf.c", "r") as f:
            lines = f.readlines()
        lines = [line.replace("+01,234,567", "+1,234,567 ") for line in lines]
        lines = [line.replace("13.10Pd", "13Pd") for line in lines]

    def _libcap_before(self):
        with open("libcap/Makefile", "r") as f:
            lines = f.readlines()
        lines = [line for line in lines if not ("install -m" in line and
                                           "$(STA" in line)]
        with open("libcap/Makefile", "w") as f:
            f.writelines(lines)

    def _shadow_before(self):
        with open("src/Makefile.in", "r") as f:
            lines = f.readlines()
        lines = [line.replace("groups$(EXEEXT) ", "") for line in lines]
        with open("src/Makefile.in", "w") as f:
            f.writelines(lines)
        makefiles = []
        for root, _, files in os.walk("man"):
            if "Makefile.in" in files:
                makefiles.append(f"{root}/Makefile.in")
        for makefile in makefiles:
            with open(makefile, "r") as f:
                lines = f.readlines()
            lines = [line.replace("groups.1 ", " ") for line in lines]
            lines = [line.replace("getspnam.3 ", " ") for line in lines]
            lines = [line.replace("passwd.5 ", " ") for line in lines]
            with open(makefile, "w") as f:
                f.writelines(lines)

        with open("etc/login.defs", "r") as f:
            lines = f.readlines()
        lines = [line.replace("#ENCRYPT_METHOD DES", "ENCRYPT_METHOD SHA512")
                 for line in lines]
        for i in range(len(lines)):
            if "#SHA_CRYPT" in lines[i]:
                lines[i] = lines[i].replace("#","") + "00"
        lines = [lines.replace("/var/spool/mail", "/var/mail") for line in
                 lines]
        lines = [line.replace("/sbin:","").replace("/bin:","") for line in
                 lines]
        with open("etc/login.defs", "w") as f:
            f.writelines(f)
        
        with open("/usr/bin/passwd", "w") as f:
            pass
