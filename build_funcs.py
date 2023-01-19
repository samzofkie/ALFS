import os
from utils import (
    try_make_build_dir, 
    find_source_dir, 
    read_in_bash_script,
    exec_commands_with_failure_and_logging,
    vanilla_build,
    get_version_num)


build_cross_binutils = vanilla_build("cross_binutils", "build")    

def build_cross_gcc():
    src_dir_path = find_source_dir("gcc")
    os.chdir(src_dir_path)
    log_file = os.environ["LFS"] + "/build-logs/cross_gcc"
    exec_commands_with_failure_and_logging(["./contrib/download_prerequisites",
                "sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64"],
                                           log_file)
    build_dir = os.environ["LFS"] + "/srcs/gcc-build"
    try_make_build_dir(build_dir)
    os.chdir(build_dir)
    commands = read_in_bash_script(os.environ["HOME"] + "/build-scripts/cross-gcc.sh")
    # Biggest reason this can't be vanilla build- I'd rather not have it be dependent
    # on version number.
    commands[0] = src_dir_path + '/' +commands[0]
    exec_commands_with_failure_and_logging(commands, log_file)
    os.chdir(src_dir_path)
    os.system("cat gcc/limitx.h gcc/glimits.h gcc/limity.h > \
        `dirname $($LFS_TGT-gcc -print-libgcc-file-name)`/install-tools/include/limits.h")
    os.system("rm -rf {}/srcs/gcc-build".format(os.environ["LFS"]))

def build_linux_api_headers():
    src_dir_path = find_source_dir("linux")
    os.chdir(src_dir_path)
    exec_commands_with_failure_and_logging(["make mrproper", "make headers",
            "find usr/include -type f ! -name '*.h' -delete",
            "cp -rv usr/include {}/usr".format(os.environ["LFS"])], 
                                           os.environ["LFS"] + "/build-logs/linux_api_headers")

def build_cross_glibc():
    src_dir = find_source_dir("glibc")
    glibc_version_n = get_version_num("glibc")
    os.chdir(src_dir)
    os.system("patch -Np1 -i ../glibc-{}-fhs-1.patch".format(glibc_version_n))
    vanilla_build("cross_glibc", "build")()
    gcc_version_n = get_version_num("gcc")
    os.system(os.environ["LFS"] + \
        "/tools/libexec/gcc/{}/{}/install-tools/mkheaders".format(os.environ["LFS_TGT"], gcc_version_n))

# Only reason this isn't fully vanilla build is source dir is gcc but target should be
# called cross_libstdcpp for logging
def build_cross_libstdcpp():
    src_dir = find_source_dir("gcc")
    build_dir = src_dir_path + '/build'
    try_make_build_dir(build_dir)
    os.chdir(build_dir)
    build_script_path = os.environ["HOME"] + "/build-scripts/cross_libstdcpp.sh"
    commands = read_in_bash_script(build_script_path)
    log_file_path = os.environ["LFS"] + "/build-logs/cross_libstdcpp"
    exec_commands_with_failure_and_logging(commands, log_file_path)

