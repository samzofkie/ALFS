# TODO
# force symlink
# run? os.environ manglin'
#   quiet run
# touch
# ensure removal
# sed

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
