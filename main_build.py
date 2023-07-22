import os, shutil, subprocess
from phase import Phase


class MainBuild(Phase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)
        self.env = {"PATH": "/usr/bin:/usr/sbin"}

        self.targets["man-pages"] = {"build_commands": ["make prefix=/usr install"]}
        self.targets["iana-etc"] = {"build_commands": []}
        self.targets["glibc"] = {
            "build_commands": [
                "../configure --prefix=/usr --disable-werror "
                "--enable-kernel=3.2 --enable-stack-protector=strong "
                "--with-headers=/usr/include libc_cv_slibdir=/usr/lib ",
                "make",
            ],
            "build_dir": True,
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
        subprocess.run("localedef -i POSIX -f UTF-8 C.UTF-8", env=self.env)
        subprocess.run("localedef -i ja_JP -f SHIFT_JIS ja_JP.SJIS", env=self.env)
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
        with open("/etc/ld.so.conf" "w") as f:
            f.write("/usr/local/lib\n/opt/lib\n")
