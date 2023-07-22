#!/usr/bin/env python3
import subprocess, os, shutil, sys


def _remove_dirs():
    package_names = [
        tarball.split(".tar")[0]
        for tarball in os.listdir("sources")
        if ".tar" in tarball
    ]
    sys_dirs = [
        "boot",
        "dev",
        "home",
        "lib64",
        "media",
        "mnt",
        "opt",
        "package-records",
        "proc",
        "root",
        "run",
        "srv",
        "sys",
        "tmp",
        "tools",
        "usr",
        "var",
    ]
    for d in package_names + sys_dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
    for d in ["bin", "lib", "sbin"]:
        if os.path.islink(d):
            os.remove(d)


def _clean_etc():
    """Run outside chroot please!"""
    contents = os.listdir("etc")
    for item in contents:
        if item not in ["group", "hosts", "passwd"]:
            item = "etc/" + item
            if os.path.isfile(item):
                os.remove(item)
            else:
                shutil.rmtree(item)


def umount_vkfs():
    """Run outside the chroot please!"""
    for d in ["dev/pts", "dev", "proc", "sys", "run"]:
        subprocess.run(f"umount {d}".split(), capture_output=True)


def clean():
    umount_vkfs()
    _remove_dirs()
    _clean_etc()


if __name__ == "__main__":
    if "umount" in sys.argv:
        umount_vkfs()
    else:
        clean()
