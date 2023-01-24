import os
import sys
import re
import subprocess

def red_print(s):
    print("\33[31m" + s + "\33[0m")

def try_make_build_dir(path):
    if os.path.exists(path):
        os.system("rm -rf " + path)
    os.mkdir(path)

def clean_target_name(target_name):
    for prefix in ["temp_", "cross_"]:
        if prefix in target_name:
            target_name = target_name.replace(prefix, '')
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

def lfs_dir_snapshot():
    os.chdir(os.environ["LFS"])
    snapshot = os.popen("find $LFS -type f").read().split('\n')
    return set(snapshot)

def vanilla_build(target_name, src_dir_name=None):
    def f():
        nonlocal src_dir_name
        if src_dir_name == None:
            src_dir_name = target_name
        src_dir_path = find_source_dir(src_dir_name)
        build_script_path = os.environ["HOME"] + \
                "/build-scripts/{}.sh".format(target_name.replace('_','-'))
        log_file_path = os.environ["LFS"] + "/build-logs/" + target_name
        tracked_file_record_path = os.environ["LFS"] + \
                "/build-logs/tracked-files/" + target_name
        snap1 = lfs_dir_snapshot()

        os.chdir(src_dir_path) 
        print("building " + target_name.replace('_',' '))
        with subprocess.Popen(build_script_path, shell=True,
                              stdout=subprocess.PIPE, text=True, 
                              stderr=subprocess.STDOUT) as p:
            output = p.stdout.read()
            p.wait()
            ret = p.returncode
        
        with open(log_file_path, 'a') as f:
            f.writelines(output)

        if ret != 0:
            red_print(build_script_path + " failed")
            #sys.exit(1)
            return

        new_files = lfs_dir_snapshot() - snap1
        with open(tracked_file_record_path, 'w') as f:
            f.writelines('\n'.join(new_files))
    
    f.__name__ = "build_" + target_name
    return f

def get_version_num(target_name):
    src_dir = find_source_dir(target_name).split('/')[-1]
    return src_dir.split('-')[-1]

def build_w_snapshots(build_func):
    snap1 = lfs_dir_snapshot()
    build_func()
    snap2 = lfs_dir_snapshot()
    snap_f_path = os.environ["LFS"] + "/" + build_func.__name__ + "_new_files"
    with open(snap_f_path, 'w') as f:
        f.write('\n'.join(snap2 - snap1))

