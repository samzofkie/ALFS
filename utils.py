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
    directories = ["etc", "lib64", "root", "run", "cross-tools", "usr", "var"]
    directories = [os.environ["LFS"] + d for d in directories]
    completed_proc = subprocess.run(["find"] + directories + ["-type", "f"],
                                    check=True, capture_output=True)
    return set(str(completed_proc.stdout).split('\\n'))

def vanilla_build(target_name, src_dir_name=None):
    def f():
        nonlocal src_dir_name
        if src_dir_name == None:
            src_dir_name = target_name
        tarball_path = find_tarball(src_dir_name)
        src_dir_path = tarball_path.split(".tar")[0]
        if "tcl" in src_dir_path:
            src_dir_path = src_dir_path.rsplit("-",1)[0]
                
        snap1 = lfs_dir_snapshot()
    
        os.chdir(os.environ["LFS"] + "srcs/")
        subprocess.run(["tar", "-xf", tarball_path], check=True, env=os.environ)
        os.chdir(src_dir_path) 
      
        build_script_path = f"{os.environ['LFS']}root/build-scripts/{target_name.replace('_','-')}.sh"
        log_file_path = f"{os.environ['LFS']}logs/{target_name}"

        proc = subprocess.run([f"{build_script_path} >{log_file_path} 2>&1"],
                              shell=True, env=os.environ)
       
        subprocess.run(["rm", "-rf", src_dir_path], check=True)
 
        tracked_file_record_path = f"{os.environ['LFS']}logs/tracked/{target_name}"
        with open(tracked_file_record_path, 'w') as f:
            new_files = lfs_dir_snapshot() - snap1 
            f.writelines('\n'.join(new_files))
   
        if proc.returncode != 0:
            red_print(build_script_path + " failed!")


    f.__name__ = "build_" + target_name
    return f
