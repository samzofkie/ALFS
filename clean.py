#!/usr/bin/env python3
import subprocess, os, shutil


def _remove_dirs():
    package_names = [tarball.split(".tar")[0] for tarball in
        os.listdir("sources") if ".tar" in tarball]
    sys_dirs = ["boot", "dev", "home", "lib64", "media", "mnt", "opt", "proc",
              "root", "run", "srv", "sys", "tmp", "tools", "usr", "var"]
    for d in package_names + sys_dirs:
        if os.path.exists(d):
            shutil.rmtree(d)


def _clean_etc():
    """ Run outside chroot please!"""
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
        subprocess.run(f"umount {d}".split())


def clean():
    _umount_vkfs()
    _remove_dirs()
    _clean_etc()


if __name__ == "__main__":
    clean()

