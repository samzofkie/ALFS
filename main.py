#!/usr/bin/env python3

import os
from urllib.request import urlopen
import subprocess
import shutil

def ensure_wget_list():
    if not os.path.exists("wget-list"):
        res = urlopen("https://www.linuxfromscratch.org/lfs/downloads/stable/wget-list")
        with open("wget-list", "w") as f:
            f.writelines(res.read().decode())

def ensure_directory_skeleton():
    for dir in SYSTEM_DIRS:
        if not os.path.exists(dir):
            os.makedirs(dir)
    if not os.path.exists("sources"):
        os.mkdir("sources")

def ensure_tarballs_downloaded():
    with open("wget-list", "r") as f:
        tarball_urls = [line.split("\n")[0] for line in f.readlines()]

    for url in tarball_urls:
        tarball_name = url.split("/")[-1]
        if not os.path.exists("sources/" + tarball_name): 
            print("downloading " + tarball_name + "...")
            res = urlopen(url)
            with open("sources/" + tarball_name, "wb") as f:
                f.write(res.read())

class TarballNotFoundError(Exception):
    pass

def get_tarball_name(package_name):
    tarballs = os.listdir("sources")
    res = [tarball for tarball in tarballs if package_name in tarball]
    res = [tarball for tarball in res if ".patch" not in tarball]
    if len(res) < 1:
        raise TarballNotFoundError("No results from search term \"" +
                                   package_name + "\"")
    elif len(res) > 1:
        raise TarballNotFoundError("Too many results from search term \"" +
                                   package_name + "\": " + str(res))
    return res[0]

def system_snapshot():
    dirs = SYSTEM_DIRS.copy()
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

def build_cross_binutils():
    # check if package has been built yet

    # unpack tar and enter source dir
    tarball_name = get_tarball_name("binutils")
    package_dir_name = tarball_name.split(".tar")[0] 
    if not os.path.exists(package_dir_name):
        subprocess.run(("tar -xvf sources/" + tarball_name).split(" "))
    os.chdir(package_dir_name)
    
    # make and enter build dir
    if not os.path.exists("build"):
        os.mkdir("build")
    os.chdir("build")

    # run build commands
    build_commands = [ f"../configure --prefix={ROOT_DIR}/tools " \
                       f"--with-sysroot={ROOT_DIR} " \
                       f"--target={LFS_TGT} " \
                       "--disable-nls " \
                       "--enable-gprofng=no " \
                       "--disable-werror",
                       "make", "make install" ]
    for command in build_commands:
        completed = subprocess.run(command.split(" "))
        if completed.returncode != 0:
            print(command + " returned " + completed.returncode)

    # return to root and delete source dir
    os.chdir(ROOT_DIR)
    shutil.rmtree(package_dir_name)

    # ensure that important files have been placed into fs

LFS_TGT = "x86_64-lfs-linux-gnu"
SYSTEM_DIRS = ["etc", "var", "usr/bin", "usr/lib", "usr/sbin", "lib64", 
               "tools"]
ROOT_DIR = os.getcwd()

ensure_wget_list()
ensure_directory_skeleton()
ensure_tarballs_downloaded()
build_cross_binutils()
