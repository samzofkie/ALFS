import os
import sys

def build_if_file_missing(file, build_func, build_target_name):
    if not os.path.exists(file):
        build_func()
    else:
        print(build_target_name + " already built")

def exec_commands_with_failure(commands):
    for command in commands:
        ret = os.system(command)
        if ret != 0:
            print(command + " returned " + str(ret))
            sys.exit(1)

def exec_commands_with_failure_and_logging(commands, log_file_path):
    if not os.path.exists(log_file_path):
        os.system("touch " + log_file_path)
    commands = [command + " 2>&1 | tee -a " + log_file_path for command in commands]
    exec_commands_with_failure(commands)

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

