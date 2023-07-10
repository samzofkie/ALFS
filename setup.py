import os
from urllib.request import urlopen


LFS_TGT = "x86_64-lfs-linux-gnu"
HOST_TRIPLET = "x86_64-pc-linux-gnu"
SYS_DIRS = ["etc", "var", "usr/bin", "usr/lib", "usr/sbin", 
                "lib64", "tools"]
ROOT_DIR = os.getcwd()
ENV_VARS = { 
            "LC_ALL": "POSIX", 
            "PATH": f"{ROOT_DIR}/tools/bin:/usr/bin",
            "CONFIG_SITE": f"{ROOT_DIR}/usr/share/config.site" 
           }


def _ensure_wget_list():
    os.chdir(ROOT_DIR)
    if not os.path.exists("wget-list"):
        res = urlopen("https://www.linuxfromscratch.org/lfs/downloads/stable/wget-list")
        with open("wget-list", "w") as f:
            f.writelines(res.read().decode())


def _ensure_directory_skeleton():
    os.chdir(ROOT_DIR)
    for dir in SYS_DIRS:
        if not os.path.exists(dir):
            os.makedirs(dir)
    extras = ["sources", "package-records"]
    for extra in extras:
        if not os.path.exists(extra):
            os.mkdir(extra)


def _ensure_tarballs_downloaded():
    os.chdir(ROOT_DIR)
    with open("wget-list", "r") as f:
        tarball_urls = [line.split("\n")[0] for line in f.readlines()]

    for url in tarball_urls:
        tarball_name = url.split("/")[-1]
        if not os.path.exists("sources/" + tarball_name): 
            print("downloading " + tarball_name + "...")
            res = urlopen(url)
            with open("sources/" + tarball_name, "wb") as f:
                f.write(res.read())


def _system_snapshot():
    os.chdir(ROOT_DIR)
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

_ensure_wget_list()
_ensure_directory_skeleton()
_ensure_tarballs_downloaded()

RECORDED_FILES = _system_snapshot() 

def record_new_files(filename):
    os.chdir(ROOT_DIR)
    global RECORDED_FILES
    new_files = _system_snapshot() - RECORDED_FILES
    with open("package-records/" + filename, "w") as f:
        f.writelines(sorted([file + "\n" for file in new_files]))
    RECORDED_FILES = RECORDED_FILES.union(new_files)



