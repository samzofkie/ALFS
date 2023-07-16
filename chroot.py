import os, subprocess, shutil, stat
from setup import ROOT_DIR


CHROOT_DIRS = ["dev", "proc", "sys", "run", "boot", "home/tester", "mnt", "opt", 
               "srv", "root", "tmp", "usr/lib/firmware"]
CHROOT_DIRS += ["etc/" + d for d in ["opt", "sysconfig"]]
CHROOT_DIRS += ["media/" + d for d in ["floppy", "cdrom"]]
CHROOT_DIRS += ["usr/local/" + d for d in ["bin", "lib", "sbin"]]
for prefix in ["usr/", "usr/local/"]:
    CHROOT_DIRS += [prefix + d for d in ["include", "src"]]
    CHROOT_DIRS += [prefix + "share/" + d for d in ["color", "dict", "doc", 
                                             "info", "locale", "man",
                                             "misc", "terminfo", 
                                             "zoneinfo"]]
    CHROOT_DIRS += [prefix + "share/man/man" + str(i) for i in range(9)]
CHROOT_DIRS += ["var/" + d for d in ["cache", "local", "log", "mail", "opt",
                                     "spool", "tmp"]]
CHROOT_DIRS += ["var/lib/" + d for d in ["color", "misc", "locate"]]


def _mount_vkfs(): 
    """ Mount Virtual Kernel Filesystems"""
    for command in [f"mount -v --bind /dev {ROOT_DIR}/dev",
                    f"mount -v --bind /dev/pts {ROOT_DIR}/dev/pts",
                    f"mount -vt proc proc {ROOT_DIR}/proc",
                    f"mount -vt sysfs sysfs {ROOT_DIR}/sys",
                    f"mount -vt tmpfs tmpfs {ROOT_DIR}/run" ]:
        ret = subprocess.run(command.split(), check=True)


def _enter_chroot():
    os.chdir(ROOT_DIR)
    os.chroot(ROOT_DIR)
    for var in os.environ:
        del os.environ[var]
    os.environ["PATH"] = "/usr/bin:/usr/sbin" 


def _make_additional_dirs():
    for d in CHROOT_DIRS:
        if not os.path.exists(d):
            os.makedirs(d)
    os.symlink("/run", "/var/run")
    os.symlink("/run/lock", "/var/lock")
    subprocess.run("chmod 1777 /tmp /var/tmp".split(), check=True)
    shutil.chown("/home/tester", user="tester")
    for file in ["btmp", "lastlog", "faillog", "wtmp"]:
        with open("/var/log/" + file, "a") as f:
            pass
    shutil.chown("/var/log/lastlog", group="utmp")
    os.chmod("/var/log/lastlog", stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
             stat.S_IWGRP | stat.S_IROTH)
    os.chmod("/var/log/btmp", stat.S_IRUSR | stat.S_IWUSR)


def prepare_and_enter_chroot():
    _mount_vkfs()
    _enter_chroot()
    _make_additional_dirs()


