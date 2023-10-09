#!/usr/bin/env -S -i python3

# TODO:
# README
# remove dockerfile dependencies
# consolidate dir touching to ensure_directory_skeleton
# try running over an already fully built system
# check git for which etc files to keep / remove
# live usb
# networkin'

import os
import subprocess
import shutil
import stat
import signal
from urllib.request import urlopen

import utils
from file_tracker import FileTracker
from clean import remove_source_trees
import temporary_environment
import core


def ensure_directory_skeleton():
    for d in FileTracker.tracked_trees + ["dev", "proc", "sys", "run"]:
        utils.ensure_dir(d)
    for d in ["bin", "lib", "sbin"]:
        utils.ensure_dir(f"usr/{d}")
        utils.ensure_symlink(f"usr/{d}", f"{os.getcwd()}/{d}")
    utils.ensure_dir("sources")


def ensure_sources_downloaded():
    urls = set()
    for package in (
        temporary_environment.cross_toolchain
        + temporary_environment.temporary_tools
        + temporary_environment.chroot_temporary_tools
        + core.packages
    ):
        urls.add(package.tarball_url)
        if hasattr(package, "patch_url"):
            urls.add(package.patch_url)
        if hasattr(package, "extra_urls"):
            for extra in package.extra_urls:
                urls.add(extra)
    for url in urls:
        filename = url.split("/")[-1]
        if not os.path.exists(f"sources/{filename}"):
            print(f"downloading {filename}...")
            with open(f"sources/{filename}", "wb") as f:
                f.write(urlopen(url).read())


def mount_vkfs():
    for d in ["dev", "dev/pts"]:
        subprocess.run(f"mount -v --bind /{d} {os.getcwd()}/{d}".split())
    for fs_type, d in [("proc", "proc"), ("sysfs", "sys"), ("tmpfs", "run")]:
        subprocess.run(f"mount -vt {fs_type} {fs_type} " f"{os.getcwd()}/{d}".split())


def unmount_vkfs():
    for d in ["dev/pts", "dev", "proc", "sys", "run"]:
        subprocess.run(f"umount -f {d}".split())


def ensure_directory_skeleton_two():
    chroot_dirs = [
        "home/tester",
        "mnt",
        "opt",
        "srv",
        "root",
        "tmp",
        "usr/lib/firmware",
    ]
    chroot_dirs += ["etc/" + d for d in ["opt", "sysconfig"]]
    # chroot_dirs += ["media/" + d for d in ["floppy", "cdrom"]]
    chroot_dirs += ["usr/local/" + d for d in ["bin", "lib", "sbin"]]
    for prefix in ["usr/", "usr/local/"]:
        chroot_dirs += [prefix + d for d in ["include", "src"]]
        chroot_dirs += [
            prefix + "share/" + d
            for d in [
                "color",
                "dict",
                "doc",
                "info",
                "locale",
                "man",
                "misc",
                "terminfo",
                "zoneinfo",
            ]
        ]
        chroot_dirs += [prefix + "share/man/man" + str(i) for i in range(9)]
    chroot_dirs += [
        "var/" + d for d in ["cache", "local", "log", "mail", "opt", "spool", "tmp"]
    ]
    chroot_dirs += ["var/lib/" + d for d in ["color", "misc", "locate", "hwclock"]]

    for d in chroot_dirs:
        utils.ensure_dir(d)

    utils.ensure_symlink("/run", "/var/run")
    utils.ensure_symlink("/run/lock", "/var/lock")
    # No way to set sticky bit with os.chmod
    subprocess.run("chmod 1777 /tmp /var/tmp".split(), check=True)
    shutil.chown("/home/tester", user="tester")
    for file in ["btmp", "lastlog", "faillog", "wtmp"]:
        utils.ensure_touch(f"/var/log/{file}")
    shutil.chown("/var/log/lastlog", group="utmp")
    os.chmod(
        "/var/log/lastlog",
        stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
    )
    os.chmod("/var/log/btmp", stat.S_IRUSR | stat.S_IWUSR)


def remove_excess_temporary_tools():
    for d in ["info", "man", "doc"]:
        shutil.rmtree(f"/usr/share/{d}")
        os.mkdir(f"/usr/share/{d}")
    for lib_dir in ["lib", "libexec"]:
        for full_path, _, files in os.walk(f"/usr/{lib_dir}"):
            for file in files:
                if file[-3:] == ".la":
                    utils.ensure_removal(f"{full_path}/{file}")
    utils.ensure_removal("/tools")


if __name__ == "__main__":
    os.environ["PATH"] = f"{os.getcwd()}/tools/bin:/usr/bin"
    ensure_directory_skeleton()
    remove_source_trees()
    ensure_sources_downloaded()

    ft = FileTracker(f"{os.getcwd()}/")

    def build(packages):
        for package in packages:
            package(ft).build()

    ft.tracked_trees.append("tools")
    build(temporary_environment.cross_toolchain + temporary_environment.temporary_tools)

    mount_vkfs()

    parent_pid = os.getpid()
    if os.fork() != 0:
        def signal_handler(signum, frame):
            pass
        signal.signal(signal.SIGCHLD, signal_handler)
        signum = signal.sigwait([signal.SIGCHLD])
        unmount_vkfs()
        exit()

    try:
        os.chroot(".")
        os.environ["PATH"] = "/usr/bin:/usr/sbin"
        ensure_directory_skeleton_two()
        ft.root_dir = "/"
        build(temporary_environment.chroot_temporary_tools)
        remove_excess_temporary_tools()
        ft.tracked_trees.remove("tools")
        build(core.packages)
    finally:
        os.kill(parent_pid, signal.SIGCHLD)
