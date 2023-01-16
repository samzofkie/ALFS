import os
import sys
import re

def build_if_file_missing(file, build_func):
    if not os.path.exists(file):
        build_func()
    else:
        target_name = build_func.__name__.replace("build_",'')
        target_name = target_name.replace('_', ' ')
        print(target_name + " already built")

def exec_commands_with_failure_and_logging(commands, log_file_path):
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    os.system("touch " + log_file_path)
    commands = [command + " 2>&1 | tee -a " + log_file_path for command in commands]
    for command in commands:
        os.system("echo 'executing: {}' | tee -a {}".format(command, log_file_path))
        ret = os.system(command)
        if ret != 0:
            os.system("echo '{} returned {}'".format(command, ret))
            sys.exit(1)

def try_make_build_dir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        os.system("rm -rf " + path)
        os.mkdir(path)
    os.chdir(path)

def find_source_dir(package):
    lfs_src_path = os.environ["LFS"] + "/srcs/"
    os.chdir(lfs_src_path)
    packages = os.listdir()
    res = [p for p in packages if package in p]
    res = [p for p in res if ".patch" not in p]
    if len(res) > 1:
        print("ambiguous package name passed to find_source_dir: " + \
                package)
        sys.exit(1)
    elif len(res) == 0:
        print("package name passed to find_source_dir ({}) turned up no results".format(package))
        sys.exit(1)
    return lfs_src_path + res[0]

def lfs_dir_snapshot():
    os.chdir(os.environ["LFS"])
    snapshot = os.popen("find -path './srcs' -prune -o -print").read().split('\n')
    return set(snapshot)

def read_in_bash_script(script_path):
    with open(script_path) as f:
        commands = [re.sub(r'\s*$', '', line) for line in f.readlines()]
    commands = [c for c in commands if c != '']
    i=0
    while i<len(commands):
        # If a line in a bash script ends in a '\',
        # the next line should be tagged on to the current line
        # and the '\' removed.
        if commands[i][-1] == '\\':
            commands[i] = commands[i][:-1] + commands[i+1]
            del commands[i+1]
        else:
            i+=1
    return commands

