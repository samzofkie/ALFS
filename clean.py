#!/usr/bin/env python3
import subprocess, os, shutil, sys
import utils


def remove_source_trees():
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
            "fstab",
            "group",
            "hosts",
            "inittab",
            "nsswitch.conf",
            "passwd",
            "profile",
            "shells",
            "syslog.conf",
        ]:
            utils.ensure_removal(f"etc/{item}")


def clean():
    remove_source_trees()
    _remove_sys_dirs()
    _clean_etc()


if __name__ == "__main__":
    clean()
