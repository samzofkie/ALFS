#!/usr/bin/env python3

import os, subprocess, shutil, time, stat
from urllib.request import urlopen
from cross_toolchain import CrossToolchainBuild
from temp_tools import TempToolsBuild
from chroot_temp_tools import ChrootTempToolsBuild
from main_build import MainBuild

SYS_DIRS = ["var", "usr", "etc", "lib64", "tools"]


def _ensure_wget_list():
    if os.path.exists("wget-list"):
        return
    
    res = urlopen("https://www.linuxfromscratch.org/lfs/downloads/stable/wget-list")
    urls = res.read().decode().split("\n")
    urls = [url for url in urls if "tcl8.6.13-html" not in url]
    with open("wget-list", "w") as f:
        f.writelines("\n".join(urls))


def _ensure_directory_skeleton():
    for d in SYS_DIRS:
        if not os.path.exists(d):
            os.makedirs(d)
    extras = ["sources", "package-records", "usr/bin", "usr/lib", "usr/sbin"]
    for extra in extras:
        if not os.path.exists(extra):
            os.mkdir(extra)
    for d in ["bin", "lib", "sbin"]:
        if not os.path.exists(f"usr/{d}"):
            os.mkdir(f"usr/{d}")
        if not os.path.exists(d):
            os.symlink(f"usr/{d}", f"{os.getcwd()}/{d}")


def _ensure_tarballs_downloaded():
    with open("wget-list", "r") as f:
        tarball_urls = [line.split("\n")[0] for line in f.readlines()]

    for url in tarball_urls:
        tarball_name = url.split("/")[-1]
        if not os.path.exists("sources/" + tarball_name):
            print("downloading " + tarball_name + "...")
            res = urlopen(url)
            with open("sources/" + tarball_name, "wb") as f:
                f.write(res.read())
    
    if os.path.exists("sources/tcl8.6.13-src.tar.gz"):
        os.rename("sources/tcl8.6.13-src.tar.gz", "sources/tcl8.6.13.tar.gz")


def setup():
    _ensure_wget_list()
    _ensure_directory_skeleton()
    _ensure_tarballs_downloaded()


class FileTracker:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.recorded_files = self._system_snapshot()

    def _system_snapshot(self):
        os.chdir(self.root_dir)
        all_files = set()
        for d in SYS_DIRS:
            for curr_dir, _, files in os.walk(d):
                for file in files:
                    full_path = f"{curr_dir}/{file}"
                    if os.path.isfile(full_path):
                        all_files.add(full_path)
        return all_files

    def _update_recorded_files(self):
        self.recorded_files = self._system_snapshot()

    def _write_file_list(self, target_name, file_list):
        with open(f"{self.root_dir}/package-records/{target_name}", "w") as f:
            f.writelines(sorted([f"{file}\n" for file in file_list]))

    def record_new_files_since(self, start_time, target_name):
        self._update_recorded_files()
        new_files = set()
        for file in self.recorded_files:
            file_time = os.stat(file).st_mtime
            if file_time > start_time:
                new_files.add(file)
        self._write_file_list(target_name, new_files)

    def query_record_existence(self, target_name):
        return os.path.exists(f"{self.root_dir}/package-records/{target_name}")


def _mount_vkfs(root_dir):
    """Mount Virtual Kernel Filesystems"""
    for d in ["dev", "proc", "sys", "run"]:
        if not os.path.exists(f"{root_dir}/{d}"):
            os.mkdir(f"{root_dir}/{d}")
    for command in [
        f"mount -v --bind /dev {root_dir}/dev",
        f"mount -v --bind /dev/pts {root_dir}/dev/pts",
        f"mount -vt proc proc {root_dir}/proc",
        f"mount -vt sysfs sysfs {root_dir}/sys",
        f"mount -vt tmpfs tmpfs {root_dir}/run",
    ]:
        ret = subprocess.run(command.split())


def _enter_chroot(root_dir):
    os.chdir(root_dir)
    os.chroot(root_dir)
    for var in os.environ:
        del os.environ[var]
    os.environ["PATH"] = "/usr/bin:/usr/sbin"


def _make_additional_dirs():
    chroot_dirs = [
        "boot",
        "home/tester",
        "mnt",
        "opt",
        "srv",
        "root",
        "tmp",
        "usr/lib/firmware",
    ]
    chroot_dirs += ["etc/" + d for d in ["opt", "sysconfig"]]
    chroot_dirs += ["media/" + d for d in ["floppy", "cdrom"]]
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
        if not os.path.exists(d):
            os.makedirs(d)

    if not os.path.islink("/var/run"):
        os.symlink("/run", "/var/run")
    if not os.path.islink("/var/lock"):
        os.symlink("/run/lock", "/var/lock")
    subprocess.run("chmod 1777 /tmp /var/tmp".split(), check=True)
    shutil.chown("/home/tester", user="tester")
    for file in ["btmp", "lastlog", "faillog", "wtmp"]:
        with open("/var/log/" + file, "a") as f:
            pass
    shutil.chown("/var/log/lastlog", group="utmp")
    os.chmod(
        "/var/log/lastlog",
        stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
    )
    os.chmod("/var/log/btmp", stat.S_IRUSR | stat.S_IWUSR)


def prepare_and_enter_chroot(root_dir):
    _mount_vkfs(root_dir)
    _enter_chroot(root_dir)
    _make_additional_dirs()


def clean_temp_system():
    for d in ["info", "man", "doc"]:
        shutil.rmtree(f"/usr/share/{d}")
        os.mkdir(f"/usr/share/{d}")
    for lib_dir in ["lib", "libexec"]:
        for full_path, _, files in os.walk(f"/usr/{lib_dir}"):
            for file in files:
                if file[-3:] == ".la":
                    os.remove(f"{full_path}/{file}")
    shutil.rmtree("/tools")


if __name__ == "__main__":
    setup()
    base_dir = os.getcwd()
    ft = FileTracker(base_dir)
    CrossToolchainBuild(base_dir, ft).build_phase()
    TempToolsBuild(base_dir, ft).build_phase()
    prepare_and_enter_chroot(base_dir)
    base_dir = "/"
    ft.root_dir = "/"
    ChrootTempToolsBuild(base_dir, ft).build_phase()
    clean_temp_system()
    MainBuild(base_dir, ft).build_phase()
