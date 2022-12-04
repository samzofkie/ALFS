#!/usr/bin/python3

import os

lfs = "./lfs"

lfs_dir_structure = [ "etc", "var", "usr", "tools",
                      "lib64",
                      "usr/bin", "usr/lib", "usr/sbin" ]

def create_dir_structure():
    try: 
        os.mkdir(lfs)
        os.chdir(lfs)
        for directory in lfs_dir_structure:
            os.mkdir(directory)
    except FileExistsError:
        pass


os.environ["LFS"]="./lfs"
create_dir_structure()
print(os.getcwd())


