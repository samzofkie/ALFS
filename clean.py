#!/usr/bin/env python3
import subprocess, os, shutil, sys


def _remove_dirs():
    package_names = [
        tarball.split(".tar")[0]
        for tarball in os.listdir("sources")
        if ".tar" in tarball
    ]
    sys_dirs = [
        "bin" "boot",
        "dev",
        "home",
        "lib" "lib64",
        "media",
        "mnt",
        "opt",
        "package-records",
        "proc",
        "root",
        "run",
        "sbin" "srv",
        "sys",
        "tmp",
        "tools",
        "usr",
        "var",
    ]
    for d in package_names + sys_dirs:
        utils.ensure_removal(d)


def _clean_etc():
    """Run outside chroot please!"""
    contents = os.listdir("etc")
    for item in contents:
        if item not in ["group", "hosts", "passwd", "nsswitch.conf"]:
            utils.ensure_removal(f"etc/{item}")


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
