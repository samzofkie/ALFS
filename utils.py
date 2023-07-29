# TODO
# touch
# removal
# sed
# run? os.environ manglin'
#   quiet run

import os


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
