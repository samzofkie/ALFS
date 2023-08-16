#!/usr/bin/env python3
import subprocess, os, shutil, sys
import utils


def remove_source_dirs():
    for d in [
        tarball.split(".tar")[0]
        for tarball in os.listdir("sources")
        if ".tar" in tarball
    ]:
        utils.ensure_removal(d)


def _remove_sys_dirs():
    for d in [
        "bin",
        "boot",
        "dev",
        "home",
        "lib",
        "lib64",
        "media",
        "mnt",
        "opt",
        "package-records",
        "proc",
        "root",
        "run",
        "sbin",
        "srv",
        "sys",
        "tmp",
        "tools",
        "usr",
        "var",
    ]:
        utils.ensure_removal(d)


def _clean_etc():
    """Run outside chroot please!"""
    contents = os.listdir("etc")
    for item in contents:
        if item not in [
            "group",
            "hosts",
            "inittab" "passwd",
            "profile",
            "shells",
            "nsswitch.conf",
            "syslog.conf",
        ]:
            utils.ensure_removal(f"etc/{item}")


def _umount_vkfs():
    """Run outside the chroot please!"""
    for d in os.listdir("dev"):
        subprocess.run(f"umount dev/{d}".split())
    for d in ["dev", "proc", "sys", "run"]:
        subprocess.run(f"umount {d}".split())


def clean():
    # _umount_vkfs()
    remove_source_dirs()
    _remove_sys_dirs()
    _clean_etc()


if __name__ == "__main__":
    clean()
