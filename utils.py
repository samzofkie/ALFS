import os
import sys
import re


def try_make_build_dir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        os.system("rm -rf " + path)
        os.mkdir(path)
    os.chdir(path)

#---------- vanilla build ----------

def clean_target_name(target_name):
    for prefix in ["temp_", "cross_"]:
        if prefix in target_name:
            target_name.replace(prefix, '')
    return target_name

def find_source_dir(target_name):
    target_name = clean_target_name(target_name)
    lfs_src_path = os.environ["LFS"] + "/srcs/"
    os.chdir(lfs_src_path)
    res = [p for p in os.listdir() if target_name in p]
    res = [p for p in res if ".patch" not in p]
    if len(res) > 1:
        print("ambiguous target name passed to find_source_dir: cleaned target name is " + \
                target_name)
        sys.exit(1)
    elif len(res) == 0:
        print("cleaned target name ({}) in find_source_dir turned up no results".format(target_name))
        sys.exit(1)
    return lfs_src_path + res[0]

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

def vanilla_build(target_name):
    def f():
        src_dir_path = find_source_dir(target_name)
        os.chdir(src_dir_path)
        build_script_path = \
                os.environ["HOME"] + "/build-scripts/{}.sh".format(target_name.replace('_', '-'))
        commands = read_in_bash_script(build_script_path)
        log_file_path = os.environ["LFS"] + "/build-logs/" + target_name
        exec_commands_with_failure_and_logging(commands, log_file_path)
    f.__name__ = "build_" + target_name
    return f

