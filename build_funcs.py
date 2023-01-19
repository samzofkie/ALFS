import os
from utils import (
    find_source_dir, 
    vanilla_build,
    get_version_num)

def build_cross_glibc():
    src_dir = find_source_dir("glibc")
    glibc_version_n = get_version_num("glibc")
    os.chdir(src_dir)
    os.system("patch -Np1 -i ../glibc-{}-fhs-1.patch".format(glibc_version_n))
    vanilla_build("cross_glibc")()
    gcc_version_n = get_version_num("gcc")
    os.system(os.environ["LFS"] + \
        "/tools/libexec/gcc/{}/{}/install-tools/mkheaders".format(os.environ["LFS_TGT"], gcc_version_n))

