import os
import sys

def build_if_file_missing(file, build_func, build_target_name):
    cross_linker_filename = os.environ["LFS"] + "/tools/bin/" + \
            os.environ["LFS_TGT"] + "-ld" 
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

