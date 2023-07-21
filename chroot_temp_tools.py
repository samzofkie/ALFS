import os, shutil
from phase import Phase


class ChrootTempToolsBuild(Phase):
    def __init__(self, root_dir, file_tracker):
        super().__init__(root_dir, file_tracker)
        self.env = {"PATH": "/usr/bin:/usr/sbin"}

        make_install = ["make", "make install"]
        self.targets["temp_gettext"] = {
            "build_commands": ["./configure --disable-shared", "make"]
        }
        self.targets["temp_bison"] = {
            "build_commands": [
                "./configure --prefix=/usr --docdir=/usr/share/doc/bison-3.8.2"
            ]
            + make_install
        }
        self.targets["temp_perl"] = {
            "build_commands": [
                "sh Configure -des -Dprefix=/usr -Dvendorprefix=/usr "
                "-Dprivlib=/usr/lib/perl5/5.36/core_perl "
                "-Darchlib=/usr/lib/perl5/5.36/core_perl "
                "-Dsitelib=/usr/lib/perl5/5.36/site_perl "
                "-Dsitearch=/usr/lib/perl5/5.36/site_perl "
                "-Dvendorlib=/usr/lib/perl5/5.36/vendor_perl "
                "-Dvendorarch=/usr/lib/perl5/5.36/vendor_perl "
            ]
            + make_install
        }
        self.targets["temp_python"] = {
            "build_commands": [
                "./configure --prefix=/usr --enable-shared --without-ensurepip"
            ]
            + make_install
        }
        self.targets["temp_texinfo"] = {
            "build_commands": ["./configure --prefix=/usr"] + make_install
        }
        self.targets["temp_util-linux"] = {
            "build_commands": [
                "./configure ADJTIME_PATH=/var/lib/hwclock/adjtime "
                "--libdir=/usr/lib --docdir=/usr/share/doc/util-linux-2.38.1 "
                "--disable-chfn-chsh --disable-login --disable-nologin "
                "--disable-su --disable-setpriv --disable-runuser "
                "--disable-pylibmount --disable-static --without-python "
                "runstatedir=/run"
            ]
            + make_install
        }

    def _temp_gettext_after(self):
        for prog in ["msgfmt", "msgmerge", "xgettext"]:
            shutil.copy(f"gettext-tools/src/{prog}", "/usr/bin")
