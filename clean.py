#!/usr/bin/env python3
import subprocess, os, shutil
from setup import ROOT_DIR


def _remove_dirs():
    for d in ["boot", "dev", "home", "lib64", "media", "mnt", "opt", "proc",
              "root", "run", "srv", "sys", "tmp", "tools", "usr", "var"]:
        if os.path.exists(d):
            shutil.rmtree(d)


def _clean_etc():
    """ Run outside chroot please!"""
    os.chdir(ROOT_DIR)
    contents = os.listdir("etc")
    for item in contents:
        if item not in ["group", "hosts", "passwd"]:
            item = "etc/" + item
            if os.path.isfile(item):
                os.remove(item)
            else:
                shutil.rmtree(item)


def _umount_vkfs():
    """ Run outside the chroot please!"""
    for d in ["dev/pts", "dev", "proc", "sys", "run"]:
        subprocess.run(f"umount {ROOT_DIR}/{d}".split())


def clean():
    _umount_vkfs()
    _remove_dirs()
    _clean_etc()

