import os
import sys
import re
import subprocess

def red_print(s):
    print("\33[31m" + s + "\33[0m")

def clean_target_name(target_name):
    for prefix in ["temp_", "cross_", "chroot_"]:
        if prefix in target_name:
            target_name = target_name.replace(prefix, '')
    return target_name

def find_tarball(target_name):
    target_name = clean_target_name(target_name)
    os.chdir(os.environ["LFS"] + "srcs/")
    res = [p for p in os.listdir() if target_name == p[:len(target_name)] 
                                      and ".patch" not in p] 
    if "tcl" in target_name:
        res.remove("tcl8.6.12-html.tar.gz")

    if len(res) == 1:
        return os.environ["LFS"] + "srcs/" + res[0]
    elif len(res) > 1:
        red_print("ambiguous target name passed to find_source_dir: cleaned target name is " + \
                target_name)
    elif len(res) == 0:
        red_print("cleaned target name ({}) in find_source_dir turned up no results".format(target_name))
    sys.exit(1)

def lfs_dir_snapshot():
    os.chdir(os.environ["LFS"])
    directories = ["etc", "lib64", "root", "run", "cross-tools", "temp-tools", "usr", "var"]
    directories = [os.environ["LFS"] + i for i in directories]
    res = subprocess.run(f"find {' '.join(directories)} -type f", 
                              shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    return set(str(res.stdout).split('\\n'))

def vanilla_build(target_name, src_dir_name=None):
    def f():
        nonlocal src_dir_name
        if src_dir_name == None:
            src_dir_name = target_name

        tarball_path = find_tarball(src_dir_name)
        src_dir_path = tarball_path.split(".tar")[0]

        if "tcl" in src_dir_path:
            src_dir_path = src_dir_path.rsplit("-",1)[0]

        build_script_path = os.environ["LFS"] + \
                "root/build-scripts/{}.sh".format(target_name.replace('_','-'))
        log_file_path = os.environ["LFS"] + "logs/" + target_name 
        tracked_file_record_path = os.environ["LFS"] + \
                "logs/tracked/" + target_name
        
        snap1 = lfs_dir_snapshot()
    
        os.chdir(os.environ["LFS"] + "srcs/") 
        subprocess.run(["tar", "-xf", tarball_path], check=True)
        os.chdir(src_dir_path) 
      
        proc = subprocess.run([f"{build_script_path} >{log_file_path} 2>&1"],
                              shell=True)
        
        os.chdir(os.environ["LFS"] + "srcs/")
        os.system("rm -rf " + src_dir_path)

        if proc.returncode != 0:
            red_print(build_script_path + " failed!")
            return
         
        with open(tracked_file_record_path, 'w') as f:
            new_files = lfs_dir_snapshot() - snap1 
            f.writelines('\n'.join(new_files))
    
    f.__name__ = "build_" + target_name
    return f
