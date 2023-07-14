import os
from setup import ROOT_DIR


def mount_vkfs(): 
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


def enter_chroot():
    os.chdir(ROOT_DIR)
    os.chroot(ROOT_DIR)
    for var in os.environ:
        del os.environ[var]
    os.environ["PATH"] = "/usr/bin:/usr/sbin" 


def mount_and_enter_chroot():
    mount_vkfs()
    enter_chroot()
