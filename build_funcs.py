import os
from utils import (
    try_make_build_dir, 
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

# Only reason this isn't fully vanilla build is source dir is gcc but target should be
# called cross_libstdcpp for logging
"""def build_cross_libstdcpp():
    src_dir = find_source_dir("gcc")
    build_dir = src_dir_path + '/build'
    try_make_build_dir(build_dir)
    os.chdir(build_dir)
    build_script_path = os.environ["HOME"] + "/build-scripts/cross_libstdcpp.sh"
    commands = read_in_bash_script(build_script_path)
    log_file_path = os.environ["LFS"] + "/build-logs/cross_libstdcpp"
    exec_commands_with_failure_and_logging(commands, log_file_path)"""

