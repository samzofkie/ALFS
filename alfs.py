#!/usr/bin/env python3

import os
from urllib.request import urlopen
from cross_toolchain import CrossToolchainBuild

SYS_DIRS = ["var", "usr/bin", "usr/lib", "usr/sbin", 
            "etc", "lib64", "tools"]

def _ensure_wget_list():
    if not os.path.exists("wget-list"):
        res = urlopen("https://www.linuxfromscratch.org/lfs/downloads/stable/wget-list")
        with open("wget-list", "w") as f:
            f.writelines(res.read().decode())


def _ensure_directory_skeleton():
    for dir in SYS_DIRS:
        if not os.path.exists(dir):
            os.makedirs(dir)
    extras = ["sources", "package-records"]
    for extra in extras:
        if not os.path.exists(extra):
            os.mkdir(extra)


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
        dirs = SYS_DIRS.copy() 
        all_files = set()
        while dirs:
            curr = dirs.pop()
            for file in os.listdir(curr):
                full_path = curr + "/" + file
                if os.path.isdir(full_path):
                    dirs.append(full_path)
                else:
                    all_files.add(full_path)
        return all_files


    def record_new_files(self, target_name):
        os.chdir(self.root_dir)
        new_files = self._system_snapshot() - self.recorded_files
        with open("package-records/" + target_name, "w") as f:
            f.writelines(sorted([file + "\n" for file in new_files]))
        self.recorded_files = self.recorded_files.union(new_files)


if __name__ == "__main__":
    setup()
    base_dir = os.getcwd()
    ft = FileTracker(base_dir)
    CrossToolchainBuild(base_dir, ft).build_phase()
    # TempToolsBuild(base_dir, ft)
    # prepare_and_enter_chroot()
    # ft.root_dir = "/"

"""from cross_toolchain import build_cross_toolchain
from temp_tools import build_temp_tools
from chroot import prepare_and_enter_chroot, build_chroot_temp_tools

if __name__ == '__main__':
    #build_cross_toolchain()
    build_temp_tools()
    #prepare_and_enter_chroot()
    #build_chroot_temp_tools()

# TODO
# * tracked file checking / remove package function"""
