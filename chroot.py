import os, subprocess, shutil, stat
from setup import ROOT_DIR


def _mount_vkfs(): 
    """ Mount Virtual Kernel Filesystems"""
    for dir in ["dev", "proc", "sys", "run"]:
        os.mkdir(f"{ROOT_DIR}/{dir}")
    for command in [f"mount -v --bind /dev {ROOT_DIR}/dev",
                    f"mount -v --bind /dev/pts {ROOT_DIR}/dev/pts",
                    f"mount -vt proc proc {ROOT_DIR}/proc",
                    f"mount -vt sysfs sysfs {ROOT_DIR}/sys",
                    f"mount -vt tmpfs tmpfs {ROOT_DIR}/run" ]:
        if os.system(command) != 0:
            exit(f"Command: '{command}' failed")


def _enter_chroot():
    os.chdir(ROOT_DIR)
    os.chroot(ROOT_DIR)
    for var in os.environ:
        del os.environ[var]
    os.environ["PATH"] = "/usr/bin:/usr/sbin" 


def _make_additional_dirs():
    dirs = ["boot", "home/tester", "mnt", "opt", "srv", "root", 
            "usr/lib/firmware"]
    dirs += ["etc/" + d for d in ["opt", "sysconfig"]]
    dirs += ["media/" + d for d in ["floppy", "cdrom"]]
    dirs += ["usr/local/" + d for d in ["bin", "lib", "sbin"]]
    for prefix in ["usr/", "usr/local/"]:
        dirs += [prefix + d for d in ["include", "src"]]
        dirs += [prefix + "share/" + d for d in ["color", "dict", "doc", 
                                                 "info", "locale", "man",
                                                 "misc", "terminfo", 
                                                 "zoneinfo"]]
        dirs += [prefix + "share/man/man" + str(i) for i in range(9)]
    dirs += ["var/" + d for d in ["cache", "local", "log", "mail", "opt",
                                  "spool", "tmp"]]
    dirs += ["var/lib/" + d for d in ["color", "misc", "locate"]]
    for d in dirs:
        os.makedirs(d)
    os.symlink("/run", "/var/run")
    os.symlink("/run/lock", "/var/lock")
    subprocess.run("chmod 1777 /tmp /var/tmp", check=True)
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


