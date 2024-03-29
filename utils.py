import os
import shutil
import subprocess


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
    if os.path.isdir(link_name):
        link_name += f"/{pointed_at.split('/')[-1]}"
    if not os.path.islink(link_name):
        os.symlink(pointed_at, link_name)


def ensure_touch(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            pass


def ensure_removal(path):
    if os.path.exists(path) or os.path.islink(path):
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def modify(filename, function):
    lines = read_file(filename)
    for i in range(len(lines)):
        lines[i] = function(lines[i], i)
    write_file(filename, lines)


def chown_tree(root, user_name):
    for root, _, files in os.walk(root):
        shutil.chown(root, user=user_name)
        for file in files:
            shutil.chown(f"{root}/{file}", user=user_name)


def run(command):
    subprocess.run(command.split(), check=True)


def run_commands(commands):
    for command in commands:
        run(command)


def run_as_tester(command, check=True):
    tester_line = [
        line for line in read_file("/etc/passwd") if "tester" in line
    ][0]
    tester_uid, tester_gid = tester_line.split(":")[2:4]
    subprocess.run(command.split(), user=int(tester_uid), group=int(tester_gid),
                   check=check)

