# TODO
# sed
# run? os.environ manglin'
#   quiet run

import os, shutil


def read_file(filename):
    with open(filename, "r") as f:
        return f.readlines()


def write_file(filename, lines):
    with open(filename, "w") as f:
        f.writelines(lines)


def ensure_dir(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


def ensure_symlink(pointed_at, link_name):
    if not os.path.exists(link_name):
        os.symlink(pointed_at, link_name)


def ensure_touch(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            pass


def ensure_removal(path):
    if os.path.exists(path) or os.path.islink(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
